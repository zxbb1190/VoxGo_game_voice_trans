"""Current-cue presentation, independent from capture, translation and history."""
from dataclasses import dataclass
import time

from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QTextLayout, QTextOption
from PyQt5.QtWidgets import QWidget


@dataclass
class CinemaCue:
    sequence: int
    item_id: str
    original: str
    translated: str
    expires_at: float
    started_at: float


class CinemaTimeline:
    """A monotonic high-water mark prevents late replies from rewinding speech."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.latest_sequence = -1
        self.cue = None

    def offer(self, sequence, item_id, original, translated):
        if not translated.strip() or sequence < self.latest_sequence:
            return False
        if (self.cue and sequence == self.cue.sequence and self.cue.translated == translated
                and self.cue.original == original):
            return False
        self.latest_sequence = sequence
        duration = min(8.0, max(4.0, len(translated) / 8.0))
        now = self.clock()
        self.cue = CinemaCue(sequence, item_id, original, translated, now + duration, now)
        return True

    @property
    def opacity(self):
        if self.cue is None:
            return 0.0
        return max(0.0, min(1.0, (self.cue.expires_at - self.clock()) / 0.35))

    def remove(self, item_id):
        if self.cue and self.cue.item_id == item_id:
            self.cue = None

    def clear(self):
        self.cue = None


class CinemaSubtitles(QWidget):
    frame_presented = pyqtSignal(str)

    def __init__(self, config, parent=None, clock=time.monotonic):
        super().__init__(parent)
        self.config = config
        self.timeline = CinemaTimeline(clock)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._lines = []
        self._layout_key = None
        self._last_presented = None
        self._pages = []
        self._seconds_per_page = 4.0
        self.setFixedHeight(64)

    def rebuild(self, width, max_height=500):
        cue = self.timeline.cue
        key = (width, max_height, cue.item_id if cue else '', cue.started_at if cue else 0,
               cue.original if cue else '', cue.translated if cue else '',
               self.config.font_family, self.config.cinema_font_size,
               self.config.cinema_original_font_size, self.config.cinema_show_original)
        if key == self._layout_key:
            return
        self._layout_key = key
        self._lines = []
        y = 8.0
        if cue:
            groups = [(cue.translated, self.config.cinema_font_size, True)]
            if self.config.cinema_show_original and cue.original.strip():
                groups.append((cue.original, self.config.cinema_original_font_size, False))
            for content, size, main in groups:
                font = QFont(self.config.font_family)
                font.setPixelSize(size)
                font.setBold(main)
                layout = QTextLayout(' '.join(content.split()), font)
                option = QTextOption(Qt.AlignHCenter)
                option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
                layout.setTextOption(option)
                layout.beginLayout()
                while True:
                    line = layout.createLine()
                    if not line.isValid():
                        break
                    line.setLineWidth(max(80, width - 28))
                    line.setPosition(QPointF(14, y))
                    y += line.height() + 2
                layout.endLayout()
                self._lines.append((layout, main))
                y += 5
        self._paginate(max(100, max_height))
        self.update()

    def _paginate(self, max_height):
        """Keep oversized cues inside the screen without discarding their text."""
        self._pages = []
        if not self._lines:
            self.setFixedHeight(64)
            return
        groups = []
        for layout, main in self._lines:
            lines = [layout.lineAt(i) for i in range(layout.lineCount())]
            # Bilingual pages share vertical space. Shorter groups stay visible
            # while a longer group continues on the next page.
            share = (.62 if main else .38) if len(self._lines) == 2 else 1.0
            budget = max(40, (max_height - 36) * share)
            chunks, chunk, height = [], [], 0
            for line in lines:
                if chunk and height + line.height() + 2 > budget:
                    chunks.append(chunk)
                    chunk, height = [], 0
                chunk.append(line)
                height += line.height() + 2
            if chunk:
                chunks.append(chunk)
            groups.append((chunks or [[]], main))
        # If the complete pair fits, avoid paging merely due to the split budget.
        actual_height = sum(sum(layout.lineAt(i).height() + 2 for i in range(layout.lineCount())) + 5
                            for layout, _ in self._lines) + 16
        if actual_height <= max_height:
            groups = [([[layout.lineAt(i) for i in range(layout.lineCount())]], main)
                      for layout, main in self._lines]
        count = max(len(chunks) for chunks, _ in groups)
        required = 64
        for page in range(count):
            entries, y = [], 8.0
            for chunks, main in groups:
                for line in chunks[min(page, len(chunks) - 1)]:
                    entries.append((line, main, y - line.position().y()))
                    y += line.height() + 2
                y += 5
            self._pages.append(entries)
            required = max(required, int(y + (24 if count > 1 else 8)))
        cue = self.timeline.cue
        if cue:
            self._seconds_per_page = min(8.0, max(4.0, len(cue.translated) / (8.0 * count)))
            if self.timeline.opacity > 0:
                cue.expires_at = cue.started_at + self._seconds_per_page * count
        self.setFixedHeight(required)

    def tick(self):
        self.update()

    def visible_text_rects(self):
        """Only painted caption lines can begin a hover interaction."""
        cue = self.timeline.cue
        if not cue or self.timeline.opacity <= 0 or not self._pages:
            return []
        page = min(len(self._pages) - 1, max(0, int((self.timeline.clock() - cue.started_at) / self._seconds_per_page)))
        return [line.naturalTextRect().translated(0, offset).adjusted(-8, -6, 8, 6).toAlignedRect()
                for line, _, offset in self._pages[page]]

    def paintEvent(self, event):
        opacity = self.timeline.opacity
        cue = self.timeline.cue
        if not cue or opacity <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setOpacity(opacity)
        if self.config.cinema_bg_opacity:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, int(255 * self.config.cinema_bg_opacity)))
            painter.drawRoundedRect(self.rect(), 8, 8)
        # Draw the shaped text with an outline. QTextLayout retains fallback
        # fonts, CJK wrapping and surrogate pairs, unlike slicing glyph strings.
        page = min(len(self._pages) - 1, max(0, int((self.timeline.clock() - cue.started_at) / self._seconds_per_page)))
        for line, main, offset in self._pages[page] if self._pages else []:
            painter.setPen(QPen(QColor('#101510')))
            for x, y in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                line.draw(painter, QPointF(x, y + offset))
            painter.setPen(QPen(QColor(self.config.cinema_text_color if main else self.config.cinema_original_text_color)))
            line.draw(painter, QPointF(0, offset))
        if len(self._pages) > 1:
            font = QFont(self.config.font_family)
            font.setPixelSize(11)
            painter.setFont(font)
            painter.setPen(QColor('#DCE4DF'))
            painter.drawText(QRectF(0, self.height() - 21, self.width(), 18), Qt.AlignCenter,
                             f'{page + 1} / {len(self._pages)}')
        painter.end()
        if cue.item_id and self._last_presented != cue.item_id:
            self._last_presented = cue.item_id
            QTimer.singleShot(0, lambda item_id=cue.item_id: self._report_presented(item_id))

    def _report_presented(self, item_id):
        cue = self.timeline.cue
        if self.isVisible() and self.timeline.opacity > 0 and cue and cue.item_id == item_id:
            self.frame_presented.emit(item_id)

    def showEvent(self, event):
        self._last_presented = None
        super().showEvent(event)
