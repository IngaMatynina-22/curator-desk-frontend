from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.core.enums import MeetingFormat
from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message
from gui.ui.widgets.student_selector import StudentSelector


class MeetingDialog(QDialog):
    def __init__(self, gateway: BackendGateway, meeting=None, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.meeting = meeting
        self._result = None
        self.setWindowTitle("Зустріч")
        self.resize(460, 480)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.topic = QLineEdit()
        self.fmt = QComboBox()
        self.fmt.addItem("Індивідуальна", "individual")
        self.fmt.addItem("Групова", "group")
        self.when = QDateTimeEdit(QDateTime.currentDateTime())
        self.when.setCalendarPopup(True)
        self.notes = QLineEdit()
        form.addRow("Тема *", self.topic)
        form.addRow("Формат", self.fmt)
        form.addRow("Дата і час *", self.when)
        form.addRow("Нотатки", self.notes)
        layout.addLayout(form)
        layout.addWidget(QLabel("Учасники"))
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
        if meeting:
            self.topic.setText(meeting.topic)
            i = self.fmt.findData(meeting.format)
            if i >= 0:
                self.fmt.setCurrentIndex(i)
            self.notes.setText(meeting.notes or "")
            if getattr(meeting, "student_ids", None):
                self.students.set_selected_ids(meeting.student_ids)

    @property
    def saved(self):
        return self._result

    def _save(self) -> None:
        q = self.when.dateTime()
        data = {
            "topic": self.topic.text().strip(),
            "format": MeetingFormat(self.fmt.currentData()),
            "scheduled_at": datetime(
                q.date().year(), q.date().month(), q.date().day(), q.time().hour(), q.time().minute()
            ),
            "notes": self.notes.text().strip() or None,
            "student_ids": self.students.selected_ids(),
        }
        self._buttons.setEnabled(False)
        try:
            if self.meeting is None:
                self._result = call(self.gateway.c.meetings.create, data)
            else:
                self._result = call(self.gateway.c.meetings.update, self.meeting.id, data)
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
