"""Presentation-only transitions and geometry for the two overlay modes."""
import time

from PyQt5.QtCore import Qt, QEvent, QPoint, QRect, QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication

from voxgo.config.models import normalize_overlay_display
from voxgo.ui.config_models import _tr


class OverlayPresentation:
    CINEMA_HOVER_HIDE_DELAY = 0.7

    def _init_cinema_hover(self):
        self._cinema_hover_left_at = None
        self._cinema_hover_origin = QRect()
        self._cinema_hover_timer = QTimer(self)
        self._cinema_hover_timer.setInterval(75)
        self._cinema_hover_timer.timeout.connect(self._poll_cinema_hover)

    def _stop_cinema_hover(self):
        self._cinema_hover_timer.stop()
        self._cinema_hovered = False
        self._cinema_hover_left_at = None
        self._cinema_hover_origin = QRect()

    def is_cinema(self):
        return self._active_display_mode == 'cinema'

    def cinema_controls_visible(self):
        return self.is_cinema() and self._cinema_hovered and not self._is_locked()

    def toggle_display_mode(self):
        self.set_display_mode('classic' if self.is_cinema() else 'cinema')

    def set_display_mode(self, mode):
        if mode not in ('classic', 'cinema') or mode == self._active_display_mode:
            return
        self._remember_window_geometry()
        self.config.display_mode = mode
        self._activate_display_mode()
        self._sync_presentation_dialog()
        self.presentation_changed.emit()

    def _activate_display_mode(self):
        self._initializing_geometry = True
        self._active_display_mode = self.config.display_mode
        self._stop_cinema_hover()
        self._cinema_view.config = self.config
        if not hasattr(self, '_classic_status_styles'):
            self._classic_status_styles = {widget: widget.styleSheet() for widget in
                                          (self._source_status, self._model_preparation_status)}
        for widget, style in self._classic_status_styles.items():
            widget.setStyleSheet(style + ('background: rgba(16, 22, 18, 210); padding: 3px;' if self.is_cinema() else ''))
        self._scroll_area.setVisible(not self.is_cinema())
        self._cinema_view.setVisible(self.is_cinema())
        self.setMaximumSize(2400 if self.is_cinema() else 980, 2160 if self.is_cinema() else 520)
        self.setWindowOpacity(1.0 if self.is_cinema() else self.config.opacity)
        self._refresh_compact_mode()
        self._restore_window_geometry()
        self._initializing_geometry = False
        self._refresh_labels()
        self._refresh_display_controls()
        self._remember_window_geometry()
        if self.is_cinema() and self.isVisible():
            self._cinema_hover_timer.start()
        self.update()

    def _sync_presentation_dialog(self):
        if self._settings_dialog:
            self._settings_dialog.sync_overlay_presentation(self.config)

    def _apply_presentation_settings(self, config):
        self._remember_window_geometry()
        for name in ('window_x', 'window_y', 'window_width', 'window_height',
                     'cinema_x', 'cinema_bottom', 'cinema_width', 'locked', 'draggable'):
            setattr(config, name, getattr(self.config, name))
        normalize_overlay_display(config)
        changed_mode = config.display_mode != self._active_display_mode
        self.config = config
        self._cinema_view.config = config
        self._apply_styles()
        self._refresh_appearance_icons()
        if changed_mode:
            self._activate_display_mode()
        else:
            self.setWindowOpacity(1.0 if self.is_cinema() else config.opacity)
            self._refresh_compact_mode()
            self._refresh_labels()
        self._refresh_lock_state()
        self.update()
        self.presentation_changed.emit()

    def _restore_cinema_geometry(self):
        area = QApplication.primaryScreen().availableGeometry()
        x, bottom = self.config.cinema_x, self.config.cinema_bottom
        if x is not None and bottom is not None:
            for screen in QApplication.screens():
                if screen.availableGeometry().contains(QPoint(x + 40, bottom - 20)):
                    area = screen.availableGeometry()
                    break
        width = min(self.config.cinema_width, area.width() - 24)
        self.resize(max(240, width), 120)
        self._cinema_view.rebuild(max(80, self.width() - 20), self._cinema_height_limit())
        self._layout.activate()
        height = min(area.height() - 24, max(80, self._layout.sizeHint().height()))
        self.resize(self.width(), height)
        if x is None or bottom is None or not self._geometry_reasonably_visible(QRect(x, bottom - height, width, height)):
            x = area.left() + (area.width() - self.width()) // 2
            bottom = area.bottom() + 1 - max(32, int(area.height() * 0.08))
        x = max(area.left(), min(x, area.right() + 1 - self.width()))
        y = max(area.top(), min(bottom - height, area.bottom() + 1 - height))
        self.move(x, y)

    def _fit_cinema_height(self):
        self._cinema_fit_pending = False
        if not self.is_cinema() or self._initializing_geometry:
            return
        self._cinema_view.rebuild(max(80, self.width() - 20), self._cinema_height_limit())
        self._layout.activate()
        screen = self.screen() or QApplication.primaryScreen()
        area = screen.availableGeometry()
        height = min(area.height() - 24, max(80, self._layout.sizeHint().height()))
        if self.cinema_controls_visible():
            # Expiring/shorter cues must not move the toolbar away from the pointer.
            height = min(area.height() - 24, max(height, self.height()))
        if height != self.height():
            bottom = self.y() + self.height()
            self._initializing_geometry = True
            self.resize(self.width(), height)
            self.move(self.x(), max(area.top(), min(bottom - height, area.bottom() + 1 - height)))
            self._initializing_geometry = False
            self._remember_window_geometry()

    def _cinema_height_limit(self):
        screen = self.screen() or QApplication.primaryScreen()
        return max(140, int(screen.availableGeometry().height() * .55))

    def _refresh_display_controls(self):
        if not hasattr(self, '_cinema_view'):
            return
        cinema = self.is_cinema()
        controls = self.cinema_controls_visible()
        self._toolbar.setVisible(not cinema or controls)
        self._source_status.setVisible(not cinema)
        self._compact_button.setVisible(not cinema)
        if cinema:
            self._language_notice.hide()
            self._beta_notice.hide()
        else:
            self._refresh_language_notice()
        notice = _tr(self._ui_language(), '翻译已暂停', 'Translation paused') if self._paused else self._cinema_problem
        self._cinema_notice.setText(notice)
        self._cinema_notice.setVisible(cinema and bool(self._cinema_notice.text()))
        if cinema:
            self._fit_cinema_height()
        self._position_lock_button()
        self._sync_cinema_mouse_passthrough()
        self._refresh_display_mode_button()
        self.update()

    def set_source_status(self, text, attention=False):
        self._source_status.setText(text)
        if self._source_attention != bool(attention):
            self._source_attention = bool(attention)
            self._refresh_display_controls()

    def enterEvent(self, event):
        self._poll_cinema_hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._poll_cinema_hover()
        super().leaveEvent(event)

    def _cinema_pointer_inside(self, point):
        if not self._cinema_hovered:
            local_point = self._cinema_view.mapFromGlobal(point)
            return any(rect.contains(local_point) for rect in self._cinema_view.visible_text_rects())
        # Global geometry also works for child widgets and mouse-transparent HWNDs.
        regions = [self.frameGeometry()]
        if self._cinema_hovered:
            regions.append(self._cinema_hover_origin)
        for widget in (self._lock_button, self._qr_popup):
            if widget.isVisible():
                regions.append(widget.frameGeometry())
        popup = QApplication.activePopupWidget()
        # isAncestorOf stops at popup window boundaries; follow the owner chain.
        while popup is not None:
            if popup is self:
                return True
            popup = popup.parentWidget()
        return any(not rect.isEmpty() and rect.adjusted(-8, -8, 8, 8).contains(point) for rect in regions)

    def _poll_cinema_hover(self):
        if not self.is_cinema() or not self.isVisible() or not hasattr(self, '_lock_button'):
            return
        inside = self._cinema_pointer_inside(QCursor.pos()) or self._dragging or self._resizing or self._lock_button.isDown()
        if inside:
            self._cinema_hover_left_at = None
            if not self._cinema_hovered:
                self._cinema_hover_origin = self.frameGeometry()
                self._cinema_hovered = True
                self._refresh_display_controls()
        elif self._cinema_hovered:
            now = time.monotonic()
            if self._cinema_hover_left_at is None:
                self._cinema_hover_left_at = now
            elif now - self._cinema_hover_left_at >= self.CINEMA_HOVER_HIDE_DELAY:
                self._cinema_hovered = False
                self._cinema_hover_origin = QRect()
                self._cinema_hover_left_at = None
                self._refresh_display_controls()

    def _sync_cinema_mouse_passthrough(self):
        enabled = self._is_locked() or (self.is_cinema() and not self._cinema_hovered)
        if self.testAttribute(Qt.WA_TransparentForMouseEvents) != enabled:
            self._set_overlay_mouse_passthrough(enabled)

    def event(self, event):
        if (event.type() == QEvent.LayoutRequest and getattr(self, '_active_display_mode', '') == 'cinema'
                and not getattr(self, '_cinema_fit_pending', False)):
            self._cinema_fit_pending = True
            QTimer.singleShot(0, self._fit_cinema_height)
        return super().event(event)
