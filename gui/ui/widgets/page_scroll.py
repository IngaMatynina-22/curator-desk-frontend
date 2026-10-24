"""Scrollable page body — uses app-styled QScrollBar via global QSS."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget


class PageScroll(QScrollArea):
    """Wraps a content widget so tall/wide pages scroll instead of clipping."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._body = QWidget()
        self._body.setObjectName("pageScrollBody")
        self._layout = QVBoxLayout(self._body)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self.setWidget(self._body)

    @property
    def body_layout(self) -> QVBoxLayout:
        return self._layout
