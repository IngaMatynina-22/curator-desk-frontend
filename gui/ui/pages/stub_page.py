from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from gui.ui.widgets.empty_state import EmptyState


class StubPage(QWidget):
    def __init__(self, title: str, description: str | None = None, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)
        empty = EmptyState(
            title="Розділ буде підключено",
            description=description
            or "Цей екран з'явиться після наступного етапу реалізації. "
            "Дані вже доступні через backend-сервіси.",
        )
        layout.addWidget(empty, stretch=1)

    def refresh(self) -> None:
        return
