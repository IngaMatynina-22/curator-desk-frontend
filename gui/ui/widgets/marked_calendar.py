"""QCalendarWidget with day markers for eventful dates."""

from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QCalendarWidget


class MarkedCalendar(QCalendarWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._marked: set[date] = set()
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setMinimumHeight(360)
        self.setMinimumWidth(420)

    def set_marked_dates(self, dates: set[date]) -> None:
        self._marked = set(dates)
        self.updateCells()

    def paintCell(self, painter: QPainter, rect, qdate: QDate) -> None:  # noqa: N802
        super().paintCell(painter, rect, qdate)
        d = date(qdate.year(), qdate.month(), qdate.day())
        if d not in self._marked:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(QColor("#1A7A6D"))
        painter.setPen(Qt.PenStyle.NoPen)
        r = 4
        cx = rect.center().x()
        cy = rect.bottom() - 8
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        painter.restore()
