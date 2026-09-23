import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from voxgo.app import VoxGoApp
from voxgo.runtime.events import TranslationReady


class ExperienceAppTests(unittest.TestCase):
    def test_only_normal_translation_results_enable_copy(self):
        owner = VoxGoApp.__new__(VoxGoApp)
        owner._stopping = False
        owner._language_flow_revision = 1
        owner._overlay = Mock()
        owner._mobile = SimpleNamespace(server=None)
        owner._stats = {'translations': 0, 'errors': 0}
        for text, expected in (('Normal translation', True), ('[翻译失败] timeout', False), ('[未翻译] disabled', False)):
            owner._handle_translation_ready(TranslationReady('source', text, 'en', 'zh', 'item', 1))
            owner._overlay.update_translation.assert_called_with('item', text, copyable=expected)

    def test_tray_reset_calls_overlay_and_persists_position(self):
        owner = VoxGoApp.__new__(VoxGoApp)
        owner._overlay = Mock()
        owner._save_user_settings = Mock()
        owner._sync_tray_state = Mock()
        owner._tray_reset_overlay_position()
        owner._overlay.reset_overlay_position.assert_called_once_with()
        owner._save_user_settings.assert_called_once_with()
        owner._sync_tray_state.assert_called_once_with()
