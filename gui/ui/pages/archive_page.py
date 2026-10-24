from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import call, user_message
from gui.ui.dialogs.confirm_dialog import ConfirmDialog
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.error_banner import ErrorBanner

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class ArchivePage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast

        root = QVBoxLayout(self)
        title = QLabel("Архів")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        self.error = ErrorBanner()
        root.addWidget(self.error)

        row = QHBoxLayout()
        self.btn_restore = QPushButton("Відновити")
        self.btn_restore.setObjectName("primaryButton")
        self.btn_restore.clicked.connect(self._restore)
        row.addWidget(self.btn_restore)
        row.addStretch()
        root.addLayout(row)

        self.tabs = QTabWidget()
        self.students_table = DataTableView()
        self.students_model = DataTableModel(
            [
                ("ПІБ", "full_name", None),
                ("Номер", "student_number", None),
                ("Статус", "status", None),
            ]
        )
        self.students_table.setModel(self.students_model)
        self.tabs.addTab(self.students_table, "Студенти")

        self.groups_table = DataTableView()
        self.groups_model = DataTableModel(
            [
                ("Назва", "name", None),
                ("Курс", "course", lambda v: str(v)),
                ("Рік", "academic_year", None),
            ]
        )
        self.groups_table.setModel(self.groups_model)
        self.tabs.addTab(self.groups_table, "Групи")
        root.addWidget(self.tabs, stretch=1)

    def refresh(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.error.clear()
        try:
            students = call(
                self.gateway.c.students.list,
                {"include_archived": True, "limit": 200},
            )
            archived_s = [s for s in students.items if s.is_archived]
            for s in archived_s:
                if not s.full_name:
                    s.full_name = f"{s.last_name} {s.first_name}"
            self.students_model.set_rows(archived_s)

            groups = call(
                self.gateway.c.groups.list,
                {"include_archived": True, "limit": 200},
            )
            self.groups_model.set_rows([g for g in groups.items if g.is_archived])
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _restore(self) -> None:
        if self.tabs.currentIndex() == 0:
            rows = self.students_table.selected_rows()
            if not rows:
                return
            if not ConfirmDialog.ask(self, "Відновлення", f"Відновити {len(rows)} студент(ів)?"):
                return
            try:
                for s in rows:
                    call(self.gateway.c.students.restore, s.id)
                if self.toast:
                    self.toast.success("Відновлено")
                self.reload()
            except AppError as exc:
                self.error.show_error(user_message(exc))
        else:
            rows = self.groups_table.selected_rows()
            if not rows:
                return
            if not ConfirmDialog.ask(self, "Відновлення", f"Відновити {len(rows)} груп(и)?"):
                return
            try:
                for g in rows:
                    call(self.gateway.c.groups.restore, g.id)
                if self.toast:
                    self.toast.success("Відновлено")
                self.reload()
            except AppError as exc:
                self.error.show_error(user_message(exc))
