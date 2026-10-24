from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message


class ChangePasswordDialog(QDialog):
    def __init__(self, gateway: BackendGateway, user_id: int, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.user_id = user_id
        self.setWindowTitle("Змінити пароль")
        self.setModal(True)
        self.resize(360, 200)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.old = QLineEdit()
        self.old.setEchoMode(QLineEdit.EchoMode.Password)
        self.new = QLineEdit()
        self.new.setEchoMode(QLineEdit.EchoMode.Password)
        self.new2 = QLineEdit()
        self.new2.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Поточний пароль", self.old)
        form.addRow("Новий пароль", self.new)
        form.addRow("Підтвердження", self.new2)
        layout.addLayout(form)

        self._error = QLabel()
        self._error.setStyleSheet("color: #b42318;")
        self._error.hide()
        layout.addWidget(self._error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save:
            save.setText("Зберегти")
            save.setObjectName("primaryButton")
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel:
            cancel.setText("Скасувати")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        self._buttons = buttons
        layout.addWidget(buttons)

    def _save(self) -> None:
        if self.new.text() != self.new2.text():
            self._error.setText("Паролі не збігаються.")
            self._error.show()
            return
        self._buttons.setEnabled(False)
        try:
            call(
                self.gateway.c.auth.change_password,
                self.user_id,
                self.old.text(),
                self.new.text(),
            )
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
