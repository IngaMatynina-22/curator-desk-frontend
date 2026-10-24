from __future__ import annotations

from datetime import datetime
from typing import Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.ui.labels import TIMELINE_KIND, label


class TimelineView(QScrollArea):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._host = QWidget()
        self._layout = QVBoxLayout(self._host)
        self._layout.setSpacing(8)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.addStretch()
        self.setWidget(self._host)

    def set_items(self, items: Sequence[object]) -> None:
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not items:
            empty = QLabel("Подій у хронології ще немає.")
            empty.setStyleSheet("color: #6b7280;")
            self._layout.insertWidget(0, empty)
            return

        for entry in items:
            self._layout.insertWidget(self._layout.count() - 1, self._make_card(entry))

    def _make_card(self, entry: object) -> QFrame:
        kind = getattr(entry, "kind", "") or ""
        title = getattr(entry, "title", "") or ""
        summary = getattr(entry, "summary", None) or ""
        status = getattr(entry, "status", None)
        occurred = getattr(entry, "occurred_at", None)

        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)

        head = QLabel(f"{label(TIMELINE_KIND, kind)} · {self._fmt_dt(occurred)}")
        head.setStyleSheet("color: #6b7280; font-size: 12px;")
        lay.addWidget(head)

        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("font-weight: 600;")
        lay.addWidget(title_lbl)

        if summary:
            sum_lbl = QLabel(summary)
            sum_lbl.setWordWrap(True)
            lay.addWidget(sum_lbl)

        if status:
            st = QLabel(str(status))
            st.setAlignment(Qt.AlignmentFlag.AlignLeft)
            lay.addWidget(st)

        return card

    @staticmethod
    def _fmt_dt(value: datetime | None) -> str:
        if value is None:
            return "—"
        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y %H:%M")
        return str(value)
