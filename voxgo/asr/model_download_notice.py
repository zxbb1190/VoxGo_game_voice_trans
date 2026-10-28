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
    def __init__(self, config_getter):
        self._config_getter = config_getter
        self.last_download_bytes = (0, 0, 0.0)

    def record_progress(self, progress: ModelDownloadProgress):
        if progress.downloaded_bytes or progress.total_bytes:
            self.last_download_bytes = (
                progress.downloaded_bytes,
                progress.total_bytes,
                progress.percent,
            )

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
            return header + "\n" + ui_text(language, "正在检查本地缓存", "Checking the local cache")
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
        return header + "\n" + ui_text(language, "已下载: {0}", "Downloaded: {0}").format(progress_line)
