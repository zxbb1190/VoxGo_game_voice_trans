"""Selection identity, bounded capture, and fail-closed runtime contracts."""
from dataclasses import replace
import threading
import unittest
from unittest.mock import Mock, patch

import numpy as np

from voxgo.audio.capture import AudioConfig
from voxgo.audio.process_loopback import ProcessAudioCapture, ProcessLevelMonitor, resolve_target
from voxgo.audio.runtime import AudioRuntime
from voxgo.config.loader import default_app_config


class ProcessAudioTests(unittest.TestCase):
    def setUp(self):
        self.identity = {"pid": 42, "path": r"C:\Games\game.exe", "started": 100}
        self.config = AudioConfig(source_mode="process", process_path=self.identity["path"],
                                  process_id=42, process_started=100)

    def test_pid_reuse_path_change_and_exit_all_fail_closed(self):
        for identity in (None, {**self.identity, "started": 101}, {**self.identity, "path": r"C:\Other.exe"}):
            with self.subTest(identity=identity), patch("voxgo.audio.process_loopback.process_identity", return_value=identity):
                with self.assertRaises(RuntimeError):
                    resolve_target(self.config)

    def test_saved_path_reconnects_only_unique_running_instance(self):
        saved = replace(self.config, process_id=0, process_started=0)
        with patch("voxgo.audio.process_loopback.list_applications", return_value=[self.identity]):
            self.assertEqual(resolve_target(saved), self.identity)
        for matches in ([], [self.identity, {**self.identity, "pid": 43}]):
            with patch("voxgo.audio.process_loopback.list_applications", return_value=matches):
                with self.assertRaises(RuntimeError):
                    resolve_target(saved)
        with self.assertRaises(RuntimeError):
            resolve_target(replace(saved, process_path=""))

    def test_selection_accepts_same_live_identity(self):
        with patch("voxgo.audio.process_loopback.process_identity", return_value=self.identity):
            self.assertEqual(resolve_target(self.config), self.identity)

    def test_stereo_downmix_rechunks_and_bounds_backlog(self):
        with patch("voxgo.audio.capture.pyaudio.PyAudio") as portaudio:
            capture = ProcessAudioCapture(self.config)
            portaudio.assert_not_called()
        block_frames = int(44100 * self.config.chunk_duration_ms / 1000)
        stereo = np.tile(np.array([1000, -500], dtype=np.int16), (block_frames * 8, 1))
        capture._receive(stereo.tobytes())
        self.assertEqual(capture._audio_queue.qsize(), self.config.audio_queue_max_blocks)
        mono = np.frombuffer(capture._audio_queue.get_nowait(), dtype=np.int16)
        self.assertEqual(len(mono), block_frames)
        self.assertTrue(np.all(mono == 250))
        capture.stop()
        capture._receive(stereo.tobytes())
        self.assertTrue(capture._audio_queue.empty())

    def test_target_exit_clears_pending_audio_and_cancels_native_reader(self):
        capture = ProcessAudioCapture(self.config)
        capture._target = self.identity
        capture._enqueue_audio_block(b"\x00\x01" * 100)
        with patch("voxgo.audio.process_loopback.process_identity", return_value=None):
            self.assertIsNotNone(capture.health_error())
        self.assertTrue(capture._cancel.is_set())
        self.assertTrue(capture._audio_queue.empty())

    def test_worker_ready_error_and_stop_release_reader(self):
        finished = threading.Event()
        def stream(pid, cancel, ready, pcm):
            ready()
            cancel.wait(2)
            finished.set()
        with patch("voxgo.audio.process_loopback.support_error", return_value=""), \
             patch("voxgo.audio.process_loopback.resolve_target", return_value=self.identity), \
             patch("voxgo.audio.process_loopback.process_identity", return_value=self.identity), \
             patch("voxgo.audio.process_loopback.stream_process", side_effect=stream):
            capture = ProcessAudioCapture(self.config)
            capture.start(allow_fallback=True)
            self.assertEqual(capture.selected_device["index"], 42)
            capture.stop()
            self.assertTrue(finished.is_set())
            self.assertFalse(capture._worker.is_alive())
        with patch("voxgo.audio.process_loopback.support_error", return_value="unsupported"):
            with self.assertRaisesRegex(RuntimeError, "unsupported"):
                ProcessAudioCapture(self.config).start()

    def test_native_error_surfaces_without_opening_system_capture(self):
        with patch("voxgo.audio.process_loopback.support_error", return_value=""), \
             patch("voxgo.audio.process_loopback.resolve_target", return_value=self.identity), \
             patch("voxgo.audio.process_loopback.process_identity", return_value=self.identity), \
             patch("voxgo.audio.process_loopback.stream_process", side_effect=OSError("denied")):
            capture = ProcessAudioCapture(self.config)
            with self.assertRaisesRegex(OSError, "denied"):
                capture.start()
            capture.stop()

    def test_runtime_application_failure_never_falls_back_or_watches_default(self):
        config = default_app_config()
        config.audio = self.config
        lost = Mock()
        runtime = AudioRuntime(lambda: config, Mock(), Mock(), Mock(), on_source_lost=lost)
        try:
            with patch("voxgo.audio.process_loopback.ProcessAudioCapture", side_effect=RuntimeError("missing")), \
                 patch("voxgo.audio.runtime.SystemAudioCapture") as system:
                with self.assertRaisesRegex(RuntimeError, "missing"):
                    runtime.start()
                for _ in range(3):
                    runtime.process_tick(True, False)
                system.assert_not_called()
                lost.assert_called_once()
                self.assertIsNone(runtime._default_watch_thread)
                self.assertIsNone(runtime._recovery_thread)
                self.assertEqual(runtime.last_error, "missing")
        finally:
            runtime.stop()

    def test_runtime_detects_target_exit_before_processing_old_audio(self):
        config = default_app_config()
        config.audio = self.config
        lost = Mock()
        runtime = AudioRuntime(lambda: config, Mock(), Mock(), Mock(), on_source_lost=lost)
        capture = Mock(health_error=Mock(return_value=RuntimeError("exited")))
        runtime.capture = capture
        runtime.process_tick(True, False)
        capture.process_audio.assert_not_called()
        capture.stop.assert_called_once()
        lost.assert_called_once()
        self.assertIsNone(runtime.capture)

    def test_level_monitor_reports_only_selected_source_and_stops(self):
        with patch("voxgo.audio.process_loopback.ProcessAudioCapture") as factory:
            capture = factory.return_value
            capture.health_error.side_effect = [None, RuntimeError("exited")]
            capture.last_level_dbfs = -42
            capture.selected_device = {"name": "game.exe"}
            payloads = []
            monitor = ProcessLevelMonitor(self.config, payloads.append)
            monitor.start()
            monitor._thread.join(1)
            monitor.stop()
            self.assertEqual(payloads[0]["device"]["name"], "game.exe")
            self.assertTrue(payloads[0]["detected"])
            self.assertEqual(payloads[1]["error"], "exited")
            capture.stop.assert_called_once()

    def test_real_identity_api_does_not_read_an_invalid_pid(self):
        from voxgo.audio.process_loopback import process_identity
        self.assertIsNone(process_identity(0))
        self.assertIsNone(process_identity(0xFFFFFFFE))
