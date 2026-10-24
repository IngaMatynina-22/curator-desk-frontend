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


class SubjectDialog(QDialog):
    def __init__(self, gateway: BackendGateway, subject=None, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.subject = subject
        self._result = None
        self.setWindowTitle("Дисципліна" if subject else "Нова дисципліна")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(subject.name if subject else "")
        self.code = QLineEdit(subject.code if subject and subject.code else "")
        self.description = QLineEdit(subject.description if subject and subject.description else "")
        form.addRow("Назва *", self.name)
        form.addRow("Код", self.code)
        form.addRow("Опис", self.description)
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

    @property
    def saved(self):
        return self._result

    def _save(self) -> None:
        data = {
            "name": self.name.text().strip(),
            "code": self.code.text().strip() or None,
            "description": self.description.text().strip() or None,
        }
        self._buttons.setEnabled(False)
        try:
            if self.subject is None:
                self._result = call(self.gateway.c.academic.create_subject, data)
            else:
                self._result = call(self.gateway.c.academic.update_subject, self.subject.id, data)
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
