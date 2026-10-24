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
    QVBoxLayout,
)

from app.core.enums import StudentStatus, StudyForm
from app.core.exceptions import AppError
from app.schemas.student import StudentOut

from gui.gateway import BackendGateway, call, user_message
from gui.ui.labels import STUDENT_STATUS, STUDY_FORM


class StudentDialog(QDialog):
    def __init__(
        self,
        gateway: BackendGateway,
        *,
        student: StudentOut | None = None,
        default_group_id: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.student = student
        self.setWindowTitle("Редагувати студента" if student else "Новий студент")
        self.setModal(True)
        self.resize(480, 520)
        self._result: StudentOut | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.student_number = QLineEdit()
        self.last_name = QLineEdit()
        self.first_name = QLineEdit()
        self.middle_name = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.address = QLineEdit()
        self.specialty = QLineEdit()
        self.course = QLineEdit()
        self.course.setPlaceholderText("1–10")

        self.group = QComboBox()
        self._load_groups(default_group_id)

        self.status = QComboBox()
        for key, text in STUDENT_STATUS.items():
            self.status.addItem(text, key)

        self.study_form = QComboBox()
        for key, text in STUDY_FORM.items():
            self.study_form.addItem(text, key)

        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setSpecialValueText("—")
        self.birth_date.setDate(QDate(2000, 1, 1))

        self.enrollment_date = QDateEdit()
        self.enrollment_date.setCalendarPopup(True)
        self.enrollment_date.setDate(QDate.currentDate())

        form.addRow("Навчальний номер *", self.student_number)
        form.addRow("Прізвище *", self.last_name)
        form.addRow("Ім'я *", self.first_name)
        form.addRow("По батькові", self.middle_name)
        form.addRow("Група *", self.group)
        form.addRow("Статус", self.status)
        form.addRow("Форма навчання", self.study_form)
        form.addRow("Курс", self.course)
        form.addRow("Спеціальність", self.specialty)
        form.addRow("Телефон", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Адреса", self.address)
        form.addRow("Дата народження", self.birth_date)
        form.addRow("Дата зарахування", self.enrollment_date)

        hint = QLabel("* обов'язкові поля")
        hint.setStyleSheet("color: #6b7280;")
        layout.addLayout(form)
        layout.addWidget(hint)

        self._field_error = QLabel()
        self._field_error.setWordWrap(True)
        self._field_error.setStyleSheet("color: #b42318;")
        self._field_error.hide()
        layout.addWidget(self._field_error)

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

        if student is not None:
            self._fill(student)

    @property
    def saved_student(self) -> StudentOut | None:
        return self._result

    def _load_groups(self, default_group_id: int | None) -> None:
        page = call(self.gateway.c.groups.list, {"limit": 200, "include_archived": False})
        self.group.clear()
        for g in page.items:
            self.group.addItem(f"{g.name} (курс {g.course})", g.id)
        if default_group_id is not None:
            idx = self.group.findData(default_group_id)
            if idx >= 0:
                self.group.setCurrentIndex(idx)

    def _fill(self, s: StudentOut) -> None:
        self.student_number.setText(s.student_number)
        self.last_name.setText(s.last_name)
        self.first_name.setText(s.first_name)
        self.middle_name.setText(s.middle_name or "")
        self.phone.setText(s.phone or "")
        self.email.setText(s.email or "")
        self.address.setText(s.address or "")
        self.specialty.setText(s.specialty or "")
        self.course.setText("" if s.course is None else str(s.course))
        idx = self.group.findData(s.group_id)
        if idx >= 0:
            self.group.setCurrentIndex(idx)
        idx = self.status.findData(s.status)
        if idx >= 0:
            self.status.setCurrentIndex(idx)
        idx = self.study_form.findData(s.study_form)
        if idx >= 0:
            self.study_form.setCurrentIndex(idx)
        if s.birth_date:
            self.birth_date.setDate(QDate(s.birth_date.year, s.birth_date.month, s.birth_date.day))
        if s.enrollment_date:
            self.enrollment_date.setDate(
                QDate(s.enrollment_date.year, s.enrollment_date.month, s.enrollment_date.day)
            )

    def _payload(self) -> dict:
        group_id = self.group.currentData()
        if group_id is None:
            raise ValueError("Оберіть групу")
        course_text = self.course.text().strip()
        course = int(course_text) if course_text else None
        birth = self.birth_date.date()
        payload = {
            "student_number": self.student_number.text().strip(),
            "last_name": self.last_name.text().strip(),
            "first_name": self.first_name.text().strip(),
            "middle_name": self.middle_name.text().strip() or None,
            "phone": self.phone.text().strip() or None,
            "email": self.email.text().strip() or None,
            "address": self.address.text().strip() or None,
            "specialty": self.specialty.text().strip() or None,
            "course": course,
            "group_id": int(group_id),
            "status": StudentStatus(self.status.currentData()),
            "study_form": StudyForm(self.study_form.currentData()),
            "enrollment_date": date(
                self.enrollment_date.date().year(),
                self.enrollment_date.date().month(),
                self.enrollment_date.date().day(),
            ),
            "birth_date": date(birth.year(), birth.month(), birth.day()),
        }
        return payload

    def _save(self) -> None:
        self._field_error.hide()
        self._buttons.setEnabled(False)
        try:
            data = self._payload()
            if self.student is None:
                self._result = call(self.gateway.c.students.create, data)
            else:
                self._result = call(self.gateway.c.students.update, self.student.id, data)
            self.accept()
        except (AppError, ValueError) as exc:
            msg = user_message(exc) if isinstance(exc, AppError) else str(exc)
            self._field_error.setText(msg)
            self._field_error.show()
            QMessageBox.warning(self, "Помилка збереження", msg)
        finally:
            self._buttons.setEnabled(True)
