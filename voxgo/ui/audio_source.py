"""Shared source selector for setup and settings."""
import ntpath

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel

from voxgo.audio.process_loopback import list_applications, support_error
from voxgo.i18n import ui_text, localize_text


class AudioSourceSelector(QWidget):
    changed = pyqtSignal()

    def __init__(self, config, language, parent=None):
        super().__init__(parent)
        self.config = config
        self.language = language
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.mode = QComboBox()
        self.mode.addItem(self.tr_text("系统声音 / 输入设备", "System audio / input device"), "system")
        self.mode.addItem(self.tr_text("只翻译指定应用", "Translate only one application"), "process")
        self.mode.setCurrentIndex(1 if getattr(config, "source_mode", "system") == "process" else 0)
        layout.addWidget(self.mode)
        row = QHBoxLayout()
        self.apps = QComboBox()
        self.apps.setMinimumContentsLength(18)
        self.apps.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.refresh_button = QPushButton(self.tr_text("刷新应用", "Refresh apps"))
        row.addWidget(self.apps, 1)
        row.addWidget(self.refresh_button)
        layout.addLayout(row)
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        self.refresh()
        self.mode.currentIndexChanged.connect(self._changed)
        self.apps.currentIndexChanged.connect(self._changed)
        self.refresh_button.clicked.connect(self._refresh_clicked)
        self._refresh_visibility()

    def tr_text(self, zh, en):
        return ui_text(self.language, zh, en)

    def set_language(self, language):
        self.language = language
        self.mode.setItemText(0, self.tr_text("系统声音 / 输入设备", "System audio / input device"))
        self.mode.setItemText(1, self.tr_text("只翻译指定应用", "Translate only one application"))
        self.refresh_button.setText(self.tr_text("刷新应用", "Refresh apps"))
        self.apps.setItemText(0, self.tr_text("请选择正在运行的应用", "Select a running application"))
        self._refresh_visibility()

    def refresh(self):
        previous = self.apps.currentData()
        path = previous.get("path", "") if previous else getattr(self.config, "process_path", "")
        pid = previous.get("pid", 0) if previous else getattr(self.config, "process_id", 0)
        self.apps.blockSignals(True)
        self.apps.clear()
        self.apps.addItem(self.tr_text("请选择正在运行的应用", "Select a running application"), None)
        try:
            choices = list_applications()
        except OSError:
            choices = []
        matches = []
        for item in choices:
            self.apps.addItem(f"{ntpath.basename(item['path'])} · {item['title'][:45]} (PID {item['pid']})", item)
            if item["path"].casefold() == path.casefold() and (not pid or item["pid"] == pid):
                matches.append(self.apps.count() - 1)
        if len(matches) == 1:
            self.apps.setCurrentIndex(matches[0])
        elif path:
            self.apps.addItem(self.tr_text("待启动或重新选择：", "Start or reselect: ") + ntpath.basename(path),
                              {"path": path, "pid": pid, "started": getattr(self.config, "process_started", 0)})
            self.apps.setCurrentIndex(self.apps.count() - 1)
        self.apps.blockSignals(False)

    def _refresh_clicked(self):
        self.refresh()
        self._changed()

    def _refresh_visibility(self):
        selected = self.mode.currentData() == "process"
        self.apps.setVisible(selected)
        self.refresh_button.setVisible(selected)
        self.hint.setVisible(selected)
        self.hint.setText(localize_text(self.language, support_error()) or self.tr_text(
            "包含该应用的子进程。退出后暂停收音，请重新选择；不会改录其他应用。",
            "Includes child processes. Capture pauses when the app exits; select it again. Other apps stay excluded."))
        self.apps.setEnabled(not support_error())

    def _changed(self):
        self._refresh_visibility()
        self.changed.emit()

    def collect(self):
        self.config.source_mode = self.mode.currentData()
        selected = self.apps.currentData() or {}
        self.config.process_path = selected.get("path", "")
        self.config.process_id = selected.get("pid", 0)
        self.config.process_started = selected.get("started", 0)
