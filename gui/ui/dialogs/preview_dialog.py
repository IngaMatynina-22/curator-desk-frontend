from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QVBoxLayout,
)


class PreviewDialog(QDialog):
    def __init__(
        self,
        title: str,
        summary: str,
        details: list[Any] | None = None,
        *,
        warnings: list[str] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(520, 400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(summary))

        if warnings:
            for w in warnings:
                lbl = QLabel(f"⚠ {w}")
                lbl.setWordWrap(True)
                layout.addWidget(lbl)

        self._list = QListWidget()
        for item in details or []:
            if isinstance(item, dict):
                text = ", ".join(f"{k}: {v}" for k, v in item.items())
            else:
                text = str(item)
            self._list.addItem(text)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok is not None:
            ok.setText("Застосувати")
            ok.setObjectName("primaryButton")
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel is not None:
            cancel.setText("Скасувати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
