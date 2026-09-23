"""Read the live Windows default output endpoint independently of PortAudio."""

import ctypes
import os
from ctypes import wintypes


class _Guid(ctypes.Structure):
    _fields_ = [
        ("data1", wintypes.DWORD),
        ("data2", wintypes.WORD),
        ("data3", wintypes.WORD),
        ("data4", ctypes.c_ubyte * 8),
    ]


def _guid(data1, data2, data3, tail):
    return _Guid(data1, data2, data3, (ctypes.c_ubyte * 8)(*tail))


_CLSID_ENUMERATOR = _guid(0xBCDE0395, 0xE52F, 0x467C, (0x8E, 0x3D, 0xC4, 0x57, 0x92, 0x91, 0x69, 0x2E))
_IID_ENUMERATOR = _guid(0xA95664D2, 0x9614, 0x4F35, (0xA7, 0x46, 0xDE, 0x8D, 0xB6, 0x36, 0x17, 0xE6))
_RPC_E_CHANGED_MODE = 0x80010106


def _method(interface, index, *argument_types):
    vtable = ctypes.cast(interface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    return ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argument_types)(vtable[index])


def _release(interface):
    if interface:
        _method(interface, 2)(interface)


def _query_default_output_endpoint_id(ole32):
    """Return an endpoint ID; all COM pointers and apartment refs are released."""
    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole32.CoInitializeEx.restype = ctypes.c_long
    ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(_Guid), ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(_Guid), ctypes.POINTER(ctypes.c_void_p),
    ]
    ole32.CoCreateInstance.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.restype = None
    ole32.CoUninitialize.argtypes = []
    ole32.CoUninitialize.restype = None
    initialized = False
    enumerator = ctypes.c_void_p()
    endpoint = ctypes.c_void_p()
    endpoint_id = ctypes.c_void_p()
    try:
        result = ole32.CoInitializeEx(None, 0) & 0xFFFFFFFF  # COINIT_MULTITHREADED
        if result in (0, 1):  # S_OK or S_FALSE both require CoUninitialize
            initialized = True
        elif result != _RPC_E_CHANGED_MODE:
            return ""
        result = ole32.CoCreateInstance(
            ctypes.byref(_CLSID_ENUMERATOR), None, 1,  # CLSCTX_INPROC_SERVER
            ctypes.byref(_IID_ENUMERATOR), ctypes.byref(enumerator),
        ) & 0xFFFFFFFF
        if result != 0 or not enumerator.value:
            return ""
        # IMMDeviceEnumerator::GetDefaultAudioEndpoint(eRender, eMultimedia).
        # PortAudio WASAPI's default output is the multimedia render endpoint.
        result = _method(enumerator, 4, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(
            enumerator, 0, 1, ctypes.byref(endpoint),
        ) & 0xFFFFFFFF
        if result != 0 or not endpoint.value:
            return ""
        result = _method(endpoint, 5, ctypes.POINTER(ctypes.c_void_p))(
            endpoint, ctypes.byref(endpoint_id),
        ) & 0xFFFFFFFF
        if result != 0 or not endpoint_id.value:
            return ""
        return ctypes.wstring_at(endpoint_id.value)
    finally:
        if endpoint_id.value:
            ole32.CoTaskMemFree(endpoint_id)
        _release(endpoint)
        _release(enumerator)
        if initialized:
            ole32.CoUninitialize()


def default_output_endpoint_id():
    if os.name != "nt":
        return ""
    try:
        return _query_default_output_endpoint_id(ctypes.windll.ole32)
    except (OSError, ValueError, AttributeError):
        return ""


def active_output_endpoint_ids():
    """Return live render endpoint IDs; None means the probe failed."""
    if os.name != "nt":
        return None
    try:
        return _query_active_output_endpoint_ids(ctypes.windll.ole32)
    except (OSError, ValueError, AttributeError):
        return None


def _query_active_output_endpoint_ids(ole32):
    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole32.CoInitializeEx.restype = ctypes.c_long
    ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(_Guid), ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(_Guid), ctypes.POINTER(ctypes.c_void_p),
    ]
    ole32.CoCreateInstance.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.restype = None
    ole32.CoUninitialize.argtypes = []
    ole32.CoUninitialize.restype = None
    initialized = False
    enumerator = ctypes.c_void_p()
    collection = ctypes.c_void_p()
    try:
        result = ole32.CoInitializeEx(None, 0) & 0xFFFFFFFF
        if result in (0, 1):
            initialized = True
        elif result != _RPC_E_CHANGED_MODE:
            return None
        result = ole32.CoCreateInstance(
            ctypes.byref(_CLSID_ENUMERATOR), None, 1,
            ctypes.byref(_IID_ENUMERATOR), ctypes.byref(enumerator),
        ) & 0xFFFFFFFF
        if result != 0 or not enumerator.value:
            return None
        # EnumAudioEndpoints(eRender, DEVICE_STATE_ACTIVE, collection**).
        result = _method(enumerator, 3, ctypes.c_int, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p))(
            enumerator, 0, 1, ctypes.byref(collection),
        ) & 0xFFFFFFFF
        if result != 0 or not collection.value:
            return None
        count = wintypes.UINT()
        result = _method(collection, 3, ctypes.POINTER(wintypes.UINT))(
            collection, ctypes.byref(count),
        ) & 0xFFFFFFFF
        if result != 0:
            return None
        ids = set()
        for index in range(count.value):
            endpoint = ctypes.c_void_p()
            endpoint_id = ctypes.c_void_p()
            try:
                result = _method(collection, 4, wintypes.UINT, ctypes.POINTER(ctypes.c_void_p))(
                    collection, index, ctypes.byref(endpoint),
                ) & 0xFFFFFFFF
                if result != 0 or not endpoint.value:
                    return None
                result = _method(endpoint, 5, ctypes.POINTER(ctypes.c_void_p))(
                    endpoint, ctypes.byref(endpoint_id),
                ) & 0xFFFFFFFF
                if result != 0 or not endpoint_id.value:
                    return None
                ids.add(ctypes.wstring_at(endpoint_id.value))
            finally:
                if endpoint_id.value:
                    ole32.CoTaskMemFree(endpoint_id)
                _release(endpoint)
        return frozenset(ids)
    finally:
        _release(collection)
        _release(enumerator)
        if initialized:
            ole32.CoUninitialize()
