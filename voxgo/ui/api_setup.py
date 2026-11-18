"""Explicit opt-in to leaving the setup wizard without API configuration."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from voxgo.i18n import ui_text
from voxgo.translation.base import endpoint_requires_api_key, is_placeholder_api_key


def missing_api_field(config):
    if config.provider == "local":
        return None
    if config.provider != "google":
        if not config.endpoint.strip():
            return "endpoint"
        if not config.model.strip():
            return "model"
        try:
            needs_key = endpoint_requires_api_key(config.endpoint)
        except ValueError:
            return "endpoint"
    else:
        needs_key = True
    if needs_key and is_placeholder_api_key(config.api_key):
        return "api_key"
    return None


class ApiConfigurationRequiredDialog(QDialog):
    SKIP = 1
    CONFIGURE = 2

    def __init__(self, language, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle(ui_text(language, "API 尚未配置完整", "API setup is incomplete"))
        layout = QVBoxLayout(self)
        self.message = QLabel(ui_text(language,
            "翻译 API 尚未配置完整。选择“配置 API”可返回填写；选择“继续跳过”可进入下一步，之后请在设置中完成 API 配置。",
            "Translation API setup is incomplete. Choose Configure API to finish entering the settings, or Skip and continue to complete API setup later in Settings."))
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.skip_button = QPushButton(ui_text(language, "继续跳过", "Skip and continue"))
        self.skip_button.setAutoDefault(False)
        self.configure_button = QPushButton(ui_text(language, "配置 API", "Configure API"))
        self.configure_button.setDefault(True)
        self.skip_button.clicked.connect(lambda: self.done(self.SKIP))
        self.configure_button.clicked.connect(lambda: self.done(self.CONFIGURE))
        buttons.addWidget(self.skip_button)
        buttons.addWidget(self.configure_button)
        layout.addLayout(buttons)
        self.resize(440, self.sizeHint().height())
        self.configure_button.setFocus()
