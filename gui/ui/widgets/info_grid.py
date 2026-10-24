"""Paper info grid: label/value pairs in two columns."""

from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout


class InfoGrid(QFrame):
    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("infoGrid")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)
        if title:
            head = QLabel(title)
            head.setObjectName("pageTitle")
            head.setStyleSheet("font-size: 16px;")
            root.addWidget(head)
        self._grid = QGridLayout()
        self._grid.setHorizontalSpacing(24)
        self._grid.setVerticalSpacing(14)
        root.addLayout(self._grid)
        self._values: dict[str, QLabel] = {}
        self._row = 0
        self._col = 0

    def add_field(self, key: str, caption: str) -> None:
        wrap = QVBoxLayout()
        wrap.setSpacing(2)
        cap = QLabel(caption)
        cap.setObjectName("mutedLabel")
        val = QLabel("—")
        val.setWordWrap(True)
        val.setObjectName("infoValue")
        wrap.addWidget(cap)
        wrap.addWidget(val)
        self._values[key] = val
        self._grid.addLayout(wrap, self._row, self._col)
        self._col += 1
        if self._col >= 2:
            self._col = 0
            self._row += 1

    def set_value(self, key: str, text: str) -> None:
        lbl = self._values.get(key)
        if lbl is not None:
            lbl.setText(text or "—")
