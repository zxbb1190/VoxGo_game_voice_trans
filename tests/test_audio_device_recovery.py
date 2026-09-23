import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from voxgo.audio.runtime import AudioRuntime
from voxgo.audio.capture import (
    AudioConfig, SystemAudioCapture, _ACTIVE_LEVEL_MONITORS,
    _LEVEL_MONITOR_REGISTRY_LOCK,
)
from voxgo.audio.windows_endpoints import _query_default_output_endpoint_id


def config():
    return SimpleNamespace(
        app=SimpleNamespace(language="en-US"),
        audio=AudioConfig(
            input_device_id="loopback:0:old speakers",
            input_device_name="Old Speakers",
            input_device_index=3,
            initial_noise_floor_dbfs=None,
            initial_energy_threshold_dbfs=None,
        ),
    )


class FakeCapture:
    def __init__(self, selected=None, fault=None):
        self.selected_device = selected or {
            "index": 3, "name": "Old Speakers", "device_id": "loopback:0:old speakers",
            "type": "system", "sample_rate": 48000, "channels": 2,
        }
        self.fault = fault
        self.stop = Mock()
        self.process_audio = Mock()

    def health_error(self):
        return self.fault


class RecoveryTests(unittest.TestCase):
    def make_runtime(self):
        settings = config()
        notice = Mock()
        runtime = AudioRuntime(lambda: settings, Mock(), notice, Mock())
        runtime.RECOVERY_DELAYS = (0, 0, 0, 0)
        self.addCleanup(runtime.stop)
        return runtime, notice

    def test_one_recovery_task_and_preferred_device_first(self):
        runtime, notice = self.make_runtime()
        original = FakeCapture(fault=RuntimeError("disconnected"))
        runtime.capture = original
        runtime._preferred_device = dict(original.selected_device)
        entered = threading.Event()
        release = threading.Event()
        tried = []
        replacement = FakeCapture({
            "index": 9, "name": "New Speakers", "device_id": "loopback:0:new speakers",
            "type": "system", "sample_rate": 48000, "channels": 2,
        })

        def open_capture(audio_config, allow_fallback=False):
            tried.append((audio_config.input_device_id, audio_config.input_device_index, allow_fallback))
            entered.set()
            release.wait(2)
            return replacement

        runtime._make_capture = open_capture
        runtime.process_tick(True, False)
        self.assertTrue(entered.wait(2))
        first_thread = runtime._recovery_thread
        tick_started = time.monotonic()
        runtime.process_tick(True, False)
        self.assertLess(time.monotonic() - tick_started, 0.3)
        self.assertIs(runtime._recovery_thread, first_thread)
        release.set()
        first_thread.join(2)
        runtime.process_tick(True, False)
        self.assertEqual(tried, [("loopback:0:old speakers", 3, True)])
        self.assertIs(runtime.capture, replacement)
        self.assertEqual(runtime._preferred_device["device_id"], "loopback:0:new speakers")
        self.assertIn("Audio device restored", str(notice.call_args_list))

    def test_failure_is_bounded_and_reports_error(self):
        runtime, notice = self.make_runtime()
        runtime.capture = FakeCapture(fault=RuntimeError("device gone"))
        attempted = []

        def fail(audio_config, allow_fallback=False):
            attempted.append(allow_fallback)
            raise OSError("no device")

        runtime._make_capture = fail
        runtime.process_tick(True, False)
        runtime._recovery_thread.join(2)
        runtime.process_tick(True, False)
        self.assertEqual(attempted, [True] * 4)
        self.assertIsNone(runtime.capture)
        self.assertFalse(runtime._needs_recovery)
        self.assertIn("Audio device recovery failed", str(notice.call_args_list))

    def test_shutdown_cancels_waiting_recovery(self):
        runtime, _ = self.make_runtime()
        runtime.RECOVERY_DELAYS = (10,)
        runtime.capture = FakeCapture(fault=RuntimeError("device gone"))
        runtime.process_tick(True, False)
        worker = runtime._recovery_thread
        runtime.cancel_recovery()
        worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertFalse(runtime._needs_recovery)

    def test_selector_falls_back_only_during_recovery(self):
        capture = SystemAudioCapture.__new__(SystemAudioCapture)
        capture._configured_device_candidates = Mock(return_value=[(3, {"name": "old"})])
        capture._has_configured_device = Mock(return_value=True)
        capture._auto_device_candidates = Mock(return_value=[(7, {"name": "new"})])
        capture._first_usable_device = Mock(side_effect=[None, 7])
        self.assertEqual(capture.find_loopback_device(allow_fallback=True), 7)
        capture._first_usable_device = Mock(return_value=None)
        capture._auto_device_candidates.reset_mock()
        self.assertIsNone(capture.find_loopback_device())
        capture._auto_device_candidates.assert_not_called()

    def test_reused_numeric_index_does_not_override_stable_identity(self):
        capture = SystemAudioCapture.__new__(SystemAudioCapture)
        capture.config = AudioConfig(
            input_device_id="loopback:0:old speakers",
            input_device_name="Old Speakers", input_device_index=3,
        )
        capture._input_device_entries = Mock(return_value=[
            (3, {"index": 3, "name": "Other Device", "hostApi": 0,
                 "isLoopbackDevice": True, "maxInputChannels": 2}),
        ])
        self.assertEqual(capture._configured_device_candidates(), [])

    def test_processing_finishes_before_old_stream_is_stopped(self):
        runtime, _ = self.make_runtime()
        entered = threading.Event()
        release = threading.Event()
        old = FakeCapture()

        def process():
            entered.set()
            release.wait(2)

        old.process_audio.side_effect = process
        runtime.capture = old
        runtime._make_capture = Mock(return_value=FakeCapture())
        tick = threading.Thread(target=runtime.process_tick, args=(True, False))
        tick.start()
        self.assertTrue(entered.wait(1))
        runtime._schedule_recovery("forced change")
        self.assertFalse(old.stop.called)
        release.set()
        tick.join(1)
        runtime._recovery_thread.join(1)
        self.assertEqual(old.stop.call_count, 1)

    def test_default_output_change_requests_default_first(self):
        runtime, _ = self.make_runtime()
        runtime.capture = FakeCapture()
        runtime._follow_default = True
        runtime._observed_default_id = "endpoint-old"
        runtime._schedule_recovery = Mock()
        stop = Mock()
        stop.wait.side_effect = [False, True]
        stop.is_set.return_value = False
        with patch("voxgo.audio.runtime.os.name", "nt"), patch("voxgo.audio.runtime.active_output_endpoint_ids", return_value=frozenset({"endpoint-new"})), patch("voxgo.audio.runtime.default_output_endpoint_id", return_value="endpoint-new"):
            runtime._watch_default_loopback(stop)
        self.assertTrue(runtime._prefer_default_once)
        runtime._schedule_recovery.assert_called_once_with("audio endpoints changed")
        self.assertEqual(runtime._recovery_config().input_device_id, "")

    def test_same_unusable_default_does_not_restart_fallback_repeatedly(self):
        runtime, _ = self.make_runtime()
        runtime.capture = FakeCapture()
        runtime._follow_default = True
        runtime._observed_default_id = "endpoint-new"
        runtime._schedule_recovery = Mock()
        stop = Mock()
        stop.wait.side_effect = [False, False, True]
        stop.is_set.return_value = False
        with patch("voxgo.audio.runtime.os.name", "nt"), patch("voxgo.audio.runtime.active_output_endpoint_ids", return_value=frozenset({"endpoint-new"})), patch("voxgo.audio.runtime.default_output_endpoint_id", return_value="endpoint-new"):
            runtime._watch_default_loopback(stop)
        runtime._schedule_recovery.assert_not_called()

    def test_new_endpoint_resumes_recovery_after_bounded_failure(self):
        runtime, _ = self.make_runtime()
        runtime.capture = None
        runtime._needs_recovery = False
        runtime._recovery_exhausted = True
        runtime._observed_active_ids = frozenset({"endpoint-old"})
        runtime._schedule_recovery = Mock()
        stop = Mock()
        stop.wait.side_effect = [False, True]
        stop.is_set.return_value = False
        with patch("voxgo.audio.runtime.os.name", "nt"), patch("voxgo.audio.runtime.active_output_endpoint_ids", return_value=frozenset({"endpoint-new"})):
            runtime._watch_default_loopback(stop)
        self.assertFalse(runtime._recovery_exhausted)
        runtime._schedule_recovery.assert_called_once_with("audio endpoints changed")

    def test_exhausted_fault_does_not_start_retries_on_every_tick(self):
        runtime, _ = self.make_runtime()
        runtime.capture = FakeCapture(fault=RuntimeError("disconnected"))
        runtime._recovery_exhausted = True
        runtime._make_capture = Mock()
        runtime.process_tick(True, False)
        runtime.process_tick(True, False)
        self.assertIsNone(runtime._recovery_thread)
        runtime._make_capture.assert_not_called()

    def test_inactive_explicit_device_triggers_recovery(self):
        runtime, _ = self.make_runtime()
        runtime.capture = FakeCapture(fault=RuntimeError("disconnected"))
        runtime._schedule_recovery = Mock()
        runtime.process_tick(True, False)
        runtime._schedule_recovery.assert_called_once()

    def test_windows_endpoint_probe_does_not_use_com_after_init_failure(self):
        ole32 = SimpleNamespace(
            CoInitializeEx=Mock(return_value=0x80004005),
            CoCreateInstance=Mock(), CoTaskMemFree=Mock(), CoUninitialize=Mock(),
        )
        self.assertEqual(_query_default_output_endpoint_id(ole32), "")
        ole32.CoCreateInstance.assert_not_called()
        ole32.CoUninitialize.assert_not_called()

    def test_audio_test_monitor_stops_before_reopening_capture(self):
        runtime, _ = self.make_runtime()
        runtime.capture = FakeCapture(fault=RuntimeError("disconnected"))
        calls = []

        class Monitor:
            def stop(self, for_recovery=False):
                calls.append(("monitor", for_recovery))

        monitor = Monitor()
        with _LEVEL_MONITOR_REGISTRY_LOCK:
            _ACTIVE_LEVEL_MONITORS.add(monitor)
        self.addCleanup(_ACTIVE_LEVEL_MONITORS.discard, monitor)
        runtime._make_capture = Mock(side_effect=lambda *_args, **_kwargs: (
            calls.append(("capture", True)) or FakeCapture()
        ))
        runtime.process_tick(True, False)
        runtime._recovery_thread.join(2)
        self.assertEqual(calls[:2], [("monitor", True), ("capture", True)])

    def test_endpoint_change_during_last_retry_is_not_lost(self):
        runtime, _ = self.make_runtime()
        runtime.capture = FakeCapture(fault=RuntimeError("disconnected"))
        attempts = []

        def fail(*_args, **_kwargs):
            attempts.append(1)
            if len(attempts) == 4:
                runtime._endpoint_generation += 1
            raise OSError("unavailable")

        runtime._make_capture = fail
        runtime.process_tick(True, False)
        runtime._recovery_thread.join(2)
        self.assertEqual(len(attempts), 4)
        self.assertTrue(runtime._needs_recovery)
        self.assertFalse(runtime._recovery_exhausted)


if __name__ == "__main__":
    unittest.main()
