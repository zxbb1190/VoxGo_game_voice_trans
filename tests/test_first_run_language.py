import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from voxgo.config.loader import load_config
from voxgo.i18n import system_ui_language


class FirstRunLanguageTests(unittest.TestCase):
    def test_exact_system_language_policy(self):
        for system in ('zh_CN', 'zh_TW', 'zh_HK', 'zh_SG', 'en_US', 'ja_JP', 'C'):
            with self.subTest(system=system), patch('PyQt5.QtCore.QLocale.system', return_value=SimpleNamespace(name=lambda: system)):
                self.assertEqual(system_ui_language(), 'zh-CN' if system in ('zh_CN', 'zh_TW') else 'en-US')

    def test_new_language_is_persisted_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch('voxgo.i18n.system_ui_language', return_value='en-US'):
                self.assertEqual(load_config(runtime_dir=root).app.language, 'en-US')
            self.assertEqual(json.loads((root/'user_settings.json').read_text())['app']['language'], 'en-US')
            with patch('voxgo.i18n.system_ui_language', return_value='zh-CN') as probe:
                self.assertEqual(load_config(runtime_dir=root).app.language, 'en-US')
                probe.assert_not_called()

    def test_old_settings_and_completed_setup_are_never_overridden(self):
        for settings in ({'language': 'zh-CN'}, {'language': 'en-US'}, {'setup_completed': True}):
            with self.subTest(settings=settings), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root/'user_settings.json').write_text(json.dumps({'app': settings}))
                with patch('voxgo.i18n.system_ui_language', return_value='en-US') as probe:
                    loaded = load_config(runtime_dir=root)
                    self.assertEqual(loaded.app.language, settings.get('language', 'zh-CN'))
                    probe.assert_not_called()

    def test_bundled_defaults_do_not_override_new_system_language(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root/'_internal/config.json'
            path.parent.mkdir()
            path.write_text(json.dumps({'app': {'language': 'zh-CN'}}))
            with patch('voxgo.i18n.system_ui_language', return_value='en-US'):
                self.assertEqual(load_config(str(path), root).app.language, 'en-US')

    def test_external_config_is_historical(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root/'config.json'
            path.write_text(json.dumps({'app': {'language': 'zh-CN', 'setup_completed': True}}))
            with patch('voxgo.i18n.system_ui_language', return_value='en-US') as probe:
                self.assertEqual(load_config(str(path), root).app.language, 'zh-CN')
                probe.assert_not_called()
