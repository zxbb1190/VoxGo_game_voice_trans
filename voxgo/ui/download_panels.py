"""Background model preparation and application update controls."""

import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QLabel, QProgressBar

from voxgo.i18n import ui_text


class DownloadSignals(QObject):
    progress = pyqtSignal(object, object)
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)


class BackgroundPanel(QWidget):
    def __init__(self, language, parent=None):
        super().__init__(parent)
        self.language = language
        self.busy = False
        self._started_at = 0.0
        self.signals = DownloadSignals()
        self.signals.progress.connect(self._progress)
        self.signals.failed.connect(self._failed)
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(0, 0, 0, 0)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.bar = QProgressBar()
        self.bar.hide()
        self.button = QPushButton()
        self.layout_box.addWidget(self.status)
        self.layout_box.addWidget(self.bar)
        self.layout_box.addWidget(self.button)

    def tr_text(self, zh, en):
        return ui_text(self.language, zh, en)

    def _start(self, job):
        if self.busy:
            return
        self.busy = True
        self._started_at = time.monotonic()
        self.button.setEnabled(False)
        self.bar.setRange(0, 0)
        self.bar.show()
        signals = self.signals

        def run():
            try:
                result = job(signals.progress.emit)
            except Exception as exc:
                signals.failed.emit(str(exc))
            else:
                signals.finished.emit(result)

        threading.Thread(target=run, name="voxgo-download", daemon=True).start()

    def _progress(self, done, total):
        if total:
            self.bar.setRange(0, 100)
            self.bar.setValue(min(100, int(done * 100 / total)))
            elapsed = max(0.001, time.monotonic() - self._started_at)
            speed = done / elapsed
            eta = (total - done) / speed if speed else 0
            rate = f"{speed/1024/1024:.1f} MB/s" if speed >= 1048576 else f"{speed/1024:.0f} KB/s"
            self.status.setText(self.tr_text(
                f"下载中：{done/total:.0%} · {rate} · 已用 {elapsed:.0f}s · 剩余约 {eta:.0f}s",
                f"Downloading: {done/total:.0%} · {rate} · elapsed {elapsed:.0f}s · about {eta:.0f}s left",
            ))

    def _failed(self, message):
        self.busy = False
        self.bar.hide()
        self.button.setEnabled(True)
        lowered = message.lower()
        network = any(word in lowered for word in ("timed out", "timeout", "urlopen error", "308", "connection"))
        if network:
            prefix = self.tr_text("下载超时或网络连接失败，请切换下载源后重试：", "Download timed out or the connection failed. Switch the download source and retry: ")
        else:
            prefix = self.tr_text("下载失败，请切换下载源后重试：", "Download failed. Switch the download source and retry: ")
        self.status.setText(prefix + message[:500])


class LocalModelPanel(BackgroundPanel):
    def __init__(self, config, language, parent=None):
        super().__init__(language, parent)
        from voxgo.translation.local_models import LOCAL_MODELS

        self.config = config
        self.source_combo = QComboBox()
        self.source_combo.addItem(self.tr_text("ModelScope 国内源（推荐）", "ModelScope China (Recommended)"), "modelscope")
        self.source_combo.addItem(self.tr_text("HF-Mirror.net 国内源", "HF-Mirror.net China"), "hf_mirror_net")
        self.source_combo.addItem(self.tr_text("国内镜像（HF-Mirror）", "China mirror (HF-Mirror)"), "hf_mirror")
        self.source_combo.addItem("Hugging Face", "huggingface")
        self.source_combo.setCurrentIndex(max(0, self.source_combo.findData(getattr(config, "local_download_source", "modelscope"))))
        self.source_combo.currentIndexChanged.connect(lambda: setattr(self.config, "local_download_source", self.source_combo.currentData()))
        self.layout_box.insertWidget(0, self.source_combo)
        self.models = QComboBox()
        for key in LOCAL_MODELS:
            self.models.addItem("OPUS-MT · English ↔ 中文 · CPU", key)
        index = self.models.findData(getattr(config, "local_model", "opus-mt-en-zh"))
        self.models.setCurrentIndex(max(0, index))
        self.layout_box.insertWidget(0, self.models)
        self.models.currentIndexChanged.connect(self._selection_changed)
        self.button.clicked.connect(self._download)
        self.signals.finished.connect(self._ready)
        self.refresh_language(language)

    def _selection_changed(self):
        self.config.local_model = self.models.currentData()
        self.refresh_language(self.language)

    def refresh_language(self, language):
        from voxgo.translation.local_models import model_files_present

        self.language = language
        self.button.setText(self.tr_text("下载离线翻译模型", "Download Offline Translation Model"))
        if not self.busy:
            ready = model_files_present(self.models.currentData())
            self.button.setEnabled(True)
            if ready:
                self.button.setText(self.tr_text("校验 / 修复模型", "Verify / Repair Model"))
            self.status.setText(self.tr_text(
                "模型已就绪，可断网翻译，无需 API Key。" if ready else "首次需联网下载约 317 MB。准备完成后，中英双向翻译无需联网或 API Key。",
                "Model ready. Translate offline without an API key." if ready else "One-time download: about 317 MB. Then translate English ↔ Chinese offline without an API key.",
            ))

    def _download(self):
        from voxgo.translation.local_models import download_model

        model = self.models.currentData()
        source = self.source_combo.currentData()
        self.source_combo.setEnabled(False)
        self.models.setEnabled(False)
        self.status.setText(self.tr_text(
            "正在后台准备模型；可以继续使用浮窗、快捷键和在线翻译，关闭此窗口也不会停止下载。",
            "Preparing the model in the background. You can keep using the overlay, hotkeys, and online translation; closing this window will not stop the download.",
        ))
        self._start(lambda progress: download_model(model, progress=progress, source=source))

    def _ready(self, result):
        self.busy = False
        self.models.setEnabled(True)
        self.source_combo.setEnabled(True)
        self.bar.hide()
        self.refresh_language(self.language)

    def _failed(self, message):
        super()._failed(message)
        self.models.setEnabled(True)
        self.source_combo.setEnabled(True)


class UpdateInstallPanel(BackgroundPanel):
    def __init__(self, update, language, on_shutdown, parent=None):
        super().__init__(language, parent)
        from voxgo.update.installer import auto_update_supported

        self.update = update
        self.on_shutdown = on_shutdown
        self.prepared = None
        self.installing = False
        self.button.setText(self.tr_text("下载更新", "Download Update"))
        supported = auto_update_supported() and callable(on_shutdown)
        self.button.setEnabled(supported)
        self.status.setText(self.tr_text(
            "下载完成后点击安装并重启，保留配置和模型。" if supported else "源码运行不支持自动安装，请通过下载页获取新版。",
            "After downloading, click Install and Restart. Settings and models are preserved." if supported else "Automatic installation is unavailable in source mode. Use the download page.",
        ))
        self.button.clicked.connect(self._action)
        self.signals.finished.connect(self._finished)

    def discard(self):
        if not self.busy and not self.installing and self.prepared is not None:
            self.prepared.cleanup()
            self.prepared = None

    def _action(self):
        from voxgo.update.installer import prepare_update, launch_update

        if self.prepared is None:
            self.status.setText(self.tr_text("正在下载并校验更新…", "Downloading and verifying the update…"))
            self._start(lambda progress: prepare_update(self.update, progress=progress))
        else:
            self.installing = True
            self.status.setText(self.tr_text("正在准备安装，程序即将退出并重启…", "Preparing installation. VoxGo will close and restart…"))
            self._start(lambda progress: launch_update(self.prepared))

    def _finished(self, result):
        self.busy = False
        self.bar.hide()
        if self.installing:
            self.on_shutdown()
        else:
            self.prepared = result
            self.status.setText(self.tr_text("更新已校验，点击下方按钮安装。", "Update verified. Click below to install."))
            self.button.setText(self.tr_text("安装并重启", "Install and Restart"))
            self.button.setEnabled(True)

    def _failed(self, message):
        self.installing = False
        super()._failed(message)
