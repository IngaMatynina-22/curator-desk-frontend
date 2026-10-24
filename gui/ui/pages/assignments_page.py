from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.enums import AssignmentStatus
from app.core.exceptions import AppError
from app.schemas.assignment import AssignmentFilter

from gui.gateway import call, user_message
from gui.ui.dialogs.assignment_dialog import AssignmentDialog
from gui.ui.dialogs.confirm_dialog import ConfirmDialog
from gui.ui.dialogs.preview_dialog import PreviewDialog
from gui.ui.labels import ASSIGNMENT_PRIORITY, ASSIGNMENT_STATUS, label
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.empty_state import EmptyState
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.filter_panel import FilterPanel
from gui.ui.widgets.pagination import PaginationControls

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class AssignmentsPage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast
        self._offset = 0

        root = QVBoxLayout(self)
        row = QHBoxLayout()
        title = QLabel("Доручення")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        row.addStretch()
        self.btn_add = QPushButton("Створити")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self._add)
        self.btn_edit = QPushButton("Редагувати")
        self.btn_edit.clicked.connect(self._edit)
        self.btn_complete = QPushButton("Завершити")
        self.btn_complete.clicked.connect(self._complete)
        self.btn_bulk = QPushButton("Масова зміна статусу")
        self.btn_bulk.clicked.connect(self._bulk_status)
        for b in (self.btn_add, self.btn_edit, self.btn_complete, self.btn_bulk):
            row.addWidget(b)
        self.btn_edit.setEnabled(False)
        self.btn_complete.setEnabled(False)
        root.addLayout(row)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        self.filters = FilterPanel()
        self.filters.search.hide()
        self.status_f = QComboBox()
        self.status_f.addItem("Усі", None)
        for k, t in ASSIGNMENT_STATUS.items():
            self.status_f.addItem(t, k)
        self.overdue_f = QComboBox()
        self.overdue_f.addItem("Усі строки", False)
        self.overdue_f.addItem("Лише прострочені", True)
        self.filters.add_filter_widget("Статус", self.status_f)
        self.filters.add_filter_widget("Прострочення", self.overdue_f)
        self.filters.cleared.connect(self._clear)
        self.filters.refresh_requested.connect(self.reload)
        self.status_f.currentIndexChanged.connect(lambda _: self.reload())
        self.overdue_f.currentIndexChanged.connect(lambda _: self.reload())
        root.addWidget(self.filters)

        self.stack = QStackedWidget()
        self.table = DataTableView()
        self.model = DataTableModel(
            [
                ("Назва", "title", None),
                ("Строк", "due_date", lambda v: str(v)),
                ("Пріоритет", "priority", lambda v: label(ASSIGNMENT_PRIORITY, v)),
                ("Статус", "status", lambda v: label(ASSIGNMENT_STATUS, v)),
                ("Прострочено", "is_overdue", lambda v: "Так" if v else "Ні"),
                ("Виконавці", "student_ids", lambda v: str(len(v or []))),
            ]
        )
        self.table.setModel(self.model)
        self.table.selection_changed_rows.connect(self._on_sel)
        self.table.row_activated.connect(lambda _: self._edit())
        self.empty = EmptyState("Немає доручень", "Створіть перше доручення.", "Створити")
        self.empty.action_clicked.connect(self._add)
        self.stack.addWidget(self.table)
        self.stack.addWidget(self.empty)
        root.addWidget(self.stack, stretch=1)
        self.pagination = PaginationControls(50)
        self.pagination.page_changed.connect(self._page)
        root.addWidget(self.pagination)

    def refresh(self) -> None:
        self.reload()

    def create_new(self) -> None:
        self._add()

    def reload(self) -> None:
        self.error.clear()
        try:
            page = call(
                self.gateway.c.assignments.list,
                AssignmentFilter(
                    status=AssignmentStatus(self.status_f.currentData())
                    if self.status_f.currentData()
                    else None,
                    overdue_only=bool(self.overdue_f.currentData()),
                    offset=self._offset,
                    limit=50,
                ),
            )
            self.model.set_rows(page.items)
            self.pagination.set_result(page.total, page.offset, page.limit)
            self.stack.setCurrentWidget(self.table if page.items else self.empty)
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add(self) -> None:
        dlg = AssignmentDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Доручення створено")
            self.reload()

    def _edit(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        dlg = AssignmentDialog(self.gateway, assignment=rows[0], parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Оновлено")
            self.reload()

    def _complete(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        if not ConfirmDialog.ask(self, "Завершення", "Позначити доручення виконаним?"):
            return
        try:
            call(self.gateway.c.assignments.complete, rows[0].id)
            if self.toast:
                self.toast.success("Виконано")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _bulk_status(self) -> None:
        rows = self.table.selected_rows()
        if not rows:
            return
        ids = [r.id for r in rows]
        preview = call(
            self.gateway.c.bulk.bulk_update_assignments,
            {"ids": ids, "status": AssignmentStatus.IN_PROGRESS, "preview": True},
        )
        dlg = PreviewDialog(
            "Масова зміна статусу",
            f"Встановити статус «В роботі» для {len(ids)} доручень.",
            details=preview.details,
            parent=self,
        )
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        try:
            result = call(
                self.gateway.c.bulk.bulk_update_assignments,
                {"ids": ids, "status": AssignmentStatus.IN_PROGRESS, "preview": False},
            )
            if self.toast:
                self.toast.success(f"Оновлено: {result.applied}")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _on_sel(self, rows: list) -> None:
        one = len(rows) == 1
        self.btn_edit.setEnabled(one)
        self.btn_complete.setEnabled(one)

    def _page(self, offset: int) -> None:
        self._offset = offset
        self.reload()

    def _clear(self) -> None:
        self.status_f.setCurrentIndex(0)
        self.overdue_f.setCurrentIndex(0)
        self._offset = 0
        self.reload()
