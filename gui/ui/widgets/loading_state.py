from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LoadingOverlay(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(247, 248, 250, 180);")
        layout = QVBoxLayout(self)
        label = QLabel("Завантаження…")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
        self.hide()

    def set_busy(self, busy: bool) -> None:
        if busy:
            if self.parentWidget() is not None:
                self.setGeometry(self.parentWidget().rect())
            self.raise_()
            self.show()
        else:
            self.hide()
