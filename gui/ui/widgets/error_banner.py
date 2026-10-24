from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


class ErrorBanner(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("errorBanner")
        self.setVisible(False)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        self._label = QLabel()
        self._label.setWordWrap(True)
        layout.addWidget(self._label, stretch=1)
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.clear)
        layout.addWidget(close_btn)

    def show_error(self, message: str) -> None:
        self._label.setText(message)
        self.setVisible(True)

    def clear(self) -> None:
        self._label.clear()
        self.setVisible(False)
