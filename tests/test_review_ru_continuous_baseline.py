import copy
import unittest

from scripts.review_ru_continuous_baseline import coverage,reviewed_assessment,human_review_items
from pathlib import Path


class RecordingReviewTests(unittest.TestCase):
    def fixture(self):
        def segment(sid,start,text,status="translation_ready"):
            row=dict(segment_id=sid,captured=True,parents=[],spans=[[start,start+1000]],pcm_sha256=sid,
                sources=[dict(id="sample",wav_start_frame=start-48000,wav_end_frame=start-47000)],
                duration_seconds=.0625,voice_duration_seconds=.05,reason="capture",status=status,
                asr_ms=1000,asr=dict(text=text,raw_text=text,language="ru",language_probability=.8))
            if status=="translation_ready":row.update(retained_text=text,translation_input=text)
            if status=="language_gate_dropped":row.update(retained_text=text,translation_input="",language_gate_reason="text_script_mismatch")
            return row
        segments=[segment("s1",48000,"один"),segment("s2",49000,"два","language_gate_dropped")]
        result=dict(segments=segments,clips=[dict(stream_start_frame=48000,stream_end_frame=50000)],spec=dict(strategy="legacy"),
            work_items=[dict(status=s["status"],queue_wait_ms=1) for s in segments],replay_cpu_seconds=2.,peak_sampled_rss_bytes=100,replay_wall_seconds=4.)
        record=dict(id="sample",split="dev",seconds=.125,reference_text="один два",reference_status="pending",audio="audio.wav",speaker_group="unknown")
        events=[dict(kind="captured",segment_id=s["segment_id"],elapsed_ms=i*100,spans=s["spans"]) for i,s in enumerate(segments)]
        for s in segments:events += [dict(kind="whisper_start",segment_id=s["segment_id"]),dict(kind="whisper_end",segment_id=s["segment_id"])]
        events += [dict(kind="translation_boundary",segment_id="s2",skip_reason="text_script_mismatch",elapsed_ms=1200)]
        return result,record,events

    def test_language_gate_count_is_separate_and_cannot_disappear_from_all_rejections(self):
        result,record,events=self.fixture()
        metrics=reviewed_assessment(result,record,events)
        self.assertEqual(metrics["counts"]["post_asr_drops"],0)
        self.assertEqual(metrics["counts"]["translation_language_gate_drops"],1)
        self.assertEqual(metrics["counts"]["all_post_inference_rejections"],1)
        self.assertEqual(metrics["issues"][-1]["first_observed_stage"],"Pipeline.translation_language_gate")
        self.assertEqual(metrics["performance"]["capture_to_terminal_all"][0]["capture_to_terminal_ms"],1100)

    def test_actual_inference_reordering_suppresses_proxy_scoring(self):
        result,record,events=self.fixture()
        events=[e for e in events if e["kind"]!="whisper_end"]+[dict(kind="whisper_end",segment_id="s2"),dict(kind="whisper_end",segment_id="s1")]
        metrics=reviewed_assessment(result,record,events)
        self.assertEqual(metrics["raw"],"два один")
        self.assertFalse(metrics["alignment"]["valid"])
        self.assertIsNone(metrics["raw_metrics"]["proxy_wer"])
        self.assertEqual(metrics["counts"]["captured"],2)

    def test_raw_evidence_is_not_changed_and_human_labels_stay_unfilled(self):
        result,record,events=self.fixture();before=copy.deepcopy(result)
        reviewed_assessment(result,record,events)
        self.assertEqual(result,before)
        items=human_review_items(result,record,Path("raw"))
        self.assertTrue(all(i["human"]["status"]=="pending" and i["human"]["valid_semantics"] is None for i in items))
        self.assertTrue(all(i["reference_for_whole_recording_only"]==record["reference_text"] for i in items))

    def test_capture_coverage_does_not_call_silence_gaps_semantic_loss(self):
        result=coverage([[48010,48030],[48020,48040]],48000,48100)
        self.assertEqual(result["uncovered_source_intervals"],[[48000,48010],[48040,48100]])
        self.assertEqual(result["duplicate_frame_occurrences"],10)
        self.assertNotIn("semantic_error",result)


if __name__=="__main__":unittest.main()
