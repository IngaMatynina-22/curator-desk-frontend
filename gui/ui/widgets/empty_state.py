from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


class EmptyState(QFrame):
    action_clicked = pyqtSignal()

    def __init__(
        self,
        title: str = "Немає даних",
        description: str = "",
        action_text: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 40, 32, 40)
        layout.setSpacing(10)

        self._title = QLabel(title)
        self._title.setObjectName("pageTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        self._description = QLabel(description)
        self._description.setObjectName("mutedLabel")
        self._description.setWordWrap(True)
        layout.addWidget(self._description)

        self._action = QPushButton(action_text or "")
        self._action.setObjectName("primaryButton")
        self._action.setVisible(bool(action_text))
        self._action.clicked.connect(self.action_clicked.emit)
        layout.addWidget(self._action)
        layout.addStretch()

    def configure(
        self,
        title: str,
        description: str = "",
        action_text: str | None = None,
    ) -> None:
        self._title.setText(title)
        self._description.setText(description)
        if action_text:
            self._action.setText(action_text)
            self._action.setVisible(True)
        else:
            self._action.setVisible(False)
