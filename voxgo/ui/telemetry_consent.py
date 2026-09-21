"""Shared, concise opt-in dialog for settings and first-run setup."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QDialogButtonBox
from voxgo.analytics.consent import telemetry_title, telemetry_summary


def confirm_telemetry(parent, english=False):
    box = QMessageBox(QMessageBox.Question, telemetry_title(english),
                      telemetry_summary(english, confirmation=True),
                      QMessageBox.Yes | QMessageBox.No, parent)
    box.button(QMessageBox.Yes).setText('Happy to help' if english else '愿意帮助')
    box.button(QMessageBox.No).setText('Cancel' if english else '取消')
    # Reverse Windows' standard Yes/No order: Cancel on the left, Help on the right.
    box.findChild(QDialogButtonBox).setLayoutDirection(Qt.RightToLeft)
    for button in box.buttons():
        button.setLayoutDirection(Qt.LeftToRight)
    box.setDefaultButton(QMessageBox.Yes)
    box.button(QMessageBox.Yes).setFocus()
    box.setEscapeButton(QMessageBox.No)
    return box.exec_()
