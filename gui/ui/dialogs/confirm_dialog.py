from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        *,
        confirm_text: str = "Підтвердити",
        danger: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(420, 160)

        layout = QVBoxLayout(self)
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok is not None:
            ok.setText(confirm_text)
            if danger:
                ok.setObjectName("dangerButton")
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel is not None:
            cancel.setText("Скасувати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def ask(
        parent,
        title: str,
        message: str,
        *,
        confirm_text: str = "Підтвердити",
        danger: bool = False,
    ) -> bool:
        dlg = ConfirmDialog(
            title, message, confirm_text=confirm_text, danger=danger, parent=parent
        )
        return dlg.exec() == QDialog.DialogCode.Accepted
