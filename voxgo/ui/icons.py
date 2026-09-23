"""Small painted icons used by the overlay UI."""

from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QPolygon


def _make_icon(kind: str, color: str) -> QIcon:
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 2)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if kind == "qr":
        for rect in (QRect(5, 5, 6, 6), QRect(17, 5, 6, 6), QRect(5, 17, 6, 6)):
            painter.drawRect(rect)
            painter.fillRect(rect.adjusted(2, 2, -2, -2), QColor(color))
        painter.fillRect(QRect(17, 17, 3, 3), QColor(color))
        painter.fillRect(QRect(21, 21, 3, 3), QColor(color))
        painter.fillRect(QRect(17, 23, 7, 2), QColor(color))
    elif kind == "settings":
        painter.drawEllipse(QPoint(14, 14), 4, 4)
        for angle in range(0, 360, 45):
            painter.save()
            painter.translate(14, 14)
            painter.rotate(angle)
            painter.drawLine(0, -11, 0, -8)
            painter.restore()
        painter.drawEllipse(QPoint(14, 14), 10, 10)
    elif kind in ("lock", "unlock"):
        painter.drawRoundedRect(QRect(7, 12, 16, 11), 2, 2)
        if kind == "lock":
            painter.drawArc(QRect(9, 4, 12, 15), 0, 180 * 16)
        else:
            painter.drawArc(QRect(13, 4, 12, 15), 35 * 16, 185 * 16)
            painter.drawLine(10, 12, 10, 10)
        painter.drawLine(14, 16, 14, 19)
    elif kind == "swap":
        painter.drawLine(7, 10, 20, 10)
        painter.drawLine(17, 7, 20, 10)
        painter.drawLine(17, 13, 20, 10)
        painter.drawLine(21, 18, 8, 18)
        painter.drawLine(11, 15, 8, 18)
        painter.drawLine(11, 21, 8, 18)
    elif kind == "pause":
        painter.setBrush(QBrush(QColor(color)))
        painter.drawRoundedRect(QRect(9, 7, 4, 14), 1, 1)
        painter.drawRoundedRect(QRect(16, 7, 4, 14), 1, 1)
    elif kind == "play":
        painter.setBrush(QBrush(QColor(color)))
        painter.drawPolygon(QPolygon([QPoint(10, 7), QPoint(21, 14), QPoint(10, 21)]))
    elif kind == "trash":
        painter.drawLine(9, 10, 21, 10)
        painter.drawLine(12, 7, 18, 7)
        painter.drawRoundedRect(QRect(10, 11, 10, 13), 2, 2)
        painter.drawLine(13, 14, 13, 21)
        painter.drawLine(17, 14, 17, 21)
    elif kind == "copy":
        painter.drawRoundedRect(QRect(8, 5, 12, 14), 1, 1)
        painter.drawRoundedRect(QRect(5, 9, 12, 14), 1, 1)
    elif kind == "compact":
        painter.drawRect(QRect(7, 8, 16, 12))
        painter.drawLine(7, 14, 12, 14)
        painter.drawLine(10, 11, 12, 14)
        painter.drawLine(10, 17, 12, 14)
        painter.drawLine(23, 14, 18, 14)
        painter.drawLine(20, 11, 18, 14)
        painter.drawLine(20, 17, 18, 14)
    elif kind == "expand":
        painter.drawRect(QRect(7, 8, 16, 12))
        painter.drawLine(12, 14, 7, 14)
        painter.drawLine(9, 11, 7, 14)
        painter.drawLine(9, 17, 7, 14)
        painter.drawLine(18, 14, 23, 14)
        painter.drawLine(21, 11, 23, 14)
        painter.drawLine(21, 17, 23, 14)
    elif kind == "help":
        painter.drawEllipse(QPoint(14, 14), 10, 10)
        painter.drawArc(QRect(10, 7, 8, 8), 20 * 16, 220 * 16)
        painter.drawLine(14, 15, 14, 17)
        painter.drawPoint(14, 21)
    else:
        painter.drawLine(8, 8, 20, 20)
        painter.drawLine(20, 8, 8, 20)

    painter.end()
    return QIcon(pixmap)
