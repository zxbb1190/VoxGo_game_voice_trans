import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from voxgo.analytics.lifecycle import LifecycleTracker


class LifecycleTrackerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name) / "scope"
        self.current = datetime(2026, 9, 21, 8, 0, tzinfo=timezone.utc)

    def tracker(self, **kwargs):
        return LifecycleTracker(self.root, "full-cuda", "0.4.3",
                                now=lambda: self.current, **kwargs)

    def shards(self):
        return [json.loads(path.read_text(encoding="utf-8"))
                for path in self.root.glob("shards/*/*.json")]

    def test_clean_exit_writes_compatible_shard_and_removes_marker(self):
        tracker = self.tracker()
        self.assertTrue(tracker.start())
        marker = tracker._marker
        self.assertTrue(marker.exists())
        self.assertTrue(tracker.mark_clean_exit())
        self.assertTrue(tracker.mark_clean_exit())
        self.assertFalse(marker.exists())
        self.assertEqual(self.shards(), [{
            "schema_version": 1,
            "date": "2026-09-21",
            "app_version": "0.4.3",
            "package_type": "full-cuda",
            "metrics": {"clean_exits": 1},
        }])

    def test_abandoned_run_is_recovered_once_as_unclean(self):
        first = self.tracker()
        self.assertTrue(first.start())
        old_marker = first._marker
        first.abandon()
        self.current += timedelta(seconds=3)

        second = self.tracker()
        self.assertTrue(second.start())
        self.assertFalse(old_marker.exists())
        unclean = [s for s in self.shards() if s["metrics"] == {"unclean_starts": 1}]
        self.assertEqual(len(unclean), 1)
        self.assertTrue(second.mark_clean_exit())

    def test_immediate_restart_recovers_process_killed_without_cleanup(self):
        script = (
            "import os,sys; "
            "from voxgo.analytics.lifecycle import LifecycleTracker; "
            "tracker=LifecycleTracker(sys.argv[1],'lite','0.4.3'); "
            "assert tracker.start(); os._exit(7)"
        )
        result = subprocess.run([sys.executable, "-c", script, str(self.root)],
                                cwd=Path(__file__).parent.parent, check=False)
        self.assertEqual(result.returncode, 7)
        restarted = self.tracker()
        self.assertTrue(restarted.start())
        unclean = [s for s in self.shards() if s["metrics"] == {"unclean_starts": 1}]
        self.assertEqual(len(unclean), 1)
        self.assertEqual(unclean[0]["package_type"], "lite")
        restarted.mark_clean_exit()

    def test_live_other_process_marker_is_not_recovered(self):
        first = self.tracker()
        self.assertTrue(first.start())
        self.current += timedelta(seconds=3)
        second = self.tracker()
        self.assertTrue(second.start())
        self.assertTrue(first._marker.exists())
        self.assertFalse(any("unclean_starts" in s["metrics"] for s in self.shards()))
        self.assertTrue(first.mark_clean_exit())
        self.assertTrue(second.mark_clean_exit())

    def test_recovery_retry_overwrites_same_shard_and_keeps_original_day(self):
        failed = self.tracker()
        self.assertTrue(failed.start())
        run_id = failed.run_id
        failed.abandon()
        marker_payload = json.loads(failed._marker.read_text(encoding="utf-8"))
        self.current += timedelta(seconds=3)

        recovering = self.tracker()
        self.assertTrue(recovering.start())
        intent = {
            "schema_version": 1,
            "run_id": run_id,
            "metric": "unclean_starts",
            "day": "2026-09-21",
            "app_version": "0.4.3",
            "package_type": "full-cuda",
        }
        # Simulate a process dying after the deterministic shard was replaced
        # but before its marker and intent were removed.
        old_marker = self.root / "runs" / f"{run_id}.json"
        old_marker.write_text(json.dumps(marker_payload), encoding="utf-8")
        old_time = self.current.timestamp() - 3
        os.utime(old_marker, (old_time, old_time))
        (self.root / "lifecycle-intents" / f"{run_id}.json").write_text(
            json.dumps(intent), encoding="utf-8")
        recovering.mark_clean_exit()
        self.current += timedelta(days=1)
        retry = self.tracker()
        self.assertTrue(retry.start())
        unclean = [s for s in self.shards() if s["metrics"] == {"unclean_starts": 1}]
        self.assertEqual(len(unclean), 1)
        self.assertEqual(unclean[0]["date"], "2026-09-21")
        retry.mark_clean_exit()

    def test_clean_exit_does_not_recreate_removed_consent_scope(self):
        tracker = self.tracker()
        self.assertTrue(tracker.start())
        import shutil
        tracker.abandon()
        shutil.rmtree(self.root)
        self.assertFalse(tracker.mark_clean_exit())
        self.assertFalse(self.root.exists())

    def test_retention_is_bounded_and_preserves_unrelated_shards(self):
        tracker = self.tracker(scan_limit=20)
        self.assertTrue(tracker.start())
        old = self.root / "shards" / ("a" * 32)
        old.mkdir()
        old.joinpath("2026-08-01.json").write_text(json.dumps({
            "schema_version": 1, "date": "2026-08-01", "app_version": "x",
            "package_type": "lite", "metrics": {"clean_exits": 1},
        }), encoding="utf-8")
        unrelated = self.root / "shards" / ("b" * 32) / "2026-08-01.json"
        unrelated.parent.mkdir()
        unrelated.write_text(json.dumps({"metrics": {"translation_success": 1}}),
                             encoding="utf-8")
        tracker._cleanup_shards(self.current.date())
        self.assertFalse(old.exists())
        self.assertTrue(unrelated.exists())
        tracker.mark_clean_exit()


if __name__ == "__main__":
    unittest.main()
