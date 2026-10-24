from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.core.enums import AttendanceStatus
from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message
from gui.ui.labels import ATTENDANCE_STATUS


class AttendanceEditDialog(QDialog):
    def __init__(self, gateway: BackendGateway, record, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.record = record
        self.setWindowTitle("Редагувати відмітку")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.status = QComboBox()
        for key, text in ATTENDANCE_STATUS.items():
            self.status.addItem(text, key)
        idx = self.status.findData(record.status)
        if idx >= 0:
            self.status.setCurrentIndex(idx)
        self.hours = QDoubleSpinBox()
        self.hours.setRange(0, 24)
        self.hours.setValue(float(record.hours_missed or 0))
        self.reason = QLineEdit(record.reason or "")
        self.comment = QLineEdit(record.comment or "")
        form.addRow("Статус", self.status)
        form.addRow("Годин пропущено", self.hours)
        form.addRow("Причина", self.reason)
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

    def _save(self) -> None:
        data = {
            "status": AttendanceStatus(self.status.currentData()),
            "hours_missed": self.hours.value(),
            "reason": self.reason.text().strip() or None,
            "comment": self.comment.text().strip() or None,
        }
        self._buttons.setEnabled(False)
        try:
            call(self.gateway.c.attendance.update, self.record.id, data)
            self.accept()
        except AppError as exc:
            msg = user_message(exc)
            self._error.setText(msg)
            self._error.show()
            QMessageBox.warning(self, "Помилка", msg)
        finally:
            self._buttons.setEnabled(True)
