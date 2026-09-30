"""Wall-clock replay through VoxGo's real capture and speech worker."""

from __future__ import annotations

import hashlib
import itertools
import time
from collections import defaultdict
from dataclasses import replace

import numpy as np
from loguru import logger

from voxgo.asr.pipeline import SpeechPipeline
from voxgo.audio.capture import AudioConfig, apply_audio_latency_preset, apply_english_realtime_latency_bias
from voxgo.config.loader import default_app_config
from voxgo.runtime.events import EventBus, TranscriptReady


class RecordingRecognizer:
    def __init__(self, recognizer):
        self.recognizer = recognizer
        self.calls = []

    def __getattr__(self, name):
        return getattr(self.recognizer, name)

    def transcribe_audio_bytes_with_language(self, audio_bytes, sample_rate=44100, language_override=None):
        started = time.perf_counter()
        result = self.recognizer.transcribe_audio_bytes_with_language(
            audio_bytes, sample_rate=sample_rate, language_override=language_override
        )
        self.calls.append((audio_bytes, result, time.perf_counter() - started))
        return result


def run_full_pipeline(samples, preset: str, recognizer, *, trace=False,
                      audio_overrides=None, policy_overrides=None,
                      filter_override=None, budget_override=None,
                      merge_override=None):
    """Return actual TranscriptReady output and ASR calls for one isolated clip."""
    # Keep the same English audio bias as the capture_cut path.
    audio = AudioConfig(latency_mode=preset, sample_rate=16000, channels=1)
    apply_audio_latency_preset(audio)
    apply_english_realtime_latency_bias(audio, preset)
    for name, value in (audio_overrides or {}).items():
        if name not in {"max_speech_seconds", "pre_roll_ms", "speech_idle_timeout_ms"}:
            raise ValueError(f"unsupported benchmark audio override: {name}")
        setattr(audio, name, value)
    config = default_app_config()
    config.audio = audio
    config.whisper = recognizer.config
    config.whisper.pure_english_environment = True
    config.whisper.language = "en"
    config.translation.source_lang = "en"
    config.translation.target_lang = "zh"

    events = []
    notices = []
    bus = EventBus()
    output_events = []
    replay_started = time.perf_counter()
    process_cpu_started = time.process_time()

    def on_output(event):
        events.append(event)
        output_events.append({"text": event.text, "seconds_from_start": time.perf_counter() - replay_started})

    bus.subscribe(TranscriptReady, on_output)
    recorded = RecordingRecognizer(recognizer)
    stats = defaultdict(int)
    ids = itertools.count(1)
    pipeline = SpeechPipeline(
        lambda: config, lambda: recorded, bus, stats,
        lambda: True, lambda: False, lambda: str(next(ids)), {},
        lambda *args: notices.append(args),
    )
    if policy_overrides:
        allowed = {"pending_timeout_seconds", "busy_weak_delay_seconds",
                   "busy_weak_stale_seconds", "weak_cooldown_seconds",
                   "weak_stale_drop_seconds"}
        if set(policy_overrides) - allowed:
            raise ValueError(f"unsupported benchmark policy override: {set(policy_overrides) - allowed}")
        baseline_policy = pipeline._mode_policy

        def experimental_policy(current_config):
            policy = replace(baseline_policy(current_config), **policy_overrides)
            pipeline._pending_buffer.timeout_seconds = policy.pending_timeout_seconds
            pipeline._busy_weak_buffer.timeout_seconds = policy.busy_weak_delay_seconds
            return policy

        pipeline._mode_policy = experimental_policy
    if budget_override:
        if budget_override != "preserve_voice_0p4":
            raise ValueError(f"unsupported benchmark budget override: {budget_override}")
        baseline_budget = pipeline._should_drop_weak_for_inference_budget

        def experimental_budget(item, mode_policy, now):
            if float(getattr(item.segment, "voice_duration_seconds", 0.0) or 0.0) >= 0.40:
                return False
            return baseline_budget(item, mode_policy, now)

        pipeline._should_drop_weak_for_inference_budget = experimental_budget
    if merge_override:
        if merge_override != "pending_voice_1p0":
            raise ValueError(f"unsupported benchmark merge override: {merge_override}")

        def experimental_should_pending(item):
            return float(getattr(item.segment, "voice_duration_seconds", 0.0) or 0.0) < 1.0

        pipeline._should_pending = experimental_should_pending
    filter_rescues = []
    if filter_override:
        if filter_override != "confident_short":
            raise ValueError(f"unsupported benchmark filter override: {filter_override}")
        baseline_filter = pipeline._weak_transcript_filter.drop_reason

        def experimental_filter(item, result, now=None):
            reason = baseline_filter(item, result, now)
            no_speech = getattr(result, "no_speech_prob", None)
            log_probability = getattr(result, "avg_logprob", None)
            language_probability = getattr(result, "language_probability", None)
            if (reason.startswith("weak_candidate_low_asr_confidence")
                    and no_speech is not None and float(no_speech) < 0.10
                    and log_probability is not None and float(log_probability) > -1.0
                    and language_probability is not None and float(language_probability) >= 0.9
                    and str(getattr(result, "language", "") or "").lower() == "en"):
                filter_rescues.append({"reason": reason, "text": str(getattr(result, "text", "") or "")})
                return ""
            return reason

        pipeline._weak_transcript_filter.drop_reason = experimental_filter
    # Import here to avoid a circular import with the benchmark runner.
    from scripts.run_asr_benchmark import capture_segments

    captured_events = []
    queue_events = []
    trace_events = []
    sink_id = None
    if trace:
        def log_event(message):
            record = message.record
            trace_events.append({
                "seconds_from_start": time.perf_counter() - replay_started,
                "component": record["name"],
                "level": record["level"].name,
                "message": record["message"],
            })

        sink_id = logger.add(log_event, level="DEBUG", filter=lambda record: record["name"] in {
            "voxgo.audio.capture", "voxgo.asr.pipeline", "voxgo.asr.whisper_engine"
        })

        # Observe the real queue operations without changing the production
        # queue policy. The worker calls get(); internal priority scans use
        # get_nowait(), so the latter are not mistaken for worker dequeues.
        original_put_nowait = pipeline._queue.put_nowait
        original_get = pipeline._queue.get

        def queue_item_details(item):
            segment = getattr(item, "segment", None)
            return {
                "audio_sha256": hashlib.sha256(segment.audio_data).hexdigest() if segment else None,
                "voice_duration_seconds": segment.voice_duration_seconds if segment else None,
                "labels": list(getattr(item, "candidate_labels", ()) or ()),
            }

        def observe_put(item):
            original_put_nowait(item)
            queue_events.append({"action": "enqueue", "seconds_from_start": time.perf_counter() - replay_started,
                                 "queue_size_after": pipeline._queue.qsize(), **queue_item_details(item)})

        def observe_get(*args, **kwargs):
            item = original_get(*args, **kwargs)
            queue_events.append({"action": "dequeue", "seconds_from_start": time.perf_counter() - replay_started,
                                 "queue_size_after": pipeline._queue.qsize(), **queue_item_details(item)})
            return item

        pipeline._queue.put_nowait = observe_put
        pipeline._queue.get = observe_get

    def on_segment(segment, source_seconds):
        pcm = np.frombuffer(segment.audio_data, dtype="<i2")
        rms = float(np.sqrt(np.mean((pcm.astype(np.float32) / 32768.0) ** 2))) if len(pcm) else 0.0
        captured_events.append({
            "emitted_source_seconds": source_seconds,
            "emitted_wall_seconds": time.perf_counter() - replay_started,
            "duration_seconds": segment.duration_seconds,
            "voice_duration_seconds": segment.voice_duration_seconds,
            "reason": segment.reason,
            "rms_dbfs": float(20 * np.log10(max(rms, 1e-10))),
            "peak_rms_dbfs": segment.peak_rms_dbfs,
            "energy_threshold_dbfs": segment.energy_threshold_dbfs,
            "vad_voice_blocks": segment.vad_voice_blocks,
            "energy_voice_blocks": segment.energy_voice_blocks,
            "block_count": segment.block_count,
            "audio_sha256": hashlib.sha256(segment.audio_data).hexdigest(),
        })

    def record_and_submit(segment, source_seconds):
        on_segment(segment, source_seconds)
        pipeline.on_speech_detected(segment)

    try:
        pipeline.start()
        captured = capture_segments(
            samples, preset,
            on_segment=lambda segment, source_seconds: record_and_submit(segment, source_seconds),
            pace_realtime=True,
            audio_overrides=audio_overrides,
        )
        capture_finished = time.perf_counter()
        source_pcm = samples.astype("<i2", copy=False).tobytes()
        source_pcm += b"\0" * (16000 * 2 * 3)
        search_from = 0
        for segment, event in zip(captured, captured_events):
            byte_offset = source_pcm.find(segment.audio_data, search_from)
            if byte_offset < 0:
                byte_offset = source_pcm.find(segment.audio_data)
            if byte_offset >= 0:
                event["source_start_seconds"] = byte_offset / (2 * 16000)
                event["source_end_seconds"] = (byte_offset + len(segment.audio_data)) / (2 * 16000)
                event["source_boundary_exact"] = True
                search_from = byte_offset + len(segment.audio_data)
            else:
                event["source_start_seconds"] = None
                event["source_end_seconds"] = None
                event["source_boundary_exact"] = False
        # Pending candidates are released by the real worker's timeout loop.
        # Keep the worker alive until every queued item has passed ASR/filtering.
        deadline = time.monotonic() + max(60.0, len(samples) / 16000 * 4 + 20)
        while time.monotonic() < deadline:
            if (pipeline._queue.empty() and not pipeline._recognition_busy
                    and not pipeline._pending_buffer.has_pending()
                    and not pipeline._busy_weak_buffer.has_pending()):
                time.sleep(0.25)
                if (pipeline._queue.empty() and not pipeline._recognition_busy
                        and not pipeline._pending_buffer.has_pending()
                        and not pipeline._busy_weak_buffer.has_pending()):
                    break
            time.sleep(0.05)
        else:
            raise TimeoutError("speech pipeline did not drain")
    finally:
        try:
            stopped = pipeline.stop()
        finally:
            if sink_id is not None:
                logger.remove(sink_id)
        if not stopped:
            raise TimeoutError("speech worker did not stop")
    if stats.get("errors", 0):
        raise RuntimeError(f"speech pipeline reported {stats['errors']} recognition errors")
    return {
        "hypothesis": " ".join(event.text for event in events).strip(),
        "raw_hypothesis": " ".join(str(getattr(result, "raw_text", getattr(result, "text", "")) or "")
                                   for _, result, _ in recorded.calls).strip(),
        "events": events,
        "calls": recorded.calls,
        "captured_segments": captured,
        "stats": dict(stats),
        "notices": notices,
        "filter_rescues": filter_rescues,
        "captured_events": captured_events,
        "queue_events": queue_events,
        "output_events": output_events,
        "trace_events": trace_events,
        "wall_seconds_total": time.perf_counter() - replay_started,
        "process_cpu_seconds": time.process_time() - process_cpu_started,
        "capture_finished_seconds": capture_finished - replay_started,
    }
