from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class PaginationControls(QWidget):
    page_changed = pyqtSignal(int)  # new offset

    def __init__(self, page_size: int = 50, parent=None) -> None:
        super().__init__(parent)
        self.page_size = page_size
        self.offset = 0
        self.total = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        self._info = QLabel("0 записів")
        layout.addWidget(self._info)
        layout.addStretch()
        self._prev = QPushButton("← Назад")
        self._next = QPushButton("Далі →")
        self._prev.clicked.connect(self._go_prev)
        self._next.clicked.connect(self._go_next)
        layout.addWidget(self._prev)
        layout.addWidget(self._next)
        self._update_buttons()

    def set_result(self, total: int, offset: int, limit: int | None = None) -> None:
        self.total = total
        self.offset = offset
        if limit:
            self.page_size = limit
        start = offset + 1 if total else 0
        end = min(offset + self.page_size, total)
        self._info.setText(f"{start}–{end} з {total}" if total else "0 записів")
        self._update_buttons()

    def _update_buttons(self) -> None:
        self._prev.setEnabled(self.offset > 0)
        self._next.setEnabled(self.offset + self.page_size < self.total)

    def _go_prev(self) -> None:
        new_offset = max(0, self.offset - self.page_size)
        self.page_changed.emit(new_offset)

    def _go_next(self) -> None:
        new_offset = self.offset + self.page_size
        if new_offset < self.total:
            self.page_changed.emit(new_offset)
