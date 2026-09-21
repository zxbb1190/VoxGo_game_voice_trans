import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from voxgo.asr.model_recovery import ModelCacheResetError, reset_model_cache


class ModelRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'models'
        self.root.mkdir()

    def cache(self, relative):
        path = self.root / relative
        path.mkdir(parents=True)
        (path / 'model.bin.part').write_bytes(b'incomplete')
        return path

    def test_removes_only_selected_model_both_sources(self):
        ms = self.cache('modelscope/Systran/faster-whisper-small')
        hf = self.cache('models--Systran--faster-whisper-small')
        other = self.cache('modelscope/Systran/faster-whisper-base')
        translation = self.cache('translation/en-zh')
        self.assertEqual(set(reset_model_cache(self.root, 'small')), {ms, hf})
        self.assertFalse(ms.exists())
        self.assertFalse(hf.exists())
        self.assertTrue((other / 'model.bin.part').exists())
        self.assertTrue((translation / 'model.bin.part').exists())

    def test_missing_is_idempotent(self):
        self.assertEqual(reset_model_cache(self.root, 'small'), ())
        self.assertEqual(reset_model_cache(self.root / 'missing', 'base'), ())

    def test_rejects_custom_names_and_paths(self):
        for name in ('../small', '/small', 'Systran/faster-whisper-small', r'..\small', '', None):
            with self.subTest(name=name), self.assertRaises(ModelCacheResetError):
                reset_model_cache(self.root, name)

    def test_alias_targets_actual_repository(self):
        cache = self.cache('models--Systran--faster-whisper-large-v3')
        self.assertEqual(reset_model_cache(self.root, 'large'), (cache,))

    def test_non_directory_refused_before_any_deletion(self):
        ms = self.cache('modelscope/Systran/faster-whisper-small')
        (self.root / 'models--Systran--faster-whisper-small').write_text('unexpected')
        with self.assertRaises(ModelCacheResetError):
            reset_model_cache(self.root, 'small')
        self.assertTrue(ms.exists())

    def test_link_refused_and_external_files_preserved(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        (outside / 'keep').write_text('keep')
        link = self.root / 'models--Systran--faster-whisper-small'
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Creating symbolic links is not permitted on this host')
        with self.assertRaises(ModelCacheResetError):
            reset_model_cache(self.root, 'small')
        self.assertEqual((outside / 'keep').read_text(), 'keep')

    def test_nested_link_prevents_deletion_of_either_provider(self):
        ms = self.cache('modelscope/Systran/faster-whisper-small')
        hf = self.cache('models--Systran--faster-whisper-small')
        outside = Path(self.tmp.name) / 'external-model'
        outside.write_text('keep')
        try:
            (hf / 'model.bin').symlink_to(outside)
        except OSError:
            self.skipTest('Creating symbolic links is not permitted on this host')
        with self.assertRaises(ModelCacheResetError):
            reset_model_cache(self.root, 'small')
        self.assertTrue(ms.exists())
        self.assertTrue(hf.exists())
        self.assertEqual(outside.read_text(), 'keep')

    def test_symlinked_root_refused(self):
        alias = Path(self.tmp.name) / 'alias'
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except OSError:
            self.skipTest('Creating symbolic links is not permitted on this host')
        cache = self.cache('models--Systran--faster-whisper-small')
        with self.assertRaises(ModelCacheResetError):
            reset_model_cache(alias, 'small')
        self.assertTrue(cache.exists())

    def test_permission_or_in_use_errors_are_actionable(self):
        self.cache('models--Systran--faster-whisper-small')
        with patch('voxgo.asr.model_recovery.shutil.rmtree', side_effect=PermissionError('private path')):
            with self.assertRaisesRegex(ModelCacheResetError, 'Close other VoxGo instances') as raised:
                reset_model_cache(self.root, 'small')
        self.assertNotIn('private path', str(raised.exception))


if __name__ == '__main__':
    unittest.main()
