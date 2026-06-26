import sys
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.asr.pipeline import RecognitionModePolicy, SpeechPipeline
from voxgo.asr.whisper_engine import TranscriptionResult, WhisperConfig
from voxgo.audio.capture import AudioConfig, SpeechSegment
from voxgo.config.schema import AppConfig, DebugConfig
from voxgo.runtime.events import EventBus, TranscriptReady
from voxgo.runtime.work_items import LatencyTrace, SpeechWorkItem


class FakeRecognizer:
    def __init__(self, text="go", result=None):
        self.calls = 0
        self.audio_lengths = []
        self.text = text
        self.result = result

    def transcribe_audio_bytes_with_language(self, audio_data, sample_rate):
        self.calls += 1
        self.audio_lengths.append(len(audio_data))
        if self.result is not None:
            return self.result
        return TranscriptionResult(self.text, "en", 0.95)


def _segment(**overrides):
    values = {
        "audio_data": b"\x01\x00" * 6400,
        "sample_rate": 16000,
        "duration_seconds": 0.4,
        "voice_duration_seconds": 0.25,
        "block_count": 2,
        "voice_blocks": 1,
        "peak_rms_dbfs": -39.5,
        "energy_threshold_dbfs": -40.0,
        "noise_floor_dbfs": -50.0,
        "reason": "test",
    }
    values.update(overrides)
    return SpeechSegment(**values)


class SpeechPipelineCandidateTest(unittest.TestCase):
    def _pipeline(self, recognizer, config=None, seen=None):
        config = config or AppConfig(
            audio=AudioConfig(
                latency_mode="fast",
                min_segment_seconds=0.45,
                min_segment_peak_margin_db=2.0,
            ),
            whisper=WhisperConfig(language="en"),
            debug=DebugConfig(),
        )
        bus = EventBus()
        seen = seen if seen is not None else []
        bus.subscribe(TranscriptReady, seen.append)
        stats = {"speech_detected": 0, "filtered_speech": 0, "dropped_speech": 0, "errors": 0}
        next_ids = iter(["translation-1", "translation-2"])
        pipeline = SpeechPipeline(
            lambda: config,
            lambda: recognizer,
            bus,
            stats,
            lambda: True,
            lambda: False,
            lambda: next(next_ids),
            {},
            lambda *args: None,
        )
        return pipeline, stats, seen

    def test_language_switch_resets_pending_and_queue(self):
        recognizer = FakeRecognizer("push")
        pipeline, stats, _seen = self._pipeline(recognizer)
        pending = SpeechWorkItem(
            segment=_segment(voice_duration_seconds=0.2),
            trace=LatencyTrace("", 1.0, 1.0),
            candidate_labels=("candidate", "short_segment"),
            short_segment=True,
        )
        queued = SpeechWorkItem(
            segment=_segment(duration_seconds=1.0, voice_duration_seconds=0.9),
            trace=LatencyTrace("", 2.0, 2.0),
            candidate_labels=("candidate",),
        )
        pipeline._pending_buffer.add_or_merge(pending, time.time())
        pipeline._queue.put_nowait(queued)

        pipeline.reset_for_language_switch("zh", "en", 2)

        self.assertFalse(pipeline._pending_buffer.has_pending())
        self.assertTrue(pipeline._queue.empty())
        self.assertEqual(stats["dropped_speech"], 2)

    def test_forced_chinese_low_confidence_result_is_filtered(self):
        recognizer = FakeRecognizer(
            result=TranscriptionResult(
                "就是狗亏警的人 但是剛才你沒有在飛機上面舉行",
                "zh",
                1.0,
                avg_logprob=-0.83,
                no_speech_prob=0.72,
                compression_ratio=1.0,
                segment_count=1,
            )
        )
        config = AppConfig(
            audio=AudioConfig(latency_mode="balanced"),
            whisper=WhisperConfig(language="zh"),
            debug=DebugConfig(),
        )
        pipeline, stats, seen = self._pipeline(recognizer, config=config)
        segment = _segment(
            duration_seconds=3.8,
            voice_duration_seconds=2.6,
            block_count=19,
            voice_blocks=13,
            vad_voice_blocks=13,
            vad_confidence=13 / 19,
            peak_rms_dbfs=-19.0,
            energy_threshold_dbfs=-45.0,
        )

        pipeline._process(
            SpeechWorkItem(
                segment=segment,
                trace=LatencyTrace("", 1.0, 1.0, source_lang="zh", target_lang="en", whisper_language="zh"),
                candidate_labels=("candidate",),
                source_lang="zh",
                target_lang="en",
                whisper_language="zh",
            )
        )

        self.assertEqual(recognizer.calls, 1)
        self.assertEqual(seen, [])
        self.assertEqual(stats["filtered_speech"], 1)

    def test_low_margin_short_segment_is_candidate_not_dropped_on_detect(self):
        recognizer = FakeRecognizer("go")
        pipeline, stats, seen = self._pipeline(recognizer)

        pipeline.on_speech_detected(_segment())

        self.assertEqual(stats["speech_detected"], 1)
        self.assertEqual(stats["filtered_speech"], 0)
        self.assertTrue(pipeline._pending_buffer.has_pending())
        self.assertEqual(recognizer.calls, 0)
        self.assertEqual(seen, [])

    def test_pending_short_segment_reaches_whisper_after_timeout(self):
        recognizer = FakeRecognizer("push")
        pipeline, stats, seen = self._pipeline(recognizer)

        pipeline.on_speech_detected(_segment())
        pipeline._flush_expired_pending(time.time() + 2.0)
        item = pipeline._queue.get_nowait()
        pipeline._process(item)

        self.assertEqual(recognizer.calls, 1)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].text, "push")
        self.assertEqual(stats["filtered_speech"], 0)

    def test_pending_short_segment_merges_with_following_neighbor(self):
        recognizer = FakeRecognizer("push")
        pipeline, _stats, _seen = self._pipeline(recognizer)

        pipeline.on_speech_detected(_segment(audio_data=b"\x01\x00" * 3200))
        pipeline.on_speech_detected(
            _segment(
                audio_data=b"\x02\x00" * 16000,
                duration_seconds=1.0,
                voice_duration_seconds=0.9,
                block_count=5,
                voice_blocks=4,
                peak_rms_dbfs=-25.0,
            )
        )
        item = pipeline._queue.get_nowait()

        self.assertIn("merged", item.candidate_labels)
        self.assertEqual(len(item.segment.audio_data), 2 * (3200 + 16000))
        self.assertAlmostEqual(item.segment.voice_duration_seconds, 1.15)
        self.assertFalse(pipeline._pending_buffer.has_pending())

    def test_empty_audio_is_still_dropped_immediately(self):
        recognizer = FakeRecognizer("push")
        pipeline, stats, _seen = self._pipeline(recognizer)

        pipeline.on_speech_detected(_segment(audio_data=b"", duration_seconds=0.0, voice_duration_seconds=0.0))

        self.assertEqual(stats["speech_detected"], 1)
        self.assertEqual(stats["filtered_speech"], 1)
        self.assertFalse(pipeline._pending_buffer.has_pending())
        self.assertEqual(recognizer.calls, 0)

    def test_energy_only_short_low_confidence_asr_is_filtered_after_whisper(self):
        recognizer = FakeRecognizer("ok")
        pipeline, stats, seen = self._pipeline(recognizer)
        segment = _segment(
            voice_duration_seconds=0.0,
            vad_voice_blocks=0,
            energy_voice_blocks=2,
            vad_confidence=0.0,
            activity_source="energy",
        )

        pipeline._process(
            SpeechWorkItem(
                segment=segment,
                trace=LatencyTrace("", 1.0, 1.0),
                candidate_labels=("candidate", "low_confidence"),
                low_confidence=True,
            )
        )

        self.assertEqual(recognizer.calls, 1)
        self.assertEqual(seen, [])
        self.assertEqual(stats["filtered_speech"], 1)

    def test_weak_short_candidate_thank_you_is_filtered_after_whisper(self):
        recognizer = FakeRecognizer(
            result=TranscriptionResult(
                "Thank you.",
                "en",
                1.0,
                avg_logprob=-0.05,
                no_speech_prob=0.1,
                compression_ratio=1.1,
                segment_count=1,
            )
        )
        pipeline, stats, seen = self._pipeline(recognizer)
        segment = _segment(
            duration_seconds=1.1,
            voice_duration_seconds=0.15,
            block_count=6,
            voice_blocks=1,
            vad_voice_blocks=1,
            energy_voice_blocks=0,
            vad_confidence=1 / 6,
            activity_source="vad",
            peak_rms_dbfs=-64.8,
            energy_threshold_dbfs=-45.0,
        )

        pipeline._process(
            SpeechWorkItem(
                segment=segment,
                trace=LatencyTrace("", 1.0, 1.0),
                candidate_labels=("candidate", "short_segment", "low_confidence"),
                low_confidence=True,
                short_segment=True,
            )
        )

        self.assertEqual(recognizer.calls, 1)
        self.assertEqual(seen, [])
        self.assertEqual(stats["filtered_speech"], 1)

    def test_weak_short_candidate_real_game_command_is_kept(self):
        recognizer = FakeRecognizer(
            result=TranscriptionResult(
                "push",
                "en",
                0.95,
                avg_logprob=-0.2,
                no_speech_prob=0.2,
                compression_ratio=1.0,
                segment_count=1,
            )
        )
        pipeline, stats, seen = self._pipeline(recognizer)
        segment = _segment(
            duration_seconds=1.1,
            voice_duration_seconds=0.30,
            block_count=6,
            voice_blocks=2,
            vad_voice_blocks=2,
            energy_voice_blocks=0,
            vad_confidence=2 / 6,
            activity_source="vad",
            peak_rms_dbfs=-52.0,
            energy_threshold_dbfs=-45.0,
        )

        pipeline._process(
            SpeechWorkItem(
                segment=segment,
                trace=LatencyTrace("", 1.0, 1.0),
                candidate_labels=("candidate", "short_segment", "low_confidence"),
                low_confidence=True,
                short_segment=True,
            )
        )

        self.assertEqual(recognizer.calls, 1)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].text, "push")
        self.assertEqual(stats["filtered_speech"], 0)

    def test_weak_short_candidate_game_word_is_not_filtered_just_for_being_short(self):
        recognizer = FakeRecognizer(
            result=TranscriptionResult(
                "enemy",
                "en",
                0.95,
                avg_logprob=-0.2,
                no_speech_prob=0.2,
                compression_ratio=1.0,
                segment_count=1,
            )
        )
        pipeline, stats, seen = self._pipeline(recognizer)
        segment = _segment(
            duration_seconds=1.0,
            voice_duration_seconds=0.30,
            block_count=6,
            voice_blocks=2,
            vad_voice_blocks=2,
            energy_voice_blocks=0,
            vad_confidence=2 / 6,
            activity_source="vad",
            peak_rms_dbfs=-52.0,
            energy_threshold_dbfs=-45.0,
        )

        pipeline._process(
            SpeechWorkItem(
                segment=segment,
                trace=LatencyTrace("", 1.0, 1.0),
                candidate_labels=("candidate", "short_segment", "low_confidence"),
                low_confidence=True,
                short_segment=True,
            )
        )

        self.assertEqual(recognizer.calls, 1)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].text, "enemy")
        self.assertEqual(stats["filtered_speech"], 0)

    def test_strong_candidate_is_prioritized_before_queued_weak_candidate(self):
        recognizer = FakeRecognizer("push")
        pipeline, _stats, _seen = self._pipeline(recognizer)
        weak = SpeechWorkItem(
            segment=_segment(voice_duration_seconds=0.15),
            trace=LatencyTrace("", 1.0, 1.0),
            candidate_labels=("candidate", "short_segment", "low_confidence"),
            low_confidence=True,
            short_segment=True,
        )
        strong = SpeechWorkItem(
            segment=_segment(duration_seconds=1.0, voice_duration_seconds=0.9, peak_rms_dbfs=-25.0),
            trace=LatencyTrace("", 2.0, 2.0),
            candidate_labels=("candidate",),
        )

        pipeline._queue.put_nowait(weak)
        pipeline._enqueue_with_backpressure(
            strong,
            RecognitionModePolicy(mode="fast", queue_size=4, pending_timeout_seconds=0.30, allow_fast_output=True),
        )

        self.assertIs(pipeline._queue.get_nowait(), strong)
        self.assertIs(pipeline._queue.get_nowait(), weak)

    def test_queue_full_with_strong_candidate_drops_older_weak_candidate(self):
        recognizer = FakeRecognizer("push")
        pipeline, stats, _seen = self._pipeline(recognizer)
        pipeline._queue_size = 2
        pipeline._queue = __import__("queue").Queue(maxsize=2)
        weak = SpeechWorkItem(
            segment=_segment(voice_duration_seconds=0.15),
            trace=LatencyTrace("", 1.0, 1.0),
            candidate_labels=("candidate", "short_segment", "low_confidence"),
            low_confidence=True,
            short_segment=True,
        )
        strong_queued = SpeechWorkItem(
            segment=_segment(duration_seconds=1.0, voice_duration_seconds=0.9, peak_rms_dbfs=-24.0),
            trace=LatencyTrace("", 1.5, 1.5),
            candidate_labels=("candidate",),
        )
        strong_incoming = SpeechWorkItem(
            segment=_segment(duration_seconds=1.1, voice_duration_seconds=1.0, peak_rms_dbfs=-23.0),
            trace=LatencyTrace("", 2.0, 2.0),
            candidate_labels=("candidate",),
        )

        pipeline._queue.put_nowait(weak)
        pipeline._queue.put_nowait(strong_queued)
        pipeline._enqueue_with_backpressure(
            strong_incoming,
            RecognitionModePolicy(mode="fast", queue_size=2, pending_timeout_seconds=0.30, allow_fast_output=True),
        )

        queued = [pipeline._queue.get_nowait(), pipeline._queue.get_nowait()]
        self.assertNotIn(weak, queued)
        self.assertIn(strong_queued, queued)
        self.assertIn(strong_incoming, queued)
        self.assertEqual(stats["dropped_speech"], 1)

    def test_clear_pending_work_drops_queued_and_pending_items(self):
        recognizer = FakeRecognizer("push")
        pipeline, stats, _seen = self._pipeline(recognizer)
        pending = SpeechWorkItem(
            segment=_segment(voice_duration_seconds=0.15),
            trace=LatencyTrace("", 1.0, 1.0),
            candidate_labels=("candidate", "short_segment"),
            short_segment=True,
        )
        queued = SpeechWorkItem(
            segment=_segment(duration_seconds=1.0, voice_duration_seconds=0.9, peak_rms_dbfs=-24.0),
            trace=LatencyTrace("", 2.0, 2.0),
            candidate_labels=("candidate",),
        )
        pipeline._pending_buffer.add_or_merge(pending, now=1.0)
        pipeline._queue.put_nowait(queued)

        dropped = pipeline.clear_pending_work("test_clear")

        self.assertEqual(dropped, 2)
        self.assertFalse(pipeline._pending_buffer.has_pending())
        self.assertTrue(pipeline._queue.empty())
        self.assertEqual(stats["dropped_speech"], 2)

    def test_queue_full_with_only_strong_segments_drops_current_weak_candidate(self):
        recognizer = FakeRecognizer("push")
        pipeline, stats, _seen = self._pipeline(recognizer)
        pipeline._queue_size = 2
        pipeline._queue = __import__("queue").Queue(maxsize=2)
        strong_one = SpeechWorkItem(
            segment=_segment(duration_seconds=1.0, voice_duration_seconds=0.9, peak_rms_dbfs=-24.0),
            trace=LatencyTrace("", 1.0, 1.0),
            candidate_labels=("candidate",),
        )
        strong_two = SpeechWorkItem(
            segment=_segment(duration_seconds=1.1, voice_duration_seconds=1.0, peak_rms_dbfs=-23.0),
            trace=LatencyTrace("", 1.5, 1.5),
            candidate_labels=("candidate",),
        )
        weak_incoming = SpeechWorkItem(
            segment=_segment(voice_duration_seconds=0.15),
            trace=LatencyTrace("", 2.0, 2.0),
            candidate_labels=("candidate", "short_segment", "low_confidence"),
            low_confidence=True,
            short_segment=True,
        )

        pipeline._queue.put_nowait(strong_one)
        pipeline._queue.put_nowait(strong_two)
        pipeline._enqueue_with_backpressure(
            weak_incoming,
            RecognitionModePolicy(mode="fast", queue_size=2, pending_timeout_seconds=0.30, allow_fast_output=True),
        )

        queued = [pipeline._queue.get_nowait(), pipeline._queue.get_nowait()]
        self.assertIn(strong_one, queued)
        self.assertIn(strong_two, queued)
        self.assertNotIn(weak_incoming, queued)
        self.assertEqual(stats["dropped_speech"], 1)

    def test_busy_queue_delays_weak_candidate_instead_of_enqueueing(self):
        recognizer = FakeRecognizer("push")
        pipeline, _stats, _seen = self._pipeline(recognizer)
        pipeline._recognition_busy = True
        weak = SpeechWorkItem(
            segment=_segment(voice_duration_seconds=0.15),
            trace=LatencyTrace("", 1.0, 1.0),
            candidate_labels=("candidate", "short_segment", "low_confidence"),
            low_confidence=True,
            short_segment=True,
        )

        pipeline._enqueue_with_backpressure(
            weak,
            RecognitionModePolicy(
                mode="fast",
                queue_size=4,
                pending_timeout_seconds=0.30,
                allow_fast_output=True,
                busy_weak_delay_seconds=0.50,
                busy_weak_stale_seconds=1.60,
            ),
        )

        self.assertTrue(pipeline._busy_weak_buffer.has_pending())
        self.assertTrue(pipeline._queue.empty())

    def test_busy_queue_does_not_delay_strong_candidate(self):
        recognizer = FakeRecognizer("push")
        pipeline, _stats, _seen = self._pipeline(recognizer)
        pipeline._recognition_busy = True
        strong = SpeechWorkItem(
            segment=_segment(duration_seconds=1.0, voice_duration_seconds=0.9, peak_rms_dbfs=-24.0),
            trace=LatencyTrace("", 1.0, 1.0),
            candidate_labels=("candidate",),
        )

        pipeline._enqueue_with_backpressure(
            strong,
            RecognitionModePolicy(
                mode="fast",
                queue_size=4,
                pending_timeout_seconds=0.30,
                allow_fast_output=True,
                busy_weak_delay_seconds=0.50,
                busy_weak_stale_seconds=1.60,
            ),
        )

        self.assertFalse(pipeline._queue.empty())
        self.assertIs(pipeline._queue.get_nowait(), strong)


if __name__ == "__main__":
    unittest.main()
