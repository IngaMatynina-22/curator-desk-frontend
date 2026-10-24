from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from app.core.exceptions import AppError
from app.schemas.group import GroupOut

from gui.gateway import BackendGateway, call, user_message


class GroupDialog(QDialog):
    def __init__(
        self,
        gateway: BackendGateway,
        *,
        group: GroupOut | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.group = group
        self._result: GroupOut | None = None
        self.setWindowTitle("Редагувати групу" if group else "Нова група")
        self.setModal(True)
        self.resize(400, 280)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit()
        self.specialty = QLineEdit()
        self.course = QSpinBox()
        self.course.setRange(1, 10)
        self.academic_year = QLineEdit()
        self.academic_year.setPlaceholderText("2025/2026")
        self.curator_name = QLineEdit()

        form.addRow("Назва *", self.name)
        form.addRow("Спеціальність *", self.specialty)
        form.addRow("Курс *", self.course)
        form.addRow("Навчальний рік *", self.academic_year)
        form.addRow("Куратор", self.curator_name)
        layout.addLayout(form)

        self._error = QLabel()
        self._error.setStyleSheet("color: #b42318;")
        self._error.hide()
        layout.addWidget(self._error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save is not None:
            save.setText("Зберегти")
            save.setObjectName("primaryButton")
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel is not None:
            cancel.setText("Скасувати")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        self._buttons = buttons
        layout.addWidget(buttons)

        if group is not None:
            self.name.setText(group.name)
            self.specialty.setText(group.specialty)
            self.course.setValue(group.course)
            self.academic_year.setText(group.academic_year)
            self.curator_name.setText(group.curator_name or "")

    @property
    def saved_group(self) -> GroupOut | None:
        return self._result

    def _save(self) -> None:
        self._error.hide()
        data = {
            "name": self.name.text().strip(),
            "specialty": self.specialty.text().strip(),
            "course": self.course.value(),
            "academic_year": self.academic_year.text().strip(),
            "curator_name": self.curator_name.text().strip() or None,
        }
        self._buttons.setEnabled(False)
        try:
            if self.group is None:
                self._result = call(self.gateway.c.groups.create, data)
            else:
                self._result = call(self.gateway.c.groups.update, self.group.id, data)
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
