"""Lightweight QPainter bar chart (no extra deps)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QFrame, QSizePolicy


class BarChartWidget(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("chartPanel")
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._labels: list[str] = []
        self._series: list[tuple[str, list[float], str]] = []  # name, values, color

    def set_data(
        self,
        labels: list[str],
        series: list[tuple[str, list[float], str]],
    ) -> None:
        self._labels = labels
        self._series = series
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        margin_l, margin_r, margin_t, margin_b = 36, 16, 16, 36
        chart_w = max(w - margin_l - margin_r, 1)
        chart_h = max(h - margin_t - margin_b, 1)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        if not self._labels or not self._series:
            painter.setPen(QColor("#8FA3AB"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Немає даних")
            painter.end()
            return

        max_v = 1.0
        for _name, vals, _c in self._series:
            for v in vals:
                max_v = max(max_v, float(v))

        n = len(self._labels)
        group_w = chart_w / n
        bar_n = max(len(self._series), 1)
        bar_w = max(group_w / (bar_n + 1), 6)

        # axes
        painter.setPen(QColor("#C5D0D6"))
        painter.drawLine(margin_l, margin_t, margin_l, margin_t + chart_h)
        painter.drawLine(margin_l, margin_t + chart_h, margin_l + chart_w, margin_t + chart_h)

        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        for i, lab in enumerate(self._labels):
            gx = margin_l + i * group_w
            for si, (_name, vals, color) in enumerate(self._series):
                v = float(vals[i]) if i < len(vals) else 0.0
                bh = (v / max_v) * (chart_h - 4)
                bx = gx + (si + 0.5) * bar_w
                by = margin_t + chart_h - bh
                painter.fillRect(int(bx), int(by), int(bar_w * 0.85), int(bh), QColor(color))
            painter.setPen(QColor("#5A6B73"))
            painter.drawText(
                int(gx),
                margin_t + chart_h + 4,
                int(group_w),
                28,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                lab,
            )

        # legend
        lx = margin_l + 8
        ly = 4
        for name, _vals, color in self._series:
            painter.fillRect(lx, ly + 4, 10, 10, QColor(color))
            painter.setPen(QColor("#5A6B73"))
            painter.drawText(lx + 14, ly, 120, 18, Qt.AlignmentFlag.AlignVCenter, name)
            lx += 100

        painter.end()
