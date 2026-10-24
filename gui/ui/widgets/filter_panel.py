from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FilterPanel(QFrame):
    """Paper filter bar: search + optional filters + clear/refresh."""

    search_changed = pyqtSignal(str)
    cleared = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, search_placeholder: str = "Пошук…", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("filterBar")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText(search_placeholder)
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(200)
        self.search.returnPressed.connect(self._emit_search)
        self._layout.addWidget(self.search, stretch=2)

        self._filters_host = QHBoxLayout()
        self._filters_host.setSpacing(10)
        self._layout.addLayout(self._filters_host, stretch=3)

        self.clear_btn = QPushButton("Очистити")
        self.clear_btn.setObjectName("ghostButton")
        self.clear_btn.clicked.connect(self._on_clear)
        self.refresh_btn = QPushButton("Оновити")
        self.refresh_btn.setObjectName("ghostButton")
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self._layout.addWidget(self.clear_btn)
        self._layout.addWidget(self.refresh_btn)

    def add_filter_widget(self, label: str, widget: QWidget) -> None:
        wrap = QHBoxLayout()
        wrap.setSpacing(6)
        lab = QLabel(label)
        lab.setObjectName("mutedLabel")
        wrap.addWidget(lab)
        wrap.addWidget(widget)
        self._filters_host.addLayout(wrap)

    def _emit_search(self) -> None:
        self.search_changed.emit(self.search.text().strip())

    def _on_clear(self) -> None:
        self.search.clear()
        self.cleared.emit()
