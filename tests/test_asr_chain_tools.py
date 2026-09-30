"""Safety gates for paired ASR chain comparisons."""

import unittest

from scripts.asr_chain_compare import compare


def report(paths, *, failures=None):
    return {
        "variant": "baseline",
        "selection": [{"group": "libri_fast", "id": "clip-1"}],
        "records": [
            {"experiment_group": "libri_fast", "id": "clip-1", "path": path,
             "normalized_reference_words": 2, "reference_words": 2,
             "normalized_errors": 0, "deletions": 0, "segments": 1,
             "inference_seconds": 0.1, "repetition_failure": False,
             "raw_repetition_failure": False, "runaway_guarded": False}
            for path in paths
        ],
        "failures": failures or [],
    }


class AsrChainCompareTest(unittest.TestCase):
    def test_rejects_partial_or_failed_reports(self):
        baseline = report(("whole", "capture_cut", "full_pipeline"))
        partial = report(("capture_cut",))
        partial["variant"] = "capture_plus_0p5"
        # A path can be omitted by a targeted A/B, but selected cases within
        # that path must still match exactly.
        self.assertEqual(compare(baseline, partial)["case_count"], 1)
        partial["records"] = []
        with self.assertRaisesRegex(ValueError, "identical cases"):
            compare(baseline, partial)
        failed = report(("capture_cut",), failures=["clip failed"])
        with self.assertRaisesRegex(ValueError, "zero-failure"):
            compare(baseline, failed)


if __name__ == "__main__":
    unittest.main()
