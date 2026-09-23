"""Audio capture lifecycle and bounded recovery after device changes."""

import queue
import os
import threading
from dataclasses import replace

from loguru import logger

from voxgo.audio.capture import (
    SAFE_MAX_SPEECH_THRESHOLD_DBFS,
    SystemAudioCapture,
    default_loopback_device_id,
    finish_audio_reinitialization,
    list_input_devices,
    stop_active_audio_monitors,
)
from voxgo.audio.benchmark import BenchmarkAudioOptions, BenchmarkAudioSource
from voxgo.i18n import ui_text
from voxgo.audio.windows_endpoints import active_output_endpoint_ids, default_output_endpoint_id


class AudioRuntime:
    RECOVERY_DELAYS = (0, 2, 5, 10)

    def __init__(
        self,
        config_getter,
        speech_callback,
        notify_user,
        write_crash_report,
        benchmark_options: BenchmarkAudioOptions = None,
    ):
        self._config_getter = config_getter
        self._speech_callback = speech_callback
        self._notify_user = notify_user
        self._write_crash_report = write_crash_report
        self._benchmark_options = benchmark_options
        self.capture = None
        self._lock = threading.RLock()
        self._io_lock = threading.Lock()
        self._recovery_thread = None
        self._recovery_cancel = threading.Event()
        self._notices = queue.SimpleQueue()
        self._stopped = False
        self._preferred_device = None
        self._needs_recovery = False
        self._recovery_exhausted = False
        self._follow_default = False
        self._prefer_default_once = False
        self._default_watch_stop = threading.Event()
        self._default_watch_thread = None
        self._observed_default_id = ""
        self._observed_active_ids = None
        self._endpoint_generation = 0
        self._reported_missing_device_id = ""

    def _language(self):
        return getattr(getattr(self._config_getter(), "app", None), "language", "")

    def _notice(self, zh_title, en_title, zh_message, en_message, level="状态"):
        self._notices.put((zh_title, en_title, zh_message, en_message, level))

    def _flush_notices(self):
        while True:
            try:
                zh_title, en_title, zh_message, en_message, level = self._notices.get_nowait()
            except queue.Empty:
                break
            lang = self._language()
            self._notify_user(
                ui_text(lang, zh_title, en_title),
                ui_text(lang, zh_message, en_message),
                ui_text(lang, level, "Error" if level == "错误" else "Status"),
            )

    def _dispose_capture(self):
        capture = self.capture
        if capture is not None:
            capture.stop()
            if self.capture is capture:
                self.capture = None

    def _make_capture(self, audio_config, allow_fallback=False):
        if self._benchmark_options:
            capture = BenchmarkAudioSource(audio_config, self._benchmark_options)
        else:
            capture = SystemAudioCapture(audio_config)
        try:
            capture.set_speech_callback(self._speech_callback)
            if allow_fallback:
                capture.start(allow_fallback=True)
            else:
                capture.start()
        except Exception:
            capture.stop()
            raise
        return capture

    def start(self, notice_title: str = "音频捕获已启动", reuse_noise_gate: bool = False):
        # Cancel before waiting for an in-flight device open. All PortAudio
        # stop/open calls are serialized, including a manual settings restart.
        self._recovery_cancel.set()
        with self._io_lock, self._lock:
            self._stopped = False
            # A manual settings change supersedes an in-flight recovery.
            self._recovery_cancel = threading.Event()
            config = self._config_getter()
            self._follow_default = not any((
                config.audio.input_device_id,
                config.audio.input_device_name,
                config.audio.input_device_index is not None,
            ))
            self._prefer_default_once = False
            self._observed_default_id = ""
            self._observed_active_ids = None
            self._endpoint_generation = 0
            self._recovery_exhausted = False
            self._reported_missing_device_id = ""
            previous_noise_gate = None
            if self.capture:
                if reuse_noise_gate and hasattr(self.capture, "current_noise_gate"):
                    previous_noise_gate = self.capture.current_noise_gate()
                self._dispose_capture()
            if previous_noise_gate and previous_noise_gate[2]:
                config.audio.initial_noise_floor_dbfs = previous_noise_gate[0]
                config.audio.initial_energy_threshold_dbfs = min(
                    float(previous_noise_gate[1]), SAFE_MAX_SPEECH_THRESHOLD_DBFS,
                )
            else:
                config.audio.initial_noise_floor_dbfs = None
                config.audio.initial_energy_threshold_dbfs = None
            try:
                self.capture = self._make_capture(config.audio)
            except Exception as exc:
                self._needs_recovery = True
                self._ensure_default_watch()
                self._schedule_recovery(exc)
                raise
            self._needs_recovery = False
            self._preferred_device = dict(self.capture.selected_device or {})
            self._ensure_default_watch()
            if self._benchmark_options:
                notice_title = "基准音频已启动"
            self._notify_user(notice_title, f"{self.describe_selected_device()} -> mono", "状态")

    def restart(self, on_error, reuse_noise_gate: bool = False):
        try:
            self.start("音频设置已更新", reuse_noise_gate=reuse_noise_gate)
        except Exception as exc:
            on_error(exc)

    def _schedule_recovery(self, reason):
        if self._benchmark_options:
            return
        with self._lock:
            if self._stopped or self._recovery_exhausted:
                return
            self._needs_recovery = True
            if self._recovery_thread and self._recovery_thread.is_alive():
                return
            cancel = self._recovery_cancel
            self._notice(
                "音频设备恢复中", "Recovering audio device",
                "正在重新连接音频设备…", "Reconnecting to an audio device…",
            )
            self._recovery_thread = threading.Thread(
                target=self._recover, args=(cancel, self._endpoint_generation),
                name="audio-device-recovery", daemon=True,
            )
            self._recovery_thread.start()
            logger.warning("音频设备故障，开始自动恢复: {}", reason)

    def _recovery_config(self):
        audio_config = replace(self._config_getter().audio)
        if self._prefer_default_once:
            audio_config.input_device_id = ""
            audio_config.input_device_name = ""
            audio_config.input_device_index = None
            return audio_config
        preferred = self._preferred_device or {}
        if preferred:
            audio_config.input_device_id = preferred.get("device_id", "")
            audio_config.input_device_name = preferred.get("name", "")
            audio_config.input_device_index = preferred.get("index")
        return audio_config

    def _recover(self, cancel, observed_generation):
        for delay in self.RECOVERY_DELAYS:
            if cancel.wait(delay):
                return
            old_capture = None
            old_disposed = False
            try:
                with self._io_lock:
                    with self._lock:
                        if self._stopped or cancel.is_set() or cancel is not self._recovery_cancel:
                            return
                        old_capture = self.capture
                        self.capture = None
                        # Re-enumerate on every attempt; the selected stable id
                        # wins, then the current default output/loopback is tried.
                        audio_config = self._recovery_config()
                    if old_capture is not None:
                        try:
                            old_capture.stop()
                        except Exception:
                            with self._lock:
                                if self.capture is None:
                                    self.capture = old_capture
                            raise
                        old_disposed = True
                    if cancel.is_set():
                        return
                    # An audio-test monitor keeps PortAudio initialized and its
                    # device list frozen. Stop those monitors before re-init.
                    stop_active_audio_monitors()
                    try:
                        if cancel.is_set():
                            return
                        recovered = self._make_capture(audio_config, allow_fallback=True)
                        with self._lock:
                            endpoint_changed = self._endpoint_generation != observed_generation
                            if endpoint_changed:
                                self._needs_recovery = True
                                self._recovery_exhausted = False
                            if (self._stopped or cancel.is_set()
                                    or cancel is not self._recovery_cancel or endpoint_changed):
                                discard = True
                            else:
                                discard = False
                                self.capture = recovered
                                old_id = (self._preferred_device or {}).get("device_id")
                                self._preferred_device = dict(recovered.selected_device or {})
                                if old_id and old_id != self._preferred_device.get("device_id"):
                                    self._follow_default = True
                                self._prefer_default_once = False
                                self._needs_recovery = False
                                self._recovery_exhausted = False
                                self._ensure_default_watch()
                        if discard:
                            recovered.stop()
                            return
                    finally:
                        finish_audio_reinitialization()
                self._notice(
                    "音频设备已恢复", "Audio device restored",
                    "已重新连接音频设备。", "Audio capture is connected again.",
                )
                logger.info("音频设备自动恢复成功: {}", self.describe_selected_device())
                return
            except Exception as exc:
                if old_capture is not None and not old_disposed:
                    with self._lock:
                        if self.capture is None:
                            self.capture = old_capture
                logger.warning("音频设备自动恢复尝试失败: {}", exc)
        with self._lock:
            if not self._stopped and not cancel.is_set() and cancel is self._recovery_cancel:
                changed_during_retry = self._endpoint_generation != observed_generation
                self._needs_recovery = changed_during_retry
                self._recovery_exhausted = not changed_during_retry
                if not changed_during_retry:
                    self._notice(
                        "音频设备恢复失败", "Audio device recovery failed",
                        "未找到可用音频设备，请检查连接或在设置中选择设备。",
                        "No usable audio device was found. Check its connection or select one in Settings.",
                        "错误",
                    )

    def stop(self):
        self.cancel_recovery()
        if not self._io_lock.acquire(timeout=2):
            raise RuntimeError("audio recovery did not release device I/O")
        try:
            with self._lock:
                self._dispose_capture()
        finally:
            self._io_lock.release()
        # Join outside every device/state lock so the watcher can finish its
        # current enumeration. A stuck driver is reported to shutdown instead
        # of being counted as a clean stop.
        for worker in (self._recovery_thread, self._default_watch_thread):
            if worker and worker.is_alive() and worker is not threading.current_thread():
                worker.join(timeout=2)
                if worker.is_alive():
                    raise RuntimeError("audio recovery worker did not stop")

    def cancel_recovery(self):
        """Immediately prevent a pending attempt from opening a new stream."""
        self._stopped = True
        self._needs_recovery = False
        self._recovery_cancel.set()
        self._default_watch_stop.set()

    def _ensure_default_watch(self):
        if self._benchmark_options or self._stopped:
            return
        if self._default_watch_thread and self._default_watch_thread.is_alive() and not self._default_watch_stop.is_set():
            return
        stop = threading.Event()
        self._default_watch_stop = stop
        self._default_watch_thread = threading.Thread(
            target=self._watch_default_loopback, args=(stop,),
            name="audio-default-output-watch", daemon=True,
        )
        self._default_watch_thread.start()

    def _watch_default_loopback(self, stop):
        first_check = True
        while not stop.wait(0 if first_check else 3):
            first_check = False
            with self._lock:
                if self._stopped:
                    continue
                capture = self.capture
                selected_id = (capture.selected_device or {}).get("device_id", "") if capture else ""
                follow_default = self._follow_default
            if os.name == "nt":
                active_ids = active_output_endpoint_ids()
                default_id = default_output_endpoint_id() if follow_default else ""
                if active_ids is None or stop.is_set():
                    continue
                with self._lock:
                    if stop.is_set() or self._stopped or self.capture is not capture:
                        continue
                    previous_ids = self._observed_active_ids
                    self._observed_active_ids = active_ids
                    active_changed = previous_ids is not None and previous_ids != active_ids
                    default_changed = False
                    if default_id:
                        previous_default = self._observed_default_id
                        self._observed_default_id = default_id
                        default_changed = bool(previous_default and previous_default != default_id)
                    if active_changed or default_changed:
                        self._endpoint_generation += 1
                        self._recovery_exhausted = False
                        if default_changed:
                            self._prefer_default_once = True
                if active_changed or default_changed:
                    self._schedule_recovery("audio endpoints changed")
                continue
            if capture is None:
                continue
            # PortAudio freezes its device list while any PyAudio instance is
            # active. Non-Windows hosts use the ordinary enumerator fallback.
            try:
                available_ids = {item.get("device_id", "") for item in list_input_devices(cancel_event=stop)}
            except Exception as exc:
                logger.debug("音频设备状态检测失败: {}", exc)
                continue
            with self._lock:
                if stop.is_set() or self._stopped or self.capture is not capture:
                    continue
                if selected_id in available_ids:
                    self._reported_missing_device_id = ""
                    missing = False
                elif selected_id and self._reported_missing_device_id != selected_id:
                    self._reported_missing_device_id = selected_id
                    missing = True
                else:
                    missing = False
            if missing:
                with self._lock:
                    self._endpoint_generation += 1
                    self._recovery_exhausted = False
                self._schedule_recovery("selected audio device removed")
                continue
            if not follow_default:
                continue
            try:
                default_id = default_loopback_device_id(cancel_event=stop)
            except Exception as exc:
                logger.debug("默认音频设备检测失败: {}", exc)
                continue
            if not default_id or not selected_id:
                continue
            with self._lock:
                if stop.is_set() or self._stopped or self.capture is not capture:
                    continue
                previous_default_id = self._observed_default_id
                self._observed_default_id = default_id
                # Trigger once per actual default-device transition. If that
                # device is unusable, repeatedly restarting a working fallback
                # stream would make the application lose audio every 3 seconds.
                if not previous_default_id or previous_default_id == default_id:
                    continue
                self._prefer_default_once = True
                self._endpoint_generation += 1
                self._recovery_exhausted = False
            self._schedule_recovery("default output changed")

    def clear_pending_audio(self) -> int:
        if not self._lock.acquire(blocking=False):
            return 0
        try:
            if self.capture and hasattr(self.capture, "clear_pending_audio"):
                return self.capture.clear_pending_audio()
            return 0
        finally:
            self._lock.release()

    def process_tick(self, running: bool, paused: bool):
        self._flush_notices()
        if not running or self._stopped:
            return
        if paused:
            self.clear_pending_audio()
            return
        if not self._lock.acquire(blocking=False):
            return
        try:
            capture = self.capture
            if capture is None:
                error = RuntimeError("capture unavailable") if self._needs_recovery else None
            else:
                error = capture.health_error() if hasattr(capture, "health_error") else None
                if error is None:
                    try:
                        capture.process_audio()
                    except Exception as exc:
                        logger.warning("音频捕获处理异常: {}", exc)
                        error = exc
        finally:
            self._lock.release()
        if error is not None:
            self._schedule_recovery(error)

    def describe_selected_device(self) -> str:
        config = self._config_getter()
        if not self.capture or not self.capture.selected_device:
            if config.audio.input_device_index is not None:
                return f"[{config.audio.input_device_index}] {config.audio.input_device_name}"
            return "自动选择"
        device = self.capture.selected_device
        return (
            f"{device['type']} [{device['index']}]: {device['name']} "
            f"({device['sample_rate']}Hz/{device['channels']}ch)"
        )

    def list_devices(self):
        if self._benchmark_options:
            return []
        try:
            return list_input_devices()
        except Exception as exc:
            self._write_crash_report("音频设备枚举失败", exc)
            logger.warning("音频设备枚举失败: {}", exc)
            self._notify_user("音频设备枚举失败", str(exc), "错误")
            return []
