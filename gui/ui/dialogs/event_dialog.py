from __future__ import annotations

from datetime import datetime, timedelta

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
    QSpinBox,
    QVBoxLayout,
)

from app.core.enums import EventType
from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message
from gui.ui.widgets.student_selector import StudentSelector

EVENT_TYPE_UA = {
    "group_meeting": "Збори групи",
    "cultural": "Культурний",
    "organizational": "Організаційний",
    "educational": "Навчальний",
    "other": "Інше",
}


class EventDialog(QDialog):
    def __init__(self, gateway: BackendGateway, event=None, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.event = event
        self._result = None
        self.setWindowTitle("Редагувати захід" if event else "Новий захід")
        self.resize(480, 520)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title = QLineEdit()
        self.event_type = QComboBox()
        for k, t in EVENT_TYPE_UA.items():
            self.event_type.addItem(t, k)
        self.location = QLineEdit()
        now = QDateTime.currentDateTime()
        self.starts = QDateTimeEdit(now)
        self.starts.setCalendarPopup(True)
        self.ends = QDateTimeEdit(now.addSecs(3600))
        self.ends.setCalendarPopup(True)
        self.description = QLineEdit()
        self.recur_count = QSpinBox()
        self.recur_count.setRange(0, 52)
        self.recur_count.setSpecialValueText("Без повторення")
        self.recur_freq = QComboBox()
        self.recur_freq.addItem("Щотижня", "weekly")
        self.recur_freq.addItem("Щодня", "daily")
        form.addRow("Назва *", self.title)
        form.addRow("Тип", self.event_type)
        form.addRow("Місце", self.location)
        form.addRow("Початок *", self.starts)
        form.addRow("Кінець *", self.ends)
        form.addRow("Опис", self.description)
        form.addRow("Повторити (разів)", self.recur_count)
        form.addRow("Період повторення", self.recur_freq)
        layout.addLayout(form)
        layout.addWidget(QLabel("Учасники"))
        self.participants = StudentSelector(gateway)
        layout.addWidget(self.participants)
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
        if event:
            self.title.setText(event.title)
            i = self.event_type.findData(event.event_type)
            if i >= 0:
                self.event_type.setCurrentIndex(i)
            self.location.setText(event.location or "")
            self.description.setText(event.description or "")
            self.starts.setDateTime(
                QDateTime(
                    event.starts_at.year,
                    event.starts_at.month,
                    event.starts_at.day,
                    event.starts_at.hour,
                    event.starts_at.minute,
                )
            )
            self.ends.setDateTime(
                QDateTime(
                    event.ends_at.year,
                    event.ends_at.month,
                    event.ends_at.day,
                    event.ends_at.hour,
                    event.ends_at.minute,
                )
            )
            if getattr(event, "participant_ids", None):
                self.participants.set_selected_ids(event.participant_ids)
            self.recur_count.setEnabled(False)

    @property
    def saved(self):
        return self._result

    def _dt(self, edit: QDateTimeEdit) -> datetime:
        q = edit.dateTime()
        return datetime(q.date().year(), q.date().month(), q.date().day(), q.time().hour(), q.time().minute())

    def _save(self) -> None:
        starts = self._dt(self.starts)
        ends = self._dt(self.ends)
        data = {
            "title": self.title.text().strip(),
            "event_type": EventType(self.event_type.currentData()),
            "location": self.location.text().strip() or None,
            "starts_at": starts,
            "ends_at": ends,
            "description": self.description.text().strip() or None,
            "participant_ids": self.participants.selected_ids(),
        }
        self._buttons.setEnabled(False)
        try:
            conflicts = call(self.gateway.c.calendar.find_conflicts, starts, ends)
            if conflicts and self.event is None:
                names = ", ".join(
                    str(c.get("title") or c.get("id") or c) for c in conflicts[:5]
                )
                if (
                    QMessageBox.question(
                        self,
                        "Конфлікт розкладу",
                        f"Знайдено можливі конфлікти: {names}.\nУсе одно зберегти?",
                    )
                    != QMessageBox.StandardButton.Yes
                ):
                    return
            if self.event is None:
                count = self.recur_count.value()
                if count > 1:
                    self._result = call(
                        self.gateway.c.calendar.create_recurring_events,
                        data,
                        {"freq": self.recur_freq.currentData(), "interval": 1, "count": count},
                    )
                else:
                    self._result = call(self.gateway.c.events.create, data)
            else:
                self._result = call(self.gateway.c.events.update, self.event.id, data)
            self.accept()
        except (AppError, ValueError) as exc:
            msg = user_message(exc) if isinstance(exc, AppError) else str(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
