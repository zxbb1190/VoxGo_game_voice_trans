"""Guide driven by normal capture/ASR/translation/render events, on the Qt thread."""
from collections import OrderedDict
from datetime import datetime, timezone
import ntpath
import time
import webbrowser

from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QScrollArea, QWidget

from voxgo.app_info import KOOK_URL, DISCORD_URL
from voxgo.i18n import ui_text, language_label, localize_text
from voxgo.runtime.first_success import LiveCheck
from voxgo.runtime.subtitle_diagnostics import collect_diagnostics
from voxgo.translation.local_models import model_files_present
from voxgo.ui.detection_help import DetectionHelpDialog


class CommunityInvitation(QWidget):
    def __init__(self, language, on_dismiss, parent=None):
        super().__init__(parent)
        self.setObjectName("communityInvitation")
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("""
            QWidget#communityInvitation { background: #2B333D; border-radius: 5px; }
            QLabel { color: #E0E8F2; font-size: 12px; }
            QPushButton { color: #E0E8F2; background: #364454; border: 1px solid #526276;
                          border-radius: 4px; padding: 3px 8px; }
            QPushButton:hover { background: #465970; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        label = QLabel(ui_text(language, "翻译成功了！欢迎交流游戏设置、排查问题、参与新版本测试。",
                              "Translation is working! Join us to discuss game settings, troubleshoot and try new versions."))
        label.setWordWrap(True)
        label.setTextFormat(Qt.PlainText)
        layout.addWidget(label)
        row = QHBoxLayout()
        links = [("KOOK", KOOK_URL), ("Discord", DISCORD_URL)]
        if not language.startswith("zh"):
            links.reverse()
        for name, url in links:
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, target=url: webbrowser.open(target))
            row.addWidget(button)
        self.dismiss_button = QPushButton(ui_text(language, "不再显示", "Do not show again"))
        self.dismiss_button.clicked.connect(on_dismiss)
        row.addWidget(self.dismiss_button)
        layout.addLayout(row)


class LiveCheckDialog(QDialog):
    def __init__(self, controller):
        super().__init__(controller.app._overlay)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.controller = controller
        self.help_dialog = None
        self.language = controller.app._ui_language()
        self.setWindowTitle(controller.tr_text("自动检测", "Automatic diagnostics"))
        self.setWindowModality(Qt.NonModal)
        self.resize(650, 560)
        layout = QVBoxLayout(self)
        self.instruction = QLabel()
        self.instruction.setWordWrap(True)
        self.instruction.setTextFormat(Qt.PlainText)
        layout.addWidget(self.instruction)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setFormat(controller.tr_text("收音音量 %p%", "Input level %p%"))
        layout.addWidget(self.level)
        self.rows = [QLabel() for _ in range(5)]
        for row in self.rows:
            layout.addWidget(row)
        self.hint = QLabel()
        self.hint.setTextFormat(Qt.PlainText)
        self.hint.setWordWrap(True)
        self.hint.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.hint.setTextInteractionFlags(Qt.TextSelectableByMouse)
        issues_scroll = QScrollArea()
        issues_scroll.setWidgetResizable(True)
        issues_scroll.setMinimumHeight(120)
        issues_scroll.setWidget(self.hint)
        layout.addWidget(issues_scroll, 1)
        self.result = QLabel()
        self.result.setTextFormat(Qt.PlainText)
        self.result.setWordWrap(True)
        layout.addWidget(self.result)
        row = QHBoxLayout()
        self.retry = QPushButton(controller.tr_text("重新检测", "Run diagnostics again"))
        self.retry.clicked.connect(controller.retry)
        self.settings = QPushButton(controller.tr_text("打开设置", "Open settings"))
        self.settings.clicked.connect(controller.app._overlay._open_settings)
        self.resume = QPushButton(controller.tr_text("继续翻译", "Resume translation"))
        self.resume.clicked.connect(controller.app._toggle_translation)
        row.addWidget(self.retry)
        row.addWidget(self.settings)
        row.addWidget(self.resume)
        self.help_button = QPushButton(controller.tr_text("帮助", "Help"))
        self.help_button.clicked.connect(self.show_help)
        row.addWidget(self.help_button)
        layout.addLayout(row)

        row = QHBoxLayout()
        self.model_retry = QPushButton(controller.tr_text("重试加载模型", "Retry loading models"))
        self.model_retry.clicked.connect(lambda: controller.app._request_model_recovery(False))
        self.seen = QPushButton(controller.tr_text("我已在浮窗看到字幕", "I can see the subtitles"))
        self.seen.clicked.connect(controller.confirm_visible)
        self.later = QPushButton(controller.tr_text("关闭", "Close"))
        self.later.clicked.connect(self.close)
        self.setup = QPushButton(controller.tr_text("完成首次设置", "Complete setup"))
        self.setup.clicked.connect(lambda: controller.app._overlay.show_first_run_wizard(controller.app._start_backend_after_setup))
        row.addWidget(self.model_retry)
        row.addWidget(self.setup)
        row.addWidget(self.seen)
        row.addWidget(self.later)
        layout.addLayout(row)

    def refresh_language(self):
        controller = self.controller
        self.language = controller.app._ui_language()
        self.setWindowTitle(controller.tr_text("自动检测", "Automatic diagnostics"))
        self.level.setFormat(controller.tr_text("收音音量 %p%", "Input level %p%"))
        for button, zh, en in (
            (self.retry, "重新检测", "Run diagnostics again"),
            (self.settings, "打开设置", "Open settings"),
            (self.resume, "继续翻译", "Resume translation"),
            (self.model_retry, "重试加载模型", "Retry loading models"),
            (self.seen, "我已在浮窗看到字幕", "I can see the subtitles"),
            (self.later, "关闭", "Close"),
            (self.help_button, "帮助", "Help"),
            (self.setup, "完成首次设置", "Complete setup"),
        ):
            button.setText(controller.tr_text(zh, en))
        if self.help_dialog:
            self.help_dialog.close()
            self.help_dialog.deleteLater()
            self.help_dialog = None

    def show_help(self):
        if self.help_dialog is None:
            self.help_dialog = DetectionHelpDialog(self.language, self)
        self.help_dialog.show()
        self.help_dialog.raise_()

    def done(self, result):
        if self.help_dialog:
            self.help_dialog.close()
        super().done(result)


class FirstSuccessController(QObject):
    # Workers publish immutable snapshots. All widgets and persisted settings are
    # touched only on the GUI thread, never from recognition/translation workers.
    transcript_received = pyqtSignal(str, int, float)
    translation_received = pyqtSignal(str, int, str, str)

    def __init__(self, app):
        super().__init__(app._overlay)
        self.app = app
        self.check = None
        self.dialog = None
        self.banner = None
        self.pending = OrderedDict()
        self.last_result = ""
        self.issues = []
        self._stopped = False
        self.transcript_received.connect(self._transcript, Qt.QueuedConnection)
        self.translation_received.connect(self._translation, Qt.QueuedConnection)
        app._overlay.subtitle_presented.connect(self._presented, Qt.QueuedConnection)
        app._overlay.live_check_requested.connect(self.show_check)
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.poll)
        self.timer.start()

    def tr_text(self, zh, en):
        return ui_text(self.app._ui_language(), zh, en)

    def show_check(self):
        if self._stopped:
            return
        if self.dialog is None:
            self.dialog = LiveCheckDialog(self)
            self.dialog.finished.connect(self._check_closed)
        if not self.dialog.isVisible():
            self.restart_check()
        self.dialog.show()
        self.poll()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def restart_check(self):
        self.check = LiveCheck(self.app._language_flow_revision)
        self.last_result = ""
        self.issues = []
        if self.dialog:
            self.dialog.result.clear()
        self.poll()

    def retry(self):
        self.restart_check()
        if self.app._backend_ready and self.app._audio.capture is None:
            self.app._restart_audio_capture()

    def _check_closed(self):
        self.check = None
        self.last_result = ""

    def _transcript(self, item_id, revision, detected_at):
        if self._stopped or revision != self.app._language_flow_revision:
            return
        self.pending[item_id] = {"revision": revision, "detected_at": detected_at, "ok": False}
        while len(self.pending) > 128:
            self.pending.popitem(last=False)
        if self.check:
            self.check.transcript(item_id, revision, detected_at)

    def _translation(self, item_id, revision, text, error):
        item = self.pending.get(item_id)
        if self._stopped or not item or revision != self.app._language_flow_revision or item["revision"] != revision:
            return
        item["ok"] = bool(text.strip()) and not error
        settings = self.app.config.app
        if item["ok"] and not self.app._paused and not settings.first_translation_at:
            settings.first_translation_at = datetime.now(timezone.utc).isoformat()
            self.app._save_user_settings()
        if self.check and self.check.translation(item_id, revision, error):
            self.last_result = text[:500]
        self.poll()

    def _presented(self, item_id):
        item = self.pending.get(item_id)
        if (self._stopped or not item or not item["ok"] or self.app._paused
                or item["revision"] != self.app._language_flow_revision):
            return
        if self.check:
            self.check.present(item_id)
        settings = self.app.config.app
        if not settings.first_subtitle_at:
            settings.first_subtitle_at = datetime.now(timezone.utc).isoformat()
            self.app._save_user_settings()
        self.poll()

    def confirm_visible(self):
        if not self.check or not self.check.complete:
            return
        self.app.config.app.subtitle_check_completed = True
        self.app._save_user_settings()
        self.dialog.accept()

    def _invite(self):
        overlay = self.app._overlay
        settings = self.app.config.app
        if (self._stopped or not (settings.first_translation_at or settings.first_subtitle_at) or settings.community_invitation_dismissed
                or not overlay.isVisible() or overlay.config.locked
                or (overlay.is_cinema() and not overlay.cinema_controls_visible())
                or (not overlay.is_cinema() and overlay.config.compact_mode)):
            return
        if self.banner is None:
            self.banner = CommunityInvitation(self.app._ui_language(), self.dismiss_invitation, overlay)
            overlay._layout.addWidget(self.banner)
        self.banner.show()
        if not settings.community_invitation_seen:
            settings.community_invitation_seen = True
            self.app._save_user_settings()

    def dismiss_invitation(self):
        if self.banner:
            self.banner.hide()
        self.app.config.app.community_invitation_seen = True
        self.app.config.app.community_invitation_dismissed = True
        self.app._save_user_settings()

    def _model_state(self):
        status = self.app._overlay._model_preparation_status.preparation_state
        if status == "error":
            return "error"
        if not self.app._backend_ready or status in {"pending", "checking", "downloading", "complete", "loading"}:
            return "preparing"
        config = self.app.config.translation
        if config.provider == "local" and not model_files_present(config.local_model):
            return "missing_translation"
        return "ready"

    def poll(self):
        if self._stopped or self.app._stopping:
            return
        overlay = self.app._overlay
        if self.banner and (self.app.config.app.community_invitation_dismissed or overlay.config.locked or
                (overlay.is_cinema() and not overlay.cinema_controls_visible()) or
                (not overlay.is_cinema() and overlay.config.compact_mode)):
            self.banner.hide()
        self._invite()
        audio = self.app._audio
        capture = audio.capture
        config = self.app.config.audio
        name = (capture.selected_device or {}).get("name", "") if capture else ""
        if config.source_mode == "process":
            source = self.tr_text("仅应用：", "App only: ") + (name or ntpath.basename(config.process_path))
            if not capture:
                source += self.tr_text(" · 已暂停，打开设置重新选择", " · Paused; reselect in settings")
        else:
            source = self.tr_text("音源：", "Source: ") + (name or self.tr_text("等待连接", "Waiting for connection"))
        self.app._overlay.set_source_status(source, attention=bool(not capture and (audio.last_error or config.source_mode == 'process')))
        if not self.dialog or not self.dialog.isVisible() or not self.check:
            return
        if self.dialog.language != self.app._ui_language():
            self.dialog.refresh_language()
        if self.check.revision != self.app._language_flow_revision:
            self.check = LiveCheck(self.app._language_flow_revision)
            self.last_result = ""
        check = self.check
        model_state = self._model_state()
        check.models = model_state == "ready"
        level = getattr(capture, "last_level_dbfs", -120.0)
        fresh = capture and time.monotonic() - getattr(capture, "last_level_at", 0) < 1
        if fresh and level > -70 and not self.app._paused:
            check.audio = True
        self.dialog.level.setValue(int(max(0, min(100, (level + 70) / 70 * 100))) if fresh else 0)
        names = [("模型就绪", "Models ready"), ("收到音频", "Audio received"), ("识别到语音", "Speech recognized"),
                 ("翻译返回", "Translation received"), ("字幕写入可见浮窗", "Subtitles rendered in visible overlay")]
        self.issues = collect_diagnostics(check, setup_complete=self.app.config.app.setup_completed,
            paused=self.app._paused, model_state=model_state, capture_available=capture is not None,
            audio_error=audio.last_error, overlay_visible=overlay.isVisible())
        for index, (label, passed, (zh, en)) in enumerate(zip(self.dialog.rows, check.stages, names)):
            problem = any(issue.confirmed and issue.stage == index for issue in self.issues)
            label.setText(("! " if problem else "✓ " if passed else "○ ") + self.tr_text(zh, en))
        language = language_label(self.app.config.translation.source_lang, self.app._ui_language())
        self.dialog.instruction.setText(self.tr_text(
            f"{source}\n请在目标应用播放一段{language}语音，然后停顿。检查使用你当前的翻译服务；在线服务会正常发送语音识别后的文字。",
            f"{source}\nPlay speech in {language} in the target app, then pause. This check uses your configured translator; online services receive recognized text as usual."))
        self.dialog.seen.setEnabled(check.complete)
        self.dialog.resume.setVisible(self.app._paused)
        self.dialog.model_retry.setVisible(model_state in {"error", "preparing"})
        self.dialog.setup.setVisible(not self.app.config.app.setup_completed)
        self.dialog.result.setText(self.last_result)
        hints = []
        for issue in self.issues:
            stage = self.tr_text(*names[issue.stage]) + ": " if issue.stage is not None else ""
            text = ("! " if issue.confirmed else "○ ") + stage + self.tr_text(issue.zh, issue.en)
            if issue.detail:
                text += "\n" + localize_text(self.app._ui_language(), issue.detail)
            hints.append(text)
        if not hints:
            hints.append(self.tr_text("链路已跑通。请确认游戏上方能看到字幕；独占全屏可切换无边框窗口。", "The pipeline works. Confirm subtitles are visible over the game; use borderless mode if exclusive fullscreen hides them."))
        self.dialog.hint.setText("\n\n".join(hints))

    def stop(self):
        self._stopped = True
        self.timer.stop()
        self.pending.clear()
        if self.dialog:
            self.dialog.close()
        if self.banner:
            self.banner.hide()
