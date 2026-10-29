"""A model status label independent of subtitle history; updated on the Qt thread."""
import time

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel

from voxgo.asr.model_download_notice import ModelDownloadNoticeFormatter


class ModelPreparationStatus(QLabel):
    def __init__(self, config_getter, parent=None, clock=time.monotonic):
        super().__init__(parent)
        self._formatter = ModelDownloadNoticeFormatter(config_getter, clock)
        self._clock = clock
        self._progress = None
        self._awaiting_model = None
        self._stopped = False
        self._last_render_at = 0.0
        self.setObjectName("modelPreparationStatus")
        self.setTextFormat(Qt.PlainText)
        self.setWordWrap(True)
        self.setStyleSheet("color: #EAB86A; font-size: 11px;")
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(500)
        self._refresh_timer.timeout.connect(self.refresh)
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.hide)
        self.hide()

    def set_progress(self, progress):
        if self._stopped:
            return
        # A repeated settings notification must not obscure a download in flight.
        if (progress.status == 'pending' and self._progress is not None
                and self._progress.model_name == progress.model_name
                and self._progress.status in {'checking', 'downloading', 'complete', 'loading'}):
            return
        if progress.status == 'pending':
            self._awaiting_model = progress.model_name
        elif self._awaiting_model is not None:
            # An old inference/download may finish after the user switches again.
            # It must not announce readiness for the newly selected model.
            if progress.model_name != self._awaiting_model:
                return
            self._awaiting_model = None
        changed_status = self._progress is None or self._progress.status != progress.status
        self._formatter.record_progress(progress)
        self._progress = progress
        self._dismiss_timer.stop()
        self.show()
        if changed_status or progress.status != 'downloading' or self._clock() - self._last_render_at >= 0.5:
            self.refresh()
        if progress.status in {'ready', 'error'}:
            self._refresh_timer.stop()
            if progress.status == 'ready':
                self._dismiss_timer.start(6000)
        else:
            self._refresh_timer.start()

    def refresh(self):
        if self._progress is not None:
            self.setText(self._formatter.format_compact(self._progress))
            self.setToolTip(self._formatter.format(self._progress))
            self._last_render_at = self._clock()

    def stop(self):
        self._stopped = True
        self._refresh_timer.stop()
        self._dismiss_timer.stop()
