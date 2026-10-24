from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
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

from gui.gateway import BackendGateway, call, user_message


class LessonDialog(QDialog):
    def __init__(self, gateway: BackendGateway, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self._lesson = None
        self.setWindowTitle("Нове заняття")
        self.setModal(True)
        self.resize(400, 280)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.subject = QComboBox()
        subjects = call(gateway.c.academic.list_subjects, False)
        for s in subjects:
            self.subject.addItem(s.name, s.id)
        self.lesson_date = QDateEdit(QDate.currentDate())
        self.lesson_date.setCalendarPopup(True)
        self.pair = QSpinBox()
        self.pair.setRange(0, 12)
        self.pair.setSpecialValueText("—")
        self.pair.setValue(0)
        self.topic = QLineEdit()
        form.addRow("Дисципліна *", self.subject)
        form.addRow("Дата *", self.lesson_date)
        form.addRow("Пара", self.pair)
        form.addRow("Тема", self.topic)
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
            save.setText("Створити")
            save.setObjectName("primaryButton")
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel:
            cancel.setText("Скасувати")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        self._buttons = buttons
        layout.addWidget(buttons)

    @property
    def lesson(self):
        return self._lesson

    def _save(self) -> None:
        sid = self.subject.currentData()
        if sid is None:
            self._error.setText("Спочатку створіть дисципліну в розділі Успішність.")
            self._error.show()
            return
        d = self.lesson_date.date()
        data = {
            "lesson_date": date(d.year(), d.month(), d.day()),
            "subject_id": int(sid),
            "pair_number": self.pair.value() or None,
            "topic": self.topic.text().strip() or None,
        }
        self._buttons.setEnabled(False)
        try:
            self._lesson = call(self.gateway.c.attendance.create_lesson, data)
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
