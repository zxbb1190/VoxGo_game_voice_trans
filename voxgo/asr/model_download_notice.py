import time

from voxgo.i18n import ui_text, localize_text
from voxgo.asr.whisper_engine import ModelDownloadProgress, describe_model_download_source


def format_download_amount(downloaded: int, total: int, percent: float) -> str:
    if total:
        return f"{format_bytes(downloaded)} / {format_bytes(total)} ({percent:.1f}%)"
    if downloaded:
        return format_bytes(downloaded)
    return ""


def format_bytes(value: int) -> str:
    value = max(0, int(value or 0))
    units = ("B", "KB", "MB", "GB")
    amount = float(value)
    unit = units[0]
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            break
        amount /= 1024
    if unit == "B":
        return f"{int(amount)} {unit}"
    return f"{amount:.1f} {unit}"


class ModelDownloadNoticeFormatter:
    def __init__(self, config_getter, clock=time.monotonic):
        self._config_getter = config_getter
        self._clock = clock
        self.last_download_bytes = (0, 0, 0.0)
        self._identity = None
        self._status = ""
        self._started_at = None
        self._download_started_at = None
        self._download_baseline = 0
        self._last_byte_change_at = None
        self._finished_at = None
        self._progress_scope = "model"

    def record_progress(self, progress: ModelDownloadProgress):
        now = self._clock()
        identity = (progress.model_name, progress.repo_id)
        if (identity != self._identity or progress.status == "checking"
                or (self._status in {"ready", "error"} and progress.status in {"pending", "loading"})):
            self.last_download_bytes = (0, 0, 0.0)
            self._identity = identity
            self._started_at = now
            self._download_started_at = None
            self._last_byte_change_at = None
            self._finished_at = None
        if self._started_at is None:
            self._started_at = now
        if progress.status == "downloading":
            if self._download_started_at is None or progress.downloaded_bytes < self.last_download_bytes[0]:
                self._download_started_at = now
                # Cached bytes are not transfer speed for this download.
                self._download_baseline = progress.downloaded_bytes
                self._last_byte_change_at = None
            elif progress.downloaded_bytes > self.last_download_bytes[0]:
                self._last_byte_change_at = now
        if progress.downloaded_bytes or progress.total_bytes:
            self.last_download_bytes = (
                progress.downloaded_bytes,
                progress.total_bytes,
                progress.percent,
            )
        if progress.status in {"ready", "error"}:
            self._finished_at = now
        self._status = progress.status
        self._progress_scope = progress.progress_scope

    def _timing(self, language, downloading=False):
        now = self._finished_at if self._finished_at is not None else self._clock()
        elapsed = max(0, now - self._started_at) if self._started_at is not None else 0
        parts = [ui_text(language, "已用 {0}s", "Elapsed {0}s").format(int(elapsed))]
        if downloading:
            if self._progress_scope == "file":
                parts.append(ui_text(language, "总剩余时间暂无法估算", "Overall remaining time is not available yet"))
                return " · ".join(parts)
            downloaded, total, _ = self.last_download_bytes
            duration = now - self._download_started_at if self._download_started_at is not None else 0
            fresh = self._last_byte_change_at is not None and now - self._last_byte_change_at <= 3
            transferred = downloaded - self._download_baseline
            if duration >= 2 and transferred > 0 and fresh:
                speed = transferred / duration
                parts.append(format_bytes(int(speed)) + "/s")
                if total > downloaded:
                    remaining = max(1, round((total - downloaded) / speed))
                    parts.append(ui_text(language, "预计剩余约 {0}s", "About {0}s remaining").format(remaining))
            else:
                parts.append(ui_text(language, "正在估算剩余时间", "Estimating remaining time"))
        return " · ".join(parts)

    def format_compact(self, progress: ModelDownloadProgress) -> str:
        config = self._config_getter()
        language = getattr(getattr(config, 'app', None), 'language', 'zh-CN')
        model = progress.model_name or config.whisper.model_size
        titles = {
            "pending": ("正在切换识别模型：{0}", "Switching speech model: {0}"),
            "checking": ("正在检查识别模型：{0}", "Checking speech model: {0}"),
            "downloading": ("正在下载识别模型：{0}", "Downloading speech model: {0}"),
            "complete": ("模型缓存已就绪：{0}", "Model cache ready: {0}"),
            "loading": ("正在加载识别模型：{0}", "Loading speech model: {0}"),
            "ready": ("识别模型已就绪：{0}", "Speech model ready: {0}"),
            "error": ("识别模型准备失败：{0}", "Speech model preparation failed: {0}"),
        }
        title = ui_text(language, *titles.get(progress.status, titles['checking'])).format(model)
        if progress.status == "pending":
            detail = ui_text(language, "等待下一段语音检查并加载，首次使用可能需要下载。", "Waiting for the next audio segment to check and load; first use may require a download.")
        elif progress.status == "checking":
            detail = ui_text(language, "正在检查本地缓存", "Checking the local cache")
        elif progress.status == "downloading":
            detail = ui_text(language, "模型下载期间，语音识别暂不可用。", "Speech recognition is temporarily unavailable during the model download.")
            amount = format_download_amount(*self.last_download_bytes)
            if amount:
                template = (("当前文件已下载: {0}", "Current file downloaded: {0}")
                            if progress.progress_scope == 'file' else ("已下载: {0}", "Downloaded: {0}"))
                detail += "\n" + ui_text(language, *template).format(amount)
        elif progress.status in {"complete", "loading"}:
            detail = ui_text(language, "正在加载识别引擎，请稍候。", "Loading the recognition engine; please wait.")
        elif progress.status == "ready":
            detail = ui_text(language, "可以继续播放语音。", "You can continue playing audio.")
        else:
            detail = ui_text(language, "请检查网络、下载源或识别设备后重试。", "Check the network, download source or recognition device, then retry.")
        return title + "\n" + detail + "\n" + self._timing(language, progress.status == "downloading")

    def format(self, progress: ModelDownloadProgress) -> str:
        config = self._config_getter()
        model = progress.model_name or config.whisper.model_size
        repo = progress.repo_id or model
        source = progress.source or describe_model_download_source(
            getattr(config.whisper, "model_download_source", "modelscope"),
            getattr(config.whisper, "model_download_endpoint", ""),
        )
        language = getattr(getattr(config, 'app', None), 'language', 'zh-CN')
        source = localize_text(language, source)
        header = "\n".join((
            ui_text(language, "模型: {0}", "Model: {0}").format(model),
            ui_text(language, "仓库: {0}", "Repository: {0}").format(repo),
            ui_text(language, "来源: {0}", "Source: {0}").format(source),
        ))
        if progress.status == "checking":
            return header + "\n" + ui_text(language, "正在检查本地缓存", "Checking the local cache") + "\n" + self._timing(language)
        if progress.status in {"pending", "loading", "ready"}:
            return header + "\n" + self.format_compact(progress)
        downloaded, total, percent = self.last_download_bytes
        progress_line = format_download_amount(downloaded, total, percent)
        if progress.status == "complete":
            detail = localize_text(language, progress.message or "模型缓存已就绪")
            amount = ("\n" + ui_text(language, "已下载: {0}", "Downloaded: {0}").format(progress_line)) if progress_line else ""
            return header + amount + "\n" + ui_text(language, "{0}，正在加载识别引擎", "{0}; loading the recognition engine").format(detail)
        if progress.status == "error":
            suffix = ("\n" + ui_text(language, "已下载: {0}", "Downloaded: {0}").format(progress_line)) if progress_line else ""
            return localize_text(language, progress.message or "模型下载失败") + suffix
        progress_line = format_download_amount(progress.downloaded_bytes, progress.total_bytes, progress.percent)
        if not progress_line:
            progress_line = ui_text(language, "正在准备下载", "Preparing download")
        return header + "\n" + ui_text(language, "已下载: {0}", "Downloaded: {0}").format(progress_line) + "\n" + self._timing(language, True)
