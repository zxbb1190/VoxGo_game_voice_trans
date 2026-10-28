import hashlib
from pathlib import Path
import tempfile
import unittest
import wave

import numpy as np
import soundfile as sf

from scripts.review_beta_blockers import choose_recordings, edit_review, read_pcm, source_conversion, segment_review
from scripts.run_ru_continuous_baseline import input_stream


class FrozenBlockerReviewTests(unittest.TestCase):
    def test_most_severe_selection_also_keeps_single_russian_regression(self):
        rows = []
        for rid, legacy, aware in (("one", .9, .4), ("two", .8, .3), ("three", .7, .2), ("regression", .1, .6)):
            rows += [dict(id=rid, language="ru", strategy="legacy", cer=legacy),
                     dict(id=rid, language="ru", strategy="language_aware", cer=aware)]
        self.assertEqual(choose_recordings(rows, "ru"), ["one", "two", "three", "regression"])

    def test_character_alignment_does_not_fabricate_semantic_gold(self):
        review = edit_review("不要开枪2人", "開槍")
        counts = review["character_counts"]
        self.assertEqual(counts["reference_characters"], 6)
        self.assertEqual(counts["deletions"], 4)
        self.assertIsNone(review["human_semantic_verdict"])

    def test_original_quiet_float_conversion_and_saved_padding_are_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            samples = np.array([.0001, -.0001, 0.] * 107, dtype=np.float64)
            original, converted = root / "original.wav", root / "source.wav"
            sf.write(original, samples, 16000, subtype="FLOAT")
            quantized = np.round(samples * 32768).astype("<i2").tobytes()
            with wave.open(str(converted), "wb") as stream:
                stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(16000); stream.writeframes(quantized)
            row = dict(id="new", split="dev", audio=str(converted), original_file=str(original), frames=len(samples),
                       wav_sha256=hashlib.sha256(converted.read_bytes()).hexdigest(), pcm_sha256=hashlib.sha256(quantized).hexdigest(),
                       original_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
            pcm = read_pcm(row)
            self.assertTrue(source_conversion(row, pcm)["matches_frozen_conversion"])
            _, padded, unpadded = input_stream(row)
            self.assertGreater(len(padded)//2, unpadded)
            result = dict(replay_stream_sha256=hashlib.sha256(padded).hexdigest(), segments=[], activity_windows=[])
            review = segment_review(row, result, root, pcm)
            self.assertEqual(review["source_frames"], len(samples))
            result["replay_stream_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "stream mismatch"):
                segment_review(row, result, root, pcm)
            row["pcm_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "PCM fingerprint"):
                read_pcm(row)


if __name__ == "__main__":
    unittest.main()
