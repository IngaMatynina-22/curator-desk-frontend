from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.core.enums import AttendanceStatus
from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message
from gui.ui.controllers.attendance_controller import AttendanceController
from gui.ui.dialogs.lesson_dialog import LessonDialog
from gui.ui.labels import ATTENDANCE_STATUS


class BulkAttendanceDialog(QDialog):
    """Create/select lesson + group, edit per-student status, save via bulk_mark."""

    def __init__(self, gateway: BackendGateway, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.ctrl = AttendanceController(gateway)
        self._lesson_id: int | None = None
        self.setWindowTitle("Масова відмітка відвідуваності")
        self.setModal(True)
        self.resize(640, 480)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.group = QComboBox()
        for g in self.ctrl.list_groups().items:
            self.group.addItem(g.name, g.id)
        form.addRow("Група *", self.group)

        lesson_row = QHBoxLayout()
        self.lesson_label = QLabel("Заняття не вибрано")
        btn_lesson = QPushButton("Створити заняття…")
        btn_lesson.clicked.connect(self._create_lesson)
        lesson_row.addWidget(self.lesson_label, stretch=1)
        lesson_row.addWidget(btn_lesson)
        form.addRow("Заняття *", lesson_row)

        self.default_status = QComboBox()
        for key, text in ATTENDANCE_STATUS.items():
            self.default_status.addItem(text, key)
        form.addRow("Статус за замовч.", self.default_status)
        layout.addLayout(form)

        btn_load = QPushButton("Завантажити список студентів")
        btn_load.setObjectName("primaryButton")
        btn_load.clicked.connect(self._load_preview)
        layout.addWidget(btn_load)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Студент", "Статус"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, stretch=1)

        self._error = QLabel()
        self._error.setStyleSheet("color: #b42318;")
        self._error.hide()
        layout.addWidget(self._error)

        self._names = self.ctrl.student_name_map()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save:
            save.setText("Зберегти відмітки")
            save.setObjectName("primaryButton")
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel:
            cancel.setText("Скасувати")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        self._buttons = buttons
        layout.addWidget(buttons)

    def _create_lesson(self) -> None:
        dlg = LessonDialog(self.gateway, parent=self)
        if dlg.exec() and dlg.lesson:
            self._lesson_id = dlg.lesson.id
            self.lesson_label.setText(
                f"#{dlg.lesson.id} · {dlg.lesson.lesson_date} · тема: {dlg.lesson.topic or '—'}"
            )

    def _load_preview(self) -> None:
        self._error.hide()
        if self._lesson_id is None:
            self._error.setText("Спочатку створіть заняття.")
            self._error.show()
            return
        gid = self.group.currentData()
        if gid is None:
            self._error.setText("Оберіть групу.")
            self._error.show()
            return
        try:
            preview = self.ctrl.preview_group(
                self._lesson_id, int(gid), self.default_status.currentData()
            )
            self.table.setRowCount(0)
            default = self.default_status.currentData()
            for detail in preview.details:
                sid = detail.get("student_id")
                status = detail.get("status", default)
                if hasattr(status, "value"):
                    status = status.value
                row = self.table.rowCount()
                self.table.insertRow(row)
                name_item = QTableWidgetItem(self._names.get(sid, str(sid)))
                name_item.setData(256, sid)
                self.table.setItem(row, 0, name_item)
                combo = QComboBox()
                for key, text in ATTENDANCE_STATUS.items():
                    combo.addItem(text, key)
                idx = combo.findData(str(status))
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                self.table.setCellWidget(row, 1, combo)
            if preview.warnings:
                self._error.setText("; ".join(preview.warnings))
                self._error.show()
            if preview.skipped:
                QMessageBox.information(
                    self,
                    "Попередній перегляд",
                    f"Буде відмічено: {len(preview.details)}, пропущено (вже є): {preview.skipped}.",
                )
        except AppError as exc:
            self._error.setText(user_message(exc))
            self._error.show()

    def _save(self) -> None:
        self._error.hide()
        if self._lesson_id is None or self.table.rowCount() == 0:
            self._error.setText("Немає відміток для збереження.")
            self._error.show()
            return
        marks = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            combo = self.table.cellWidget(row, 1)
            if name_item is None or not isinstance(combo, QComboBox):
                continue
            marks.append(
                {
                    "student_id": int(name_item.data(256)),
                    "status": AttendanceStatus(combo.currentData()),
                }
            )
        self._buttons.setEnabled(False)
        try:
            call(
                self.gateway.c.attendance.bulk_mark,
                {"lesson_id": self._lesson_id, "marks": marks},
            )
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
