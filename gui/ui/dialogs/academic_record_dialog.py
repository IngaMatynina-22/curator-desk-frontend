from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.core.enums import ControlType, GradeScale
from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message


CONTROL_UA = {
    "exam": "Іспит",
    "credit": "Залік",
    "test": "Контрольна",
    "coursework": "Курсова",
    "other": "Інше",
}
SCALE_UA = {
    "numeric": "Числова",
    "credit_pass": "Залік/незалік",
    "text": "Текстова",
}


class AcademicRecordDialog(QDialog):
    def __init__(
        self,
        gateway: BackendGateway,
        *,
        record=None,
        default_student_id: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.record = record
        self._result = None
        self.setWindowTitle("Редагувати оцінку" if record else "Новий запис")
        self.resize(440, 400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.student = QComboBox()
        page = call(gateway.c.students.list, {"limit": 500})
        for s in page.items:
            name = s.full_name or f"{s.last_name} {s.first_name}"
            self.student.addItem(name, s.id)
        if default_student_id:
            i = self.student.findData(default_student_id)
            if i >= 0:
                self.student.setCurrentIndex(i)

        self.subject = QComboBox()
        for s in call(gateway.c.academic.list_subjects, False):
            self.subject.addItem(s.name, s.id)

        self.record_date = QDateEdit(QDate.currentDate())
        self.record_date.setCalendarPopup(True)
        self.control = QComboBox()
        for k, t in CONTROL_UA.items():
            self.control.addItem(t, k)
        self.scale = QComboBox()
        for k, t in SCALE_UA.items():
            self.scale.addItem(t, k)
        self.scale.currentIndexChanged.connect(self._scale_changed)
        self.score = QDoubleSpinBox()
        self.score.setRange(0, 200)
        self.max_score = QDoubleSpinBox()
        self.max_score.setRange(0, 200)
        self.max_score.setValue(100)
        self.text_result = QLineEdit()
        self.comment = QLineEdit()

        form.addRow("Студент *", self.student)
        form.addRow("Дисципліна *", self.subject)
        form.addRow("Дата *", self.record_date)
        form.addRow("Тип контролю", self.control)
        form.addRow("Шкала", self.scale)
        form.addRow("Бал", self.score)
        form.addRow("Макс. бал", self.max_score)
        form.addRow("Текстовий результат", self.text_result)
        form.addRow("Коментар", self.comment)
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

        if record:
            self._fill(record)
        self._scale_changed()

    @property
    def saved(self):
        return self._result

    def _fill(self, r) -> None:
        i = self.student.findData(r.student_id)
        if i >= 0:
            self.student.setCurrentIndex(i)
        i = self.subject.findData(r.subject_id)
        if i >= 0:
            self.subject.setCurrentIndex(i)
        if r.record_date:
            self.record_date.setDate(QDate(r.record_date.year, r.record_date.month, r.record_date.day))
        i = self.control.findData(r.control_type)
        if i >= 0:
            self.control.setCurrentIndex(i)
        i = self.scale.findData(r.grade_scale)
        if i >= 0:
            self.scale.setCurrentIndex(i)
        if r.score is not None:
            self.score.setValue(r.score)
        if r.max_score is not None:
            self.max_score.setValue(r.max_score)
        self.text_result.setText(r.text_result or "")
        self.comment.setText(r.comment or "")

    def _scale_changed(self) -> None:
        scale = self.scale.currentData()
        numeric = scale == "numeric"
        self.score.setEnabled(numeric or scale == "text")
        self.max_score.setEnabled(numeric)
        self.text_result.setEnabled(scale in {"credit_pass", "text"})

    def _save(self) -> None:
        d = self.record_date.date()
        scale = GradeScale(self.scale.currentData())
        data = {
            "student_id": int(self.student.currentData()),
            "subject_id": int(self.subject.currentData()),
            "record_date": date(d.year(), d.month(), d.day()),
            "control_type": ControlType(self.control.currentData()),
            "grade_scale": scale,
            "score": self.score.value() if scale == GradeScale.NUMERIC else None,
            "max_score": self.max_score.value() if scale == GradeScale.NUMERIC else None,
            "text_result": self.text_result.text().strip() or None,
            "comment": self.comment.text().strip() or None,
        }
        if scale == GradeScale.TEXT:
            data["score"] = None
            data["text_result"] = self.text_result.text().strip() or None
        self._buttons.setEnabled(False)
        try:
            if self.record is None:
                self._result = call(self.gateway.c.academic.create_record, data)
            else:
                patch = {k: v for k, v in data.items() if k not in {"student_id", "subject_id"}}
                self._result = call(self.gateway.c.academic.update_record, self.record.id, patch)
            self.accept()
        except (AppError, ValueError) as exc:
            msg = user_message(exc) if isinstance(exc, AppError) else str(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
