import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch

from voxgo.analytics.retention import cleanup_remote


class RemoteRetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'remote'
        self.epoch = str(uuid.uuid4())
        self.current = self.root / self.epoch
        self.shards = self.current / 'shards'
        self.today = datetime.now(timezone.utc).date()

    def write(self, path, content=b'{}'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_old_epochs_removed_active_identity_state_and_lock_preserved(self):
        old = self.write(self.root / str(uuid.uuid4()) / 'shards' / 'p' / 'x.json')
        kept = [self.write(self.current / name) for name in
                ['aggregate.json', 'identity.json', 'upload.lock']]
        self.write(self.root / 'unrelated' / 'file')
        cleanup_remote(self.root, self.epoch)
        self.assertFalse(old.exists())
        self.assertTrue(all(path.exists() for path in kept))
        self.assertTrue((self.root / 'unrelated' / 'file').exists())

    def test_denial_removes_all_epoch_data(self):
        self.write(self.current / 'identity.json')
        cleanup_remote(self.root, None)
        self.assertFalse(self.current.exists())

    def test_seven_utc_days_including_boundary_and_corrupt_files(self):
        paths = {}
        for offset in [-7, -6, 0, 1]:
            day = self.today + timedelta(days=offset)
            paths[offset] = self.write(self.shards / str(uuid.uuid4()) / (day.isoformat() + '.json'))
        corrupt = self.write(self.shards / 'p' / ((self.today - timedelta(days=7)).isoformat() + '.json.corrupt-1'))
        temp = self.write(self.shards / 'p' / '.snapshot-old')
        age = datetime.now(timezone.utc).timestamp() - 8 * 86400
        os.utime(temp, (age, age))
        cleanup_remote(self.root, self.epoch)
        self.assertFalse(paths[-7].exists())
        self.assertFalse(paths[-7].parent.exists())
        self.assertTrue(paths[-6].exists())
        self.assertTrue(paths[0].exists())
        self.assertFalse(paths[1].exists())
        self.assertFalse(corrupt.exists())
        self.assertFalse(temp.exists())

    def test_file_and_byte_caps_include_temporary_files(self):
        for i in range(95):
            self.write(self.shards / str(i) / (self.today.isoformat() + '.json'), b'x' * 30000)
        self.write(self.shards / 'temp' / '.snapshot-new', b'x' * 30000)
        cleanup_remote(self.root, self.epoch)
        remaining = [p for p in self.shards.rglob('*') if p.is_file()]
        self.assertLessEqual(len(remaining), 90)
        self.assertLessEqual(sum(p.stat().st_size for p in remaining), 2 * 1024 * 1024)
        self.assertFalse((self.shards / 'temp' / '.snapshot-new').exists())

    def test_small_scan_budget_progressively_removes_old_epoch(self):
        old = self.root / str(uuid.uuid4())
        for i in range(12):
            self.write(old / str(i))
        with patch('voxgo.analytics.retention.SCAN_LIMIT', 4):
            for _ in range(15):
                cleanup_remote(self.root, self.epoch)
        self.assertFalse(old.exists())

    def test_symlink_never_follows_external_directory(self):
        external = self.write(Path(self.temp.name) / 'outside' / 'keep')
        self.root.mkdir(parents=True)
        link = self.root / str(uuid.uuid4())
        try:
            link.symlink_to(external.parent, target_is_directory=True)
        except OSError:
            self.skipTest('symlink creation unavailable')
        cleanup_remote(self.root, self.epoch)
        self.assertTrue(external.exists())
        self.assertFalse(link.exists())
