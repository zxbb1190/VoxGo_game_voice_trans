"""Registration policy tests: callbacks are captured without installing OS hooks."""
import unittest
from unittest.mock import Mock, patch

from voxgo.config.hotkeys import HOTKEY_ACTIONS, hotkey_conflicts
from voxgo.config.models import HotkeyConfig
from voxgo.runtime.hotkeys import HotkeyManager


class HotkeyConflictTests(unittest.TestCase):
    def setUp(self):
        self.notify = Mock()
        self.manager = HotkeyManager(self.notify)
        self.callbacks = {name: Mock() for name, _, _ in HOTKEY_ACTIONS}

    def test_defaults_have_no_conflict_and_mode_callback_is_registered(self):
        config = HotkeyConfig()
        self.assertEqual(hotkey_conflicts(config), [])
        with patch('voxgo.runtime.hotkeys.keyboard.add_hotkey', side_effect=lambda key, callback: key) as add:
            self.manager.setup(config, self.callbacks)
        self.assertIn(('ctrl+alt+m', self.callbacks['toggle_display_mode']), [call.args for call in add.call_args_list])
        self.assertEqual(len(self.manager._handles), 4)
        self.notify.assert_not_called()

    def test_existing_user_binding_wins_when_new_default_conflicts(self):
        config = HotkeyConfig(toggle_overlay='M + Alt + Control')
        self.assertEqual(hotkey_conflicts(config), [('toggle_overlay', 'toggle_display_mode')])
        with patch('voxgo.runtime.hotkeys.keyboard.add_hotkey', side_effect=lambda key, callback: key) as add:
            self.manager.setup(config, self.callbacks)
        registered = [call.args[1] for call in add.call_args_list]
        self.assertIn(self.callbacks['toggle_overlay'], registered)
        self.assertNotIn(self.callbacks['toggle_display_mode'], registered)
        self.assertIn(self.callbacks['toggle_translation'], registered)
        self.notify.assert_called_once()

    def test_disabled_shortcut_is_not_registered(self):
        with patch('voxgo.runtime.hotkeys.keyboard.add_hotkey') as add:
            self.manager.setup(HotkeyConfig(toggle_display_mode=''), self.callbacks)
        self.assertEqual(add.call_count, 3)
        self.notify.assert_not_called()

    def test_one_registration_failure_does_not_break_other_shortcuts_and_cleanup(self):
        def register(key, callback):
            if key == 'invalid':
                raise ValueError('invalid binding')
            return key
        with patch('voxgo.runtime.hotkeys.keyboard.add_hotkey', side_effect=register):
            self.manager.setup(HotkeyConfig(toggle_overlay='invalid'), self.callbacks)
        self.assertIn('ctrl+alt+m', self.manager._handles)
        self.notify.assert_called_once()
        with patch('voxgo.runtime.hotkeys.keyboard.remove_hotkey') as remove:
            self.manager.remove_all()
        self.assertEqual(remove.call_count, 3)
        self.assertEqual(self.manager._handles, [])
