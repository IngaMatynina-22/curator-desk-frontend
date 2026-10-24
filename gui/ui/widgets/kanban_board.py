"""Trello-like assignment columns (no drag-drop)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.ui.icons import icon
from gui.ui.labels import ASSIGNMENT_STATUS, label


class KanbanCard(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self, assignment: Any, parent=None) -> None:
        super().__init__(parent)
        self.assignment = assignment
        self.setObjectName("kanbanCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        title = QLabel(getattr(assignment, "title", "—"))
        title.setWordWrap(True)
        title.setObjectName("kanbanCardTitle")
        lay.addWidget(title)
        due = getattr(assignment, "due_date", None)
        meta = QLabel(f"До {due}" if due else "")
        meta.setObjectName("mutedLabel")
        lay.addWidget(meta)
        st = getattr(assignment, "status", "") or ""
        badge = QLabel(label(ASSIGNMENT_STATUS, st) if st else st)
        badge.setObjectName("mutedLabel")
        lay.addWidget(badge)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.assignment)
        super().mousePressEvent(event)


class KanbanColumn(QFrame):
    add_clicked = pyqtSignal()
    card_clicked = pyqtSignal(object)

    def __init__(self, title: str, *, allow_add: bool = True, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("kanbanColumn")
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        head = QHBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("kanbanColumnTitle")
        head.addWidget(self.title_lbl)
        head.addStretch()
        self.count_lbl = QLabel("0")
        self.count_lbl.setObjectName("mutedLabel")
        head.addWidget(self.count_lbl)
        if allow_add:
            add = QPushButton()
            add.setObjectName("ghostButton")
            add.setIcon(icon("plus", color="#1A7A6D", size=16))
            add.setToolTip("Додати")
            add.setFixedSize(28, 28)
            add.clicked.connect(self.add_clicked.emit)
            head.addWidget(add)
        root.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._host = QWidget()
        self._cards = QVBoxLayout(self._host)
        self._cards.setContentsMargins(0, 0, 0, 0)
        self._cards.setSpacing(8)
        self._cards.addStretch()
        scroll.setWidget(self._host)
        root.addWidget(scroll, stretch=1)

    def set_items(self, items: list[Any]) -> None:
        while self._cards.count() > 1:
            item = self._cards.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.count_lbl.setText(str(len(items)))
        for a in items:
            card = KanbanCard(a)
            card.clicked.connect(self.card_clicked.emit)
            self._cards.insertWidget(self._cards.count() - 1, card)


class KanbanBoard(QWidget):
    add_requested = pyqtSignal(str)  # column key
    card_activated = pyqtSignal(object)

    def __init__(
        self,
        columns: list[tuple[str, str]],
        *,
        parent=None,
    ) -> None:
        """columns: list of (key, title)."""
        super().__init__(parent)
        self._cols: dict[str, KanbanColumn] = {}
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        for key, title in columns:
            col = KanbanColumn(title, allow_add=True)
            col.add_clicked.connect(lambda k=key: self.add_requested.emit(k))
            col.card_clicked.connect(self.card_activated.emit)
            self._cols[key] = col
            lay.addWidget(col, stretch=1)

    def set_column_items(self, key: str, items: list[Any]) -> None:
        col = self._cols.get(key)
        if col is not None:
            col.set_items(items)
