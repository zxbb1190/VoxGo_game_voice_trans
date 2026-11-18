"""Classify observed stages without treating absent speech as a proven failure."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DiagnosticIssue:
    code: str
    stage: int | None
    confirmed: bool
    zh: str
    en: str
    detail: str = ""


def collect_diagnostics(check, *, setup_complete, paused, model_state, capture_available,
                        audio_error, overlay_visible):
    issues = []

    def add(code, stage, confirmed, zh, en, detail=""):
        issues.append(DiagnosticIssue(code, stage, confirmed, zh, en, str(detail)[:500]))

    if not setup_complete:
        add("setup", None, True, "首次设置尚未完成，请点击“完成首次设置”配置翻译和音源。",
            "Initial setup is incomplete. Select Complete setup to configure translation and audio.")
    if paused:
        add("paused", None, True, "翻译已暂停。点击“继续翻译”再播放语音。",
            "Translation is paused. Resume it and play speech.")
    if model_state == "error":
        add("model_error", 0, True, "模型准备失败，请打开设置检查下载源并重试加载。",
            "Model preparation failed. Open settings to check the download source and retry loading.")
    elif model_state == "missing_translation":
        add("local_model_missing", 0, True, "本地翻译模型尚未就绪，请打开设置下载或修复模型。",
            "The local translation model is not ready. Open settings to download or repair it.")
    elif model_state != "ready":
        add("model_waiting", 0, False, "等待模型下载或加载；若浮窗提示失败，检查下载源、磁盘空间并重试加载。",
            "Waiting for models. If loading failed, check the download source and disk space, then retry.")
    if audio_error and not capture_available:
        add("capture_error", 1, True, "收音未连接，请在设置中检查所选应用或播放设备，再重新检测。",
            "Audio capture is disconnected. Check the selected app or playback device in Settings, then retry.", audio_error)
    elif model_state == "ready" and not capture_available:
        add("capture_missing", 1, True, "收音未连接，请在设置中检查所选应用或播放设备，再重新检测。",
            "Audio capture is disconnected. Check the selected app or playback device in Settings, then retry.")
    elif model_state == "ready" and not paused:
        if not check.audio:
            add("audio_waiting", 1, False, "尚未收到声音：检查应用是否静音、音量和选中的音源。仅应用模式请在选中的应用内播放。",
                "No sound yet: check mute, volume and the selected source. In app mode, play audio inside that app.")
        elif not check.transcripts:
            add("speech_waiting", 2, False, "已收到声音，尚未识别出指定语言。播放清晰语音，核对原文语言；低音量可先调高应用音量。",
                "Sound is arriving, but no matching speech yet. Play clear speech, check the source language, and raise low app volume.")
    if check.error:
        add("translation_error", 3, True, "打开设置检查翻译服务、API Key、额度与网络，再重新检查。",
            "Check the translator, API key, quota and network in Settings, then check again.", check.error)
    elif check.transcripts and not check.translations:
        add("translation_waiting", 3, False, "语音已识别，等待翻译服务返回；长时间无结果可在设置测试翻译服务。",
            "Speech recognized; waiting for translation. If it takes too long, test the translator in Settings.")
    if not overlay_visible:
        add("overlay_hidden", 4, True, "字幕浮窗已隐藏，请先显示浮窗，再播放一句语音。",
            "The subtitle overlay is hidden. Show it, then play another phrase.")
    elif check.translations and not check.presented:
        add("display_waiting", 4, False, "翻译已返回，请显示浮窗；若字幕行已消失，再播放一句语音。",
            "Translation received. Show the overlay; play another phrase if its row has expired.")
    return issues
