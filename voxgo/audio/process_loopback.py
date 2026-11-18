"""Windows process-tree loopback, independent of the default output device.

Uses the public ActivateAudioInterfaceAsync API (Windows build 20348+).
All COM/audio operations live on one worker; no system-audio fallback.
"""
import ctypes as C
from ctypes import wintypes as W
import os
import sys
import threading
import time
import uuid

import numpy as np

from voxgo.audio.capture import SystemAudioCapture


def support_error():
    if sys.platform != "win32" or sys.getwindowsversion().build < 20348:
        return "Application capture requires Windows build 20348 or later"
    return ""


def process_identity(pid):
    """Path and creation time protect against PID reuse, without debug privilege."""
    if sys.platform != "win32" or not pid:
        return None
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    kernel.OpenProcess.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    kernel.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return None
    try:
        size = W.DWORD(32768)
        path = C.create_unicode_buffer(size.value)
        times = [W.FILETIME() for _ in range(4)]
        if not kernel.QueryFullProcessImageNameW(handle, 0, path, C.byref(size)):
            return None
        if not kernel.GetProcessTimes(handle, *(C.byref(t) for t in times)):
            return None
        created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        return {"pid": int(pid), "path": path.value, "started": created}
    finally:
        kernel.CloseHandle(handle)


def list_applications():
    """List visible desktop applications; choosing their root includes child audio."""
    if support_error():
        return []
    user = C.WinDLL("user32", use_last_error=True)
    callback_type = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    user.EnumWindows.argtypes = [callback_type, W.LPARAM]
    user.IsWindowVisible.argtypes = [W.HWND]
    user.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, C.c_int]
    user.GetWindowThreadProcessId.argtypes = [W.HWND, C.POINTER(W.DWORD)]
    found = {}

    @callback_type
    def visit(hwnd, _):
        if not user.IsWindowVisible(hwnd):
            return True
        title = C.create_unicode_buffer(256)
        user.GetWindowTextW(hwnd, title, len(title))
        pid = W.DWORD()
        user.GetWindowThreadProcessId(hwnd, C.byref(pid))
        if title.value and pid.value != os.getpid() and pid.value not in found:
            identity = process_identity(pid.value)
            if identity:
                found[pid.value] = {**identity, "title": title.value}
        return True

    user.EnumWindows(visit, 0)
    return sorted(found.values(), key=lambda item: (item["path"].lower(), item["pid"]))


def resolve_target(config):
    path = str(config.process_path or "").casefold()
    if not path:
        raise RuntimeError("Select an application first")
    pid = int(config.process_id or 0)
    if pid:
        identity = process_identity(pid)
        if (identity and identity["path"].casefold() == path
                and int(config.process_started or 0) == identity["started"]):
            return identity
        raise RuntimeError("The selected application exited. Select it again in Settings.")
    matches = [app for app in list_applications() if app["path"].casefold() == path]
    if len(matches) != 1:
        raise RuntimeError("Start the selected application and select it again in Settings.")
    return matches[0]


class _Guid(C.Structure):
    _fields_ = [("bytes", C.c_ubyte * 16)]


def _guid(value):
    return _Guid((C.c_ubyte * 16).from_buffer_copy(uuid.UUID(value).bytes_le))


def _method(ptr, index, *args):
    table = C.cast(ptr, C.POINTER(C.POINTER(C.c_void_p))).contents
    return C.WINFUNCTYPE(C.c_long, C.c_void_p, *args)(table[index])


def _check(hr):
    if hr < 0:
        raise OSError(f"Windows audio error 0x{hr & 0xffffffff:08X}")


def _release(ptr):
    if ptr:
        _method(ptr, 2)(ptr)


class _WaveFormat(C.Structure):
    _pack_ = 2
    _fields_ = [("tag", W.WORD), ("channels", W.WORD), ("rate", W.DWORD),
                ("bytes_per_second", W.DWORD), ("align", W.WORD),
                ("bits", W.WORD), ("extra", W.WORD)]


# Async activation may complete after a timeout. Retain the COM callback until
# Windows releases its final reference, even when the capture has been stopped.
_pending_callbacks = {}
_retired_callbacks = []


def _activate(pid, cancel):
    # Do not free a ctypes callback thunk while its native Release call returns.
    now = time.monotonic()
    _retired_callbacks[:] = [(when, refs) for when, refs in _retired_callbacks if now - when < 60]
    class Blob(C.Structure):
        _fields_ = [("size", W.ULONG), ("data", C.c_void_p)]

    class Value(C.Union):
        _fields_ = [("blob", Blob), ("padding", C.c_ubyte * (16 if C.sizeof(C.c_void_p) == 8 else 8))]

    class Variant(C.Structure):
        _fields_ = [("vt", W.WORD), ("reserved", W.WORD * 3), ("value", Value)]

    params = (W.DWORD * 3)(1, pid, 0)  # process loopback, include target process tree
    variant = Variant(65, (W.WORD * 3)(), Value(blob=Blob(C.sizeof(params), C.addressof(params))))
    iid = _guid("1CB9AD4C-DBFA-4c32-B178-C2F568A703B2")
    done = threading.Event()
    state = {"refs": 1}
    qi_type = C.WINFUNCTYPE(C.c_long, C.c_void_p, C.POINTER(_Guid), C.POINTER(C.c_void_p))
    ref_type = C.WINFUNCTYPE(W.ULONG, C.c_void_p)
    complete_type = C.WINFUNCTYPE(C.c_long, C.c_void_p, C.c_void_p)
    supported = {uuid.UUID(v).bytes_le for v in (
        "00000000-0000-0000-C000-000000000046",  # IUnknown
        "94EA2B94-E9CC-49E0-C0FF-EE64CA8F5B90",  # IAgileObject
        "41D949AB-9862-444A-80F6-C261334DA5EB",  # completion handler
    )}

    @qi_type
    def query(this, requested, output):
        if bytes(requested.contents.bytes) in supported:
            output[0] = this
            addref(this)
            return 0
        output[0] = None
        return -2147467262

    @ref_type
    def addref(_):
        state["refs"] += 1
        return state["refs"]

    @ref_type
    def release(this):
        state["refs"] -= 1
        if not state["refs"]:
            refs = _pending_callbacks.pop(this, None)
            if refs:
                _retired_callbacks.append((time.monotonic(), refs))
        return state["refs"]

    @complete_type
    def completed(_, operation):
        state["operation"] = operation
        _method(operation, 1)(operation)  # keep alive for the worker to read result
        done.set()
        return 0

    table = (C.c_void_p * 4)(*(C.cast(f, C.c_void_p).value for f in (query, addref, release, completed)))
    instance = C.pointer(C.cast(table, C.c_void_p))
    address = C.cast(instance, C.c_void_p).value
    _pending_callbacks[address] = (instance, table, query, addref, release, completed, params, variant)
    operation = C.c_void_p()
    api = C.WinDLL("Mmdevapi").ActivateAudioInterfaceAsync
    api.argtypes = [W.LPCWSTR, C.POINTER(_Guid), C.POINTER(Variant), C.c_void_p, C.POINTER(C.c_void_p)]
    api.restype = C.c_long
    try:
        _check(api("VAD\\Process_Loopback", C.byref(iid), C.byref(variant), instance, C.byref(operation)))
        # The native async operation has no cancellation API. Worker waits for its
        # completion; callers can stop immediately without releasing live callbacks.
        done.wait()
        result, unknown, client = C.c_long(), C.c_void_p(), C.c_void_p()
        try:
            _check(_method(operation, 3, C.POINTER(C.c_long), C.POINTER(C.c_void_p))(
                operation, C.byref(result), C.byref(unknown)))
            _check(result.value)
            if cancel.is_set():
                raise RuntimeError("Capture cancelled")
            _check(_method(unknown, 0, C.POINTER(_Guid), C.POINTER(C.c_void_p))(
                unknown, C.byref(iid), C.byref(client)))
            return client
        finally:
            _release(unknown)
            _release(state.get("operation"))
    finally:
        _release(operation)
        release(address)


def stream_process(pid, cancel, on_ready, on_pcm):
    """Read stereo 44.1 kHz PCM16 using the documented Windows sample format."""
    ole = C.OleDLL("ole32")
    _check(ole.CoInitializeEx(None, 0))
    client = capture = None
    try:
        client = _activate(pid, cancel)
        fmt = _WaveFormat(1, 2, 44100, 176400, 4, 16, 0)
        _check(_method(client, 3, C.c_int, W.DWORD, C.c_longlong, C.c_longlong,
                       C.POINTER(_WaveFormat), C.c_void_p)(client, 0, 0x80020000, 200000, 0, C.byref(fmt), None))
        capture = C.c_void_p()
        iid = _guid("C8ADBD64-E71E-48a0-A4DE-185C395CD317")
        _check(_method(client, 14, C.POINTER(_Guid), C.POINTER(C.c_void_p))(
            client, C.byref(iid), C.byref(capture)))
        _check(_method(client, 10)(client))
        on_ready()
        while not cancel.wait(0.01):
            frames = W.UINT()
            _check(_method(capture, 5, C.POINTER(W.UINT))(capture, C.byref(frames)))
            while frames.value and not cancel.is_set():
                data, count, flags = C.c_void_p(), W.UINT(), W.DWORD()
                _check(_method(capture, 3, C.POINTER(C.c_void_p), C.POINTER(W.UINT),
                               C.POINTER(W.DWORD), C.c_void_p, C.c_void_p)(
                    capture, C.byref(data), C.byref(count), C.byref(flags), None, None))
                try:
                    pcm = bytes(count.value * 4) if flags.value & 2 else C.string_at(data, count.value * 4)
                    on_pcm(pcm)
                finally:
                    _check(_method(capture, 4, W.UINT)(capture, count.value))
                _check(_method(capture, 5, C.POINTER(W.UINT))(capture, C.byref(frames)))
        _check(_method(client, 11)(client))
    finally:
        _release(capture)
        _release(client)
        ole.CoUninitialize()


class ProcessAudioCapture(SystemAudioCapture):
    def __init__(self, config):
        super().__init__(config, initialize_portaudio=False)
        self._cancel = threading.Event()
        self._ready = threading.Event()
        self._worker = None
        self._target = None
        self._identity_checked_at = 0.0
        self._pending = bytearray()

    def start(self, allow_fallback=False):
        error = support_error()
        if error:
            raise RuntimeError(error)
        self._target = resolve_target(self.config)
        self.config.sample_rate = self._capture_sample_rate = 44100
        self.config.channels = 1
        self.selected_device = {"type": "应用 / App", "index": self._target["pid"],
                                "name": os.path.basename(self._target["path"]),
                                "sample_rate": 44100, "channels": 2}
        self._running = True
        self._worker = threading.Thread(target=self._run, name="process-loopback", daemon=True)
        self._worker.start()
        if not self._ready.wait(5):
            self.stop()
            raise RuntimeError("Application audio startup timed out. Open Settings → Help & Feedback → Automatic diagnostics.")
        if self._capture_fault:
            raise self._capture_fault

    def _run(self):
        try:
            self._verify_target()
            stream_process(self._target["pid"], self._cancel, self._capture_started, self._receive)
        except Exception as exc:
            if not self._cancel.is_set():
                self._capture_fault = exc
        finally:
            self._ready.set()

    def _verify_target(self):
        expected = {key: self._target[key] for key in ("pid", "path", "started")}
        if process_identity(self._target["pid"]) != expected:
            raise RuntimeError("The selected application exited. Select it again in Settings.")

    def _capture_started(self):
        self._verify_target()
        self._ready.set()

    def _receive(self, pcm):
        if self._cancel.is_set():
            return
        mono = np.frombuffer(pcm, dtype=np.int16).reshape(-1, 2).mean(axis=1).astype(np.int16)
        self._pending.extend(mono.tobytes())
        size = max(1, int(44100 * self.config.chunk_duration_ms / 1000)) * 2
        while len(self._pending) >= size:
            self._enqueue_audio_block(bytes(self._pending[:size]))
            del self._pending[:size]

    def health_error(self):
        if self._capture_fault:
            return self._capture_fault
        if time.monotonic() - self._identity_checked_at > 0.5:
            self._identity_checked_at = time.monotonic()
            if process_identity(self._target["pid"]) != {key: self._target[key] for key in ("pid", "path", "started")}:
                self._capture_fault = RuntimeError("The selected application exited. Select it again in Settings.")
                self._cancel.set()
                self.clear_pending_audio()
        return self._capture_fault

    def stop(self):
        self._running = False
        self._cancel.set()
        if self._worker and self._worker is not threading.current_thread():
            self._worker.join(timeout=1)
        self.clear_pending_audio()


class ProcessLevelMonitor:
    def __init__(self, config, on_level):
        self.capture = ProcessAudioCapture(config)
        self._on_level = on_level
        self._cancel = threading.Event()
        self._thread = None

    def start(self):
        self.capture.start()
        self._thread = threading.Thread(target=self._run, name="process-level-monitor", daemon=True)
        self._thread.start()

    def _run(self):
        peak = -120.0
        while not self._cancel.wait(0.1):
            try:
                error = self.capture.health_error()
                if error is None:
                    self.capture.process_audio()
            except Exception as exc:
                error = exc
            if error:
                self._on_level({"error": str(error)})
                return
            rms = self.capture.last_level_dbfs
            peak = max(peak, rms)
            self._on_level({"rms_dbfs": rms, "peak_dbfs": peak, "detected": rms > -70,
                            "device": self.capture.selected_device})

    def stop(self):
        self._cancel.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=1)
        self.capture.stop()
