from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.core.exceptions import AppError
from app.schemas.meeting import MeetingFilter

from gui.gateway import call, user_message
from gui.ui.dialogs.confirm_dialog import ConfirmDialog
from gui.ui.dialogs.meeting_dialog import MeetingDialog
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.empty_state import EmptyState
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.filter_panel import FilterPanel
from gui.ui.widgets.pagination import PaginationControls

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class MeetingsPage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast
        self._offset = 0

        root = QVBoxLayout(self)
        row = QHBoxLayout()
        title = QLabel("Зустрічі")
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
        self.btn_cancel = QPushButton("Скасувати")
        self.btn_cancel.clicked.connect(self._cancel)
        for b in (self.btn_add, self.btn_edit, self.btn_complete, self.btn_cancel):
            row.addWidget(b)
        self.btn_edit.setEnabled(False)
        self.btn_complete.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        root.addLayout(row)

        self.error = ErrorBanner()
        root.addWidget(self.error)
        self.filters = FilterPanel()
        self.filters.search.hide()
        self.filters.refresh_requested.connect(self.reload)
        self.filters.cleared.connect(self.reload)
        root.addWidget(self.filters)

        self.stack = QStackedWidget()
        self.table = DataTableView()
        self.model = DataTableModel(
            [
                ("Тема", "topic", None),
                ("Дата", "scheduled_at", lambda v: str(v)),
                ("Формат", "format", None),
                ("Статус", "status", None),
                ("Учасники", "student_ids", lambda v: str(len(v or []))),
            ]
        )
        self.table.setModel(self.model)
        self.table.selection_changed_rows.connect(self._on_sel)
        self.table.row_activated.connect(lambda _: self._edit())
        self.empty = EmptyState("Немає зустрічей", "Заплануйте зустріч зі студентами.", "Створити")
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
            page = call(self.gateway.c.meetings.list, MeetingFilter(offset=self._offset, limit=50))
            self.model.set_rows(page.items)
            self.pagination.set_result(page.total, page.offset, page.limit)
            self.stack.setCurrentWidget(self.table if page.items else self.empty)
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add(self) -> None:
        dlg = MeetingDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Зустріч створено")
            self.reload()

    def _edit(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        dlg = MeetingDialog(self.gateway, meeting=rows[0], parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Оновлено")
            self.reload()

    def _complete(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        if not ConfirmDialog.ask(self, "Завершення", "Позначити зустріч завершеною?"):
            return
        try:
            call(self.gateway.c.meetings.complete, rows[0].id)
            if self.toast:
                self.toast.success("Завершено")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _cancel(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        if not ConfirmDialog.ask(self, "Скасування", "Скасувати зустріч?", danger=True):
            return
        try:
            call(self.gateway.c.meetings.cancel, rows[0].id)
            if self.toast:
                self.toast.success("Скасовано")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _on_sel(self, rows: list) -> None:
        one = len(rows) == 1
        self.btn_edit.setEnabled(one)
        self.btn_complete.setEnabled(one)
        self.btn_cancel.setEnabled(one)

    def _page(self, offset: int) -> None:
        self._offset = offset
        self.reload()
