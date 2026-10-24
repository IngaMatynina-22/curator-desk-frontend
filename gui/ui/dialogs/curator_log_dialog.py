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
    QTextEdit,
    QVBoxLayout,
)

from app.core.enums import CuratorLogCategory
from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message
from gui.ui.widgets.student_selector import StudentSelector

CAT_UA = {
    "organizational": "Організаційна",
    "student_communication": "Спілкування зі студентом",
    "teacher_interaction": "З викладачем",
    "parent_interaction": "З батьками",
    "academic": "Навчальна",
    "educational_event": "Виховний захід",
    "preventive": "Профілактика",
    "other": "Інше",
}


class CuratorLogDialog(QDialog):
    def __init__(self, gateway: BackendGateway, entry=None, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.entry = entry
        self._result = None
        self.setWindowTitle("Запис журналу")
        self.resize(480, 520)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.occurred = QDateTimeEdit(QDateTime.currentDateTime())
        self.occurred.setCalendarPopup(True)
        self.category = QComboBox()
        for k, t in CAT_UA.items():
            self.category.addItem(t, k)
        self.title = QLineEdit()
        self.description = QTextEdit()
        self.result = QLineEdit()
        self.next_actions = QLineEdit()
        form.addRow("Дата *", self.occurred)
        form.addRow("Категорія", self.category)
        form.addRow("Заголовок *", self.title)
        form.addRow("Опис *", self.description)
        form.addRow("Результат", self.result)
        form.addRow("Далі", self.next_actions)
        layout.addLayout(form)
        layout.addWidget(QLabel("Студенти"))
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
        if entry:
            self.title.setText(entry.title)
            self.description.setPlainText(entry.description)
            self.result.setText(entry.result or "")
            self.next_actions.setText(entry.next_actions or "")
            i = self.category.findData(entry.category)
            if i >= 0:
                self.category.setCurrentIndex(i)
            if entry.student_ids:
                self.students.set_selected_ids(entry.student_ids)

    @property
    def saved(self):
        return self._result

    def _save(self) -> None:
        q = self.occurred.dateTime()
        data = {
            "occurred_at": datetime(
                q.date().year(), q.date().month(), q.date().day(), q.time().hour(), q.time().minute()
            ),
            "category": CuratorLogCategory(self.category.currentData()),
            "title": self.title.text().strip(),
            "description": self.description.toPlainText().strip(),
            "result": self.result.text().strip() or None,
            "next_actions": self.next_actions.text().strip() or None,
            "student_ids": self.students.selected_ids(),
        }
        self._buttons.setEnabled(False)
        try:
            if self.entry is None:
                self._result = call(self.gateway.c.curator_logs.create, data)
            else:
                self._result = call(self.gateway.c.curator_logs.update, self.entry.id, data)
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
