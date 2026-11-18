"""In-app explanations for manual, evidence-driven subtitle diagnostics."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget

from voxgo.i18n import ui_text


HELP_SECTIONS = (
    ("如何使用", "How to use",
     "检测使用当前配置。请在目标应用播放指定原文语言的清晰语音，再停顿。✓ 表示已观察到通过，! 表示已发现问题，○ 表示仍在等待；没有语音不代表故障。检测不会自动修改设置，在线翻译仍按当前配置发送识别文字。",
     "Diagnostics use your current configuration. Play clear speech in the selected source language in the target app, then pause. A check mark means observed success, ! means a detected issue, and a circle means waiting. Silence is not proof of failure. Settings are not changed automatically; online translation sends recognized text as configured."),
    ("模型", "Models",
     "下载或加载时请等待；失败时检查网络、下载源和磁盘空间，并重试加载。本地翻译还需要离线翻译模型，在设置 → 翻译中下载或修复。语音识别模型就绪不等于翻译模型也就绪。",
     "Wait during download or loading. On failure, check the network, download source and disk space, then retry. Local translation also needs its offline translation model: download or repair it under Settings → Translation. A ready speech model does not mean the translation model is ready."),
    ("收音", "Audio capture",
     "音量条没有变化时，检查静音、音量、播放设备及设置 → 语音中的音源。只翻译指定应用时，要在该应用内播放；应用退出后需要重新选择。收到声音只证明有音频，不保证其中含有可识别的语音。",
     "If the level meter stays still, check mute, volume, the playback device and the source under Settings → Speech. In app-only mode, play speech in that app and reselect it after it exits. Audio activity does not prove that recognizable speech is present."),
    ("语音识别", "Speech recognition",
     "有声音但没有原文时，检查原文语言，播放清晰对话，适当提高低音量，减少音乐和噪声。暂停翻译时先继续。等待识别本身不能证明识别模型损坏。",
     "If audio arrives without a transcript, check the source language, play clear dialogue, raise low volume and reduce music or noise. Resume translation if paused. Waiting for recognition alone does not prove model damage."),
    ("翻译", "Translation",
     "有原文但没有译文时，查看检测中的实际错误，并在设置 → 翻译测试服务。常见排查方向包括 API Key、权限、额度、限流、网络和服务地址；这些是排查建议，具体原因以接口返回为准。本地翻译需确认模型及语言方向可用。",
     "If a transcript has no translation, inspect the actual error and test the service under Settings → Translation. Check API keys, permissions, quota, rate limits, network and endpoint. These are troubleshooting suggestions; the service response determines the cause. For local translation, check the model and supported language direction."),
    ("字幕显示", "Subtitle display",
     "译文已返回但看不见字幕时，检查浮窗是否隐藏或移出屏幕、颜色和透明度。电影字幕淡出后请再播放一句。独占全屏可能遮住浮窗，可尝试无边框窗口。程序记录到绘制不保证游戏上方真的可见，最后请亲眼确认。",
     "If translation arrives but subtitles are invisible, check whether the overlay is hidden or off-screen, plus colors and opacity. Play another phrase after cinema subtitles fade. Try borderless mode if exclusive fullscreen hides the overlay. A render event does not guarantee visibility over the game; confirm it yourself."),
)


class DetectionHelpDialog(QDialog):
    def __init__(self, language, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle(ui_text(language, "自动检测帮助", "Diagnostics help"))
        self.resize(650, 540)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        body = QVBoxLayout(content)
        for zh_title, en_title, zh_text, en_text in HELP_SECTIONS:
            title = QLabel(ui_text(language, zh_title, en_title))
            font = title.font()
            font.setBold(True)
            title.setFont(font)
            text = QLabel(ui_text(language, zh_text, en_text))
            text.setTextFormat(Qt.PlainText)
            text.setWordWrap(True)
            text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            body.addWidget(title)
            body.addWidget(text)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        close = QPushButton(ui_text(language, "关闭", "Close"))
        close.clicked.connect(self.close)
        layout.addWidget(close)
