from __future__ import annotations

from datetime import date, time

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDateEdit,
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
from gui.ui.widgets.student_selector import StudentSelector


class DutyDialog(QDialog):
    def __init__(self, gateway: BackendGateway, duty=None, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.duty = duty
        self._result = None
        self.setWindowTitle("Чергування")
        self.resize(440, 420)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.duty_date = QDateEdit(QDate.currentDate())
        self.duty_date.setCalendarPopup(True)
        self.location = QLineEdit()
        self.duty_type = QLineEdit()
        self.start_time = QLineEdit()
        self.start_time.setPlaceholderText("09:00")
        self.end_time = QLineEdit()
        self.end_time.setPlaceholderText("10:00")
        self.comment = QLineEdit()
        form.addRow("Дата *", self.duty_date)
        form.addRow("Місце", self.location)
        form.addRow("Тип", self.duty_type)
        form.addRow("Початок", self.start_time)
        form.addRow("Кінець", self.end_time)
        form.addRow("Коментар", self.comment)
        layout.addLayout(form)
        layout.addWidget(QLabel("Призначені студенти"))
        self.students = StudentSelector(gateway)
        layout.addWidget(self.students)
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
        if duty:
            d = duty.duty_date
            self.duty_date.setDate(QDate(d.year, d.month, d.day))
            self.location.setText(duty.location or "")
            self.duty_type.setText(duty.duty_type or "")
            self.comment.setText(duty.comment or "")
            if getattr(duty, "student_ids", None):
                self.students.set_selected_ids(duty.student_ids)

    @property
    def saved(self):
        return self._result

    @staticmethod
    def _parse_time(value: str) -> time | None:
        text = value.strip()
        if not text:
            return None
        parts = text.split(":")
        return time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)

    def _save(self) -> None:
        d = self.duty_date.date()
        data = {
            "duty_date": date(d.year(), d.month(), d.day()),
            "location": self.location.text().strip() or None,
            "duty_type": self.duty_type.text().strip() or None,
            "start_time": self._parse_time(self.start_time.text()),
            "end_time": self._parse_time(self.end_time.text()),
            "comment": self.comment.text().strip() or None,
            "student_ids": self.students.selected_ids(),
        }
        self._buttons.setEnabled(False)
        try:
            if self.duty is None:
                self._result = call(self.gateway.c.duties.create, data)
            else:
                self._result = call(self.gateway.c.duties.update, self.duty.id, data)
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
