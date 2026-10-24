"""Subtle 24px grid backdrop for chalk workspace / auth canvas."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class PatternBackdrop(QWidget):
    def __init__(self, parent=None, *, grid_color: str = "#0C2A35", opacity: float = 0.08) -> None:
        super().__init__(parent)
        self.setObjectName("canvas")
        self._grid = QColor(grid_color)
        self._grid.setAlphaF(opacity)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def set_grid_color(self, color: str, opacity: float = 0.08) -> None:
        self._grid = QColor(color)
        self._grid.setAlphaF(opacity)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        pen = QPen(self._grid)
        pen.setWidth(1)
        painter.setPen(pen)
        step = 24
        w, h = self.width(), self.height()
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)
        painter.end()
