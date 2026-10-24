from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.core.exceptions import AppError
from app.schemas.duty import DutyFilter

from gui.gateway import call, user_message
from gui.ui.dialogs.duty_dialog import DutyDialog
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.empty_state import EmptyState
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.filter_panel import FilterPanel
from gui.ui.widgets.pagination import PaginationControls

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class DutiesPage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast
        self._offset = 0

        root = QVBoxLayout(self)
        row = QHBoxLayout()
        title = QLabel("Чергування")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        row.addStretch()
        self.btn_add = QPushButton("Створити")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self._add)
        self.btn_edit = QPushButton("Редагувати")
        self.btn_edit.clicked.connect(self._edit)
        self.btn_edit.setEnabled(False)
        row.addWidget(self.btn_add)
        row.addWidget(self.btn_edit)
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
                ("Дата", "duty_date", lambda v: str(v)),
                ("Тип", "duty_type", lambda v: v or "—"),
                ("Місце", "location", lambda v: v or "—"),
                ("Статус", "status", None),
                ("Студенти", "student_ids", lambda v: str(len(v or []))),
            ]
        )
        self.table.setModel(self.model)
        self.table.selection_changed_rows.connect(lambda rows: self.btn_edit.setEnabled(len(rows) == 1))
        self.table.row_activated.connect(lambda _: self._edit())
        self.empty = EmptyState("Немає чергувань", "Створіть графік чергування.", "Створити")
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
            page = call(self.gateway.c.duties.list, DutyFilter(offset=self._offset, limit=50))
            self.model.set_rows(page.items)
            self.pagination.set_result(page.total, page.offset, page.limit)
            self.stack.setCurrentWidget(self.table if page.items else self.empty)
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add(self) -> None:
        dlg = DutyDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Чергування створено")
            self.reload()

    def _edit(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        dlg = DutyDialog(self.gateway, duty=rows[0], parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Оновлено")
            self.reload()

    def _page(self, offset: int) -> None:
        self._offset = offset
        self.reload()
