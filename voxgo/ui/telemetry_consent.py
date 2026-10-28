"""Shared, concise opt-in dialog for settings and first-run setup."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QDialogButtonBox
from voxgo.analytics.consent import telemetry_title, telemetry_summary
from voxgo.i18n import ui_text


def confirm_telemetry(parent, english=False, ui_language=None):
    language = ui_language or ('en-US' if english else 'zh-CN')
    box = QMessageBox(QMessageBox.Question, ui_text(language, telemetry_title(False), telemetry_title(True)),
                      ui_text(language, telemetry_summary(False, confirmation=True), telemetry_summary(True, confirmation=True)),
                      QMessageBox.Yes | QMessageBox.No, parent)
    box.button(QMessageBox.Yes).setText(ui_text(language, '愿意帮助', 'Happy to help'))
    box.button(QMessageBox.No).setText(ui_text(language, '取消', 'Cancel'))
    # Reverse Windows' standard Yes/No order: Cancel on the left, Help on the right.
    box.findChild(QDialogButtonBox).setLayoutDirection(Qt.RightToLeft)
    for button in box.buttons():
        button.setLayoutDirection(Qt.LeftToRight)
    box.setDefaultButton(QMessageBox.Yes)
    box.button(QMessageBox.Yes).setFocus()
    box.setEscapeButton(QMessageBox.No)
    return box.exec_()
