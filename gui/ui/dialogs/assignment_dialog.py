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
    QTextEdit,
    QVBoxLayout,
)

from app.core.enums import AssignmentPriority, AssignmentStatus
from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message
from gui.ui.labels import ASSIGNMENT_PRIORITY, ASSIGNMENT_STATUS
from gui.ui.widgets.student_selector import StudentSelector


class AssignmentDialog(QDialog):
    def __init__(self, gateway: BackendGateway, assignment=None, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.assignment = assignment
        self._result = None
        self.setWindowTitle("Доручення")
        self.resize(480, 520)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title = QLineEdit()
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        self.due = QDateEdit(QDate.currentDate().addDays(7))
        self.due.setCalendarPopup(True)
        self.priority = QComboBox()
        for k, t in ASSIGNMENT_PRIORITY.items():
            self.priority.addItem(t, k)
        self.status = QComboBox()
        for k, t in ASSIGNMENT_STATUS.items():
            self.status.addItem(t, k)
        form.addRow("Назва *", self.title)
        form.addRow("Опис", self.description)
        form.addRow("Строк *", self.due)
        form.addRow("Пріоритет", self.priority)
        form.addRow("Статус", self.status)
        layout.addLayout(form)
        layout.addWidget(QLabel("Виконавці"))
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
        if assignment:
            self.title.setText(assignment.title)
            self.description.setPlainText(assignment.description or "")
            d = assignment.due_date
            self.due.setDate(QDate(d.year, d.month, d.day))
            i = self.priority.findData(assignment.priority)
            if i >= 0:
                self.priority.setCurrentIndex(i)
            i = self.status.findData(assignment.status)
            if i >= 0:
                self.status.setCurrentIndex(i)
            if assignment.student_ids:
                self.students.set_selected_ids(assignment.student_ids)

    @property
    def saved(self):
        return self._result

    def _save(self) -> None:
        d = self.due.date()
        data = {
            "title": self.title.text().strip(),
            "description": self.description.toPlainText().strip() or None,
            "due_date": date(d.year(), d.month(), d.day()),
            "priority": AssignmentPriority(self.priority.currentData()),
            "status": AssignmentStatus(self.status.currentData()),
            "student_ids": self.students.selected_ids(),
        }
        self._buttons.setEnabled(False)
        try:
            if self.assignment is None:
                self._result = call(self.gateway.c.assignments.create, data)
            else:
                self._result = call(self.gateway.c.assignments.update, self.assignment.id, data)
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
