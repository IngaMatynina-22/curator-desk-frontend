"""Painted QIcons for CuratorDesk (no emoji, no external assets)."""

from __future__ import annotations

from functools import lru_cache

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF


def _pix(size: int, paint) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    paint(p, size)
    p.end()
    return pm


def _stroke(p: QPainter, color: str, width: float = 1.6) -> None:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)


@lru_cache(maxsize=64)
def icon(key: str, *, color: str = "#E8EEF1", size: int = 20) -> QIcon:
    drawers = {
        "dashboard": _draw_grid,
        "students": _draw_users,
        "attendance": _draw_check,
        "academic": _draw_book,
        "calendar": _draw_calendar,
        "assignments": _draw_clipboard,
        "duties": _draw_clock,
        "meetings": _draw_chat,
        "log": _draw_pen,
        "notifications": _draw_bell,
        "analytics": _draw_bars,
        "reports": _draw_doc,
        "archive": _draw_box,
        "settings": _draw_gear,
        "users": _draw_users,
        "today": _draw_calendar,
        "overdue": _draw_alert,
        "unread": _draw_bell,
        "plus": _draw_plus,
    }
    drawer = drawers.get(key, _draw_dot)
    return QIcon(_pix(size, lambda p, s: drawer(p, s, color)))


def _draw_dot(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawEllipse(QRectF(s * 0.35, s * 0.35, s * 0.3, s * 0.3))


def _draw_grid(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    m = s * 0.2
    gap = s * 0.08
    cell = (s - 2 * m - gap) / 2
    for i in range(2):
        for j in range(2):
            p.drawRoundedRect(
                QRectF(m + i * (cell + gap), m + j * (cell + gap), cell, cell),
                2,
                2,
            )


def _draw_users(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawEllipse(QRectF(s * 0.32, s * 0.18, s * 0.36, s * 0.36))
    p.drawArc(QRectF(s * 0.18, s * 0.55, s * 0.64, s * 0.5), 0 * 16, 180 * 16)


def _draw_check(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c, 2)
    p.drawRoundedRect(QRectF(s * 0.2, s * 0.2, s * 0.6, s * 0.6), 3, 3)
    poly = QPolygonF(
        [
            QPointF(s * 0.32, s * 0.52),
            QPointF(s * 0.45, s * 0.66),
            QPointF(s * 0.7, s * 0.36),
        ]
    )
    p.drawPolyline(poly)


def _draw_book(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawRoundedRect(QRectF(s * 0.25, s * 0.18, s * 0.5, s * 0.64), 2, 2)
    p.drawLine(QPointF(s * 0.5, s * 0.18), QPointF(s * 0.5, s * 0.82))


def _draw_calendar(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawRoundedRect(QRectF(s * 0.18, s * 0.28, s * 0.64, s * 0.54), 2, 2)
    p.drawLine(QPointF(s * 0.18, s * 0.42), QPointF(s * 0.82, s * 0.42))
    p.drawLine(QPointF(s * 0.35, s * 0.18), QPointF(s * 0.35, s * 0.32))
    p.drawLine(QPointF(s * 0.65, s * 0.18), QPointF(s * 0.65, s * 0.32))


def _draw_clipboard(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawRoundedRect(QRectF(s * 0.25, s * 0.22, s * 0.5, s * 0.6), 2, 2)
    p.drawRoundedRect(QRectF(s * 0.35, s * 0.14, s * 0.3, s * 0.14), 2, 2)
    p.drawLine(QPointF(s * 0.35, s * 0.45), QPointF(s * 0.65, s * 0.45))
    p.drawLine(QPointF(s * 0.35, s * 0.58), QPointF(s * 0.6, s * 0.58))


def _draw_clock(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawLine(QPointF(s * 0.5, s * 0.5), QPointF(s * 0.5, s * 0.32))
    p.drawLine(QPointF(s * 0.5, s * 0.5), QPointF(s * 0.68, s * 0.5))


def _draw_chat(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawRoundedRect(QRectF(s * 0.18, s * 0.22, s * 0.64, s * 0.42), 3, 3)
    poly = QPolygonF(
        [
            QPointF(s * 0.32, s * 0.64),
            QPointF(s * 0.4, s * 0.78),
            QPointF(s * 0.5, s * 0.64),
        ]
    )
    p.drawPolyline(poly)


def _draw_pen(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawLine(QPointF(s * 0.28, s * 0.72), QPointF(s * 0.7, s * 0.28))
    p.drawLine(QPointF(s * 0.28, s * 0.72), QPointF(s * 0.22, s * 0.78))
    p.drawLine(QPointF(s * 0.62, s * 0.22), QPointF(s * 0.78, s * 0.38))


def _draw_bell(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawArc(QRectF(s * 0.28, s * 0.22, s * 0.44, s * 0.44), 0 * 16, 180 * 16)
    p.drawLine(QPointF(s * 0.28, s * 0.44), QPointF(s * 0.22, s * 0.62))
    p.drawLine(QPointF(s * 0.72, s * 0.44), QPointF(s * 0.78, s * 0.62))
    p.drawLine(QPointF(s * 0.22, s * 0.62), QPointF(s * 0.78, s * 0.62))
    p.drawEllipse(QRectF(s * 0.42, s * 0.68, s * 0.16, s * 0.14))


def _draw_bars(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.setBrush(QColor(c))
    p.drawRect(QRectF(s * 0.22, s * 0.55, s * 0.14, s * 0.25))
    p.drawRect(QRectF(s * 0.43, s * 0.35, s * 0.14, s * 0.45))
    p.drawRect(QRectF(s * 0.64, s * 0.22, s * 0.14, s * 0.58))


def _draw_doc(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawRoundedRect(QRectF(s * 0.28, s * 0.16, s * 0.44, s * 0.68), 2, 2)
    p.drawLine(QPointF(s * 0.38, s * 0.36), QPointF(s * 0.62, s * 0.36))
    p.drawLine(QPointF(s * 0.38, s * 0.5), QPointF(s * 0.62, s * 0.5))
    p.drawLine(QPointF(s * 0.38, s * 0.64), QPointF(s * 0.55, s * 0.64))


def _draw_box(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawRect(QRectF(s * 0.22, s * 0.38, s * 0.56, s * 0.42))
    poly = QPolygonF(
        [
            QPointF(s * 0.22, s * 0.38),
            QPointF(s * 0.5, s * 0.22),
            QPointF(s * 0.78, s * 0.38),
        ]
    )
    p.drawPolyline(poly)
    p.drawLine(QPointF(s * 0.5, s * 0.22), QPointF(s * 0.5, s * 0.8))


def _draw_gear(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    p.drawEllipse(QRectF(s * 0.32, s * 0.32, s * 0.36, s * 0.36))
    p.drawEllipse(QRectF(s * 0.42, s * 0.42, s * 0.16, s * 0.16))
    for ang in range(0, 360, 45):
        p.save()
        p.translate(s / 2, s / 2)
        p.rotate(ang)
        p.drawRect(QRectF(-s * 0.06, -s * 0.42, s * 0.12, s * 0.14))
        p.restore()


def _draw_alert(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c)
    poly = QPolygonF(
        [
            QPointF(s * 0.5, s * 0.16),
            QPointF(s * 0.82, s * 0.78),
            QPointF(s * 0.18, s * 0.78),
        ]
    )
    p.drawPolygon(poly)
    p.drawLine(QPointF(s * 0.5, s * 0.38), QPointF(s * 0.5, s * 0.58))
    p.drawEllipse(QRectF(s * 0.46, s * 0.64, s * 0.08, s * 0.08))


def _draw_plus(p: QPainter, s: int, c: str) -> None:
    _stroke(p, c, 2)
    p.drawLine(QPointF(s * 0.5, s * 0.25), QPointF(s * 0.5, s * 0.75))
    p.drawLine(QPointF(s * 0.25, s * 0.5), QPointF(s * 0.75, s * 0.5))
