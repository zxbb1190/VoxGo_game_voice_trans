"""Background model preparation and application update controls."""

import threading
import time

from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QDialog, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QLabel, QProgressBar

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


class LocalModelRequiredDialog(QDialog):
    SKIP = 1
    DOWNLOAD = 2

    def __init__(self, language, downloading=False, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle(ui_text(language, "本地翻译模型尚未准备好", "Local translation model is not ready"))
        layout = QVBoxLayout(self)
        self.message = QLabel(ui_text(
            language,
            "模型正在下载。继续跳过可进入下一步，但模型准备好前无法使用本地翻译。选择“下载模型”可返回查看下载进度。" if downloading else
            "本地翻译模型尚未下载完整。继续跳过可进入下一步，但模型准备好前无法使用本地翻译。选择“下载模型”会留在当前页面下载。",
            "The model is downloading. You can skip to the next step, but local translation will be unavailable until it is ready. Choose Download model to return to the download progress." if downloading else
            "The local translation model has not been fully downloaded. You can skip to the next step, but local translation will be unavailable until it is ready. Choose Download model to download it on this page.",
        ))
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.skip_button = QPushButton(ui_text(language, "继续跳过", "Skip and continue"))
        self.skip_button.setAutoDefault(False)
        self.download_button = QPushButton(ui_text(language, "下载模型", "Download model"))
        self.download_button.setDefault(True)
        self.skip_button.clicked.connect(lambda: self.done(self.SKIP))
        self.download_button.clicked.connect(lambda: self.done(self.DOWNLOAD))
        buttons.addWidget(self.skip_button)
        buttons.addWidget(self.download_button)
        layout.addLayout(buttons)
        self.resize(440, self.sizeHint().height())
        self.download_button.setFocus()


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
            self.models.addItem(self.tr_text("OPUS-MT · English ↔ 中文 · CPU", "OPUS-MT English ↔ Chinese (CPU)"), key)
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
        for index in range(self.models.count()):
            self.models.setItemText(index, self.tr_text("OPUS-MT · English ↔ 中文 · CPU", "OPUS-MT English ↔ Chinese (CPU)"))
        for index, (zh, en) in enumerate((
                ("ModelScope 国内源（推荐）", "ModelScope China (Recommended)"),
                ("HF-Mirror.net 国内源", "HF-Mirror.net China"),
                ("国内镜像（HF-Mirror）", "China mirror (HF-Mirror)"))):
            self.source_combo.setItemText(index, self.tr_text(zh, en))
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

    def confirm_before_continue(self):
        from voxgo.translation.local_models import model_files_present

        if model_files_present(self.models.currentData()):
            return True
        prompt = LocalModelRequiredDialog(self.language, self.busy, self)
        choice = prompt.exec_()
        prompt.deleteLater()
        if choice == LocalModelRequiredDialog.SKIP:
            return True
        if choice == LocalModelRequiredDialog.DOWNLOAD:
            # The existing worker may have finished while the prompt was open.
            if not model_files_present(self.models.currentData()):
                self._download()
        return False

    def _download(self):
        if self.busy:
            return
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
        from voxgo.update.installer import auto_update_supported, detect_edition

        self.update = update
        self.on_shutdown = on_shutdown
        self.prepared = None
        self.installing = False
        self.button.setText(self.tr_text("下载更新", "Download Update"))
        supported = auto_update_supported() and callable(on_shutdown)
        edition = detect_edition() if supported else None
        self.source_combo = QComboBox()
        self.source_combo.addItem("GitHub", "github")
        self.source_combo.addItem("", "gitcode")
        self.cancel_download = threading.Event()
        self.cancel_button = QPushButton()
        self.cancel_button.hide()
        self.cancel_button.clicked.connect(self._cancel_download)
        self.refresh_source_labels()
        self.source_combo.setVisible(edition == 'lite' and bool(update.verified_gitcode_lite_url()))
        self.layout_box.insertWidget(0, self.source_combo)
        self.layout_box.addWidget(self.cancel_button)
        self.button.setEnabled(supported and edition != 'unknown')
        self.status.setText(self.tr_text(
            "下载完成后点击安装并重启，保留配置和模型。" if supported else "源码运行不支持自动安装，请通过下载页获取新版。",
            "After downloading, click Install and Restart. Settings and models are preserved." if supported else "Automatic installation is unavailable in source mode. Use the download page.",
        ))
        if edition == 'unknown':
            self.status.setText(self.tr_text("无法识别当前安装包类型，请打开下载页手动更新。",
                                             "Cannot identify this edition. Open Downloads to update manually."))
        self.button.clicked.connect(self._action)
        self.signals.finished.connect(self._finished)

    def refresh_source_labels(self):
        self.source_combo.setAccessibleName(self.tr_text("下载来源", "Download source"))
        self.source_combo.setItemText(1, self.tr_text("国内镜像（GitCode）", "China mirror (GitCode)"))
        self.cancel_button.setText(self.tr_text("取消下载", "Cancel download"))

    def _cancel_download(self):
        self.cancel_download.set()
        self.cancel_button.setEnabled(False)

    def discard(self):
        if not self.busy and not self.installing and self.prepared is not None:
            self.prepared.cleanup()
            self.prepared = None

    def _action(self):
        from voxgo.update.installer import prepare_update, launch_update

        if self.prepared is None:
            source = self.source_combo.currentData()
            self.cancel_download.clear()
            self.cancel_button.setEnabled(True)
            self.cancel_button.setVisible(not self.source_combo.isHidden())
            self.source_combo.setEnabled(False)
            self.status.setText(self.tr_text("正在下载并校验更新…", "Downloading and verifying the update…"))
            self._start(lambda progress: prepare_update(self.update, progress=progress, source=source,
                                                        cancel=self.cancel_download))
        else:
            self.installing = True
            self.status.setText(self.tr_text("正在准备安装，程序即将退出并重启…", "Preparing installation. VoxGo will close and restart…"))
            self._start(lambda progress: launch_update(self.prepared))

    def _finished(self, result):
        if self.cancel_download.is_set() and not self.installing:
            result.cleanup()
            self._failed("")
            return
        self.busy = False
        self.cancel_button.hide()
        self.bar.hide()
        if self.installing:
            self.on_shutdown()
        else:
            self.prepared = result
            self.source_combo.hide()
            self.status.setText(self.tr_text("更新已校验，点击下方按钮安装。", "Update verified. Click below to install."))
            self.button.setText(self.tr_text("安装并重启", "Install and Restart"))
            self.button.setEnabled(True)

    def _failed(self, message):
        self.installing = False
        self.cancel_button.hide()
        self.source_combo.setEnabled(self.prepared is None)
        super()._failed(message)
        if self.cancel_download.is_set():
            self.status.setText(self.tr_text("下载已取消，可切换来源后重试。", "Download cancelled. Choose a source and retry."))
