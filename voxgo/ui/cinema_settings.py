"""Cinema appearance controls, kept separate from the classic preferences."""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QFormLayout, QSpinBox, QSlider, QCheckBox, QLabel, QHBoxLayout

from voxgo.ui.config_models import _tr
from voxgo.ui.widgets import ColorButton


class CinemaSettings(QWidget):
    changed = pyqtSignal()

    def __init__(self, config, language, parent=None):
        super().__init__(parent)
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        self.translation_size = QSpinBox()
        self.translation_size.setRange(18, 64)
        self.translation_size.setSuffix(' px')
        self.original_size = QSpinBox()
        self.original_size.setRange(10, 40)
        self.original_size.setSuffix(' px')
        self.translation_color = ColorButton(config.cinema_text_color, ui_language=language)
        self.original_color = ColorButton(config.cinema_original_text_color, ui_language=language)
        self.show_original = QCheckBox(_tr(language, '显示语音原文', 'Show original speech text'))
        self.background = QSlider(Qt.Horizontal)
        self.background.setRange(0, 80)
        self.background_value = QLabel()
        self.background.valueChanged.connect(lambda value: self.background_value.setText(f'{value}%'))
        background_row = QHBoxLayout()
        background_row.addWidget(self.background)
        background_row.addWidget(self.background_value)
        self.hint = QLabel(_tr(language,
            '字幕居中显示并自动淡出。鼠标移入显示控制栏；锁定后移入字幕可解锁，托盘也可解锁。背景设为 0 即为透明。',
            'Centered subtitles fade automatically. Hover for controls or the unlock button when locked. You can also unlock from the tray. Set background to 0 for transparency.'))
        self.hint.setWordWrap(True)
        for zh, en, widget in (
            ('译文字号', 'Translation font size', self.translation_size),
            ('原文字号', 'Original font size', self.original_size),
            ('译文颜色', 'Translation Color', self.translation_color),
            ('原文颜色', 'Original Color', self.original_color),
            ('双语对照', 'Bilingual Display', self.show_original),
        ):
            form.addRow(_tr(language, zh, en), widget)
        form.addRow(_tr(language, '黑色背景浓度', 'Black background opacity'), background_row)
        form.addRow(self.hint)
        self.sync(config)
        for widget in (self.translation_size, self.original_size, self.background):
            widget.valueChanged.connect(self.changed)
        self.show_original.toggled.connect(self.changed)
        self.translation_color.color_changed.connect(self.changed)
        self.original_color.color_changed.connect(self.changed)

    def sync(self, config):
        widgets = (self.translation_size, self.original_size, self.background, self.show_original)
        for widget in widgets:
            widget.blockSignals(True)
        self.translation_size.setValue(config.cinema_font_size)
        self.original_size.setValue(config.cinema_original_font_size)
        self.background.setValue(round(config.cinema_bg_opacity * 100))
        self.background_value.setText(f'{self.background.value()}%')
        self.show_original.setChecked(config.cinema_show_original)
        self.translation_color.set_color(config.cinema_text_color)
        self.original_color.set_color(config.cinema_original_text_color)
        for widget in widgets:
            widget.blockSignals(False)

    def collect(self, config):
        config.cinema_font_size = self.translation_size.value()
        config.cinema_original_font_size = self.original_size.value()
        config.cinema_bg_opacity = self.background.value() / 100
        config.cinema_show_original = self.show_original.isChecked()
        config.cinema_text_color = self.translation_color.color()
        config.cinema_original_text_color = self.original_color.color()
