from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QStatusBar


class ToastManager:
    """Short confirmations via status bar (desktop-appropriate, no floating noise)."""

    def __init__(self, status_bar: QStatusBar) -> None:
        self._bar = status_bar
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._bar.clearMessage)
        self._label = QLabel()
        self._bar.addPermanentWidget(self._label)
        self._label.hide()

    def success(self, message: str, timeout_ms: int = 3500) -> None:
        self._bar.showMessage(message, timeout_ms)
        self._timer.start(timeout_ms)

    def warning(self, message: str, timeout_ms: int = 5000) -> None:
        self._bar.showMessage(f"⚠ {message}", timeout_ms)
        self._timer.start(timeout_ms)
