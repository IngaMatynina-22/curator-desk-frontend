from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.core.exceptions import AppError
from app.schemas.curator_log import CuratorLogFilter

from gui.gateway import call, user_message
from gui.ui.dialogs.curator_log_dialog import CuratorLogDialog, CAT_UA
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.empty_state import EmptyState
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.filter_panel import FilterPanel
from gui.ui.widgets.pagination import PaginationControls
from gui.ui.widgets.timeline_widget import TimelineView

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class CuratorLogPage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast
        self._offset = 0

        root = QVBoxLayout(self)
        row = QHBoxLayout()
        title = QLabel("Журнал куратора")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        row.addStretch()
        self.btn_add = QPushButton("Новий запис")
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
        self.filters = FilterPanel(search_placeholder="Пошук у журналі…")
        self.filters.search_changed.connect(lambda _: self.reload())
        self.filters.refresh_requested.connect(self.reload)
        self.filters.cleared.connect(self._clear)
        root.addWidget(self.filters)

        body = QHBoxLayout()
        self.stack = QStackedWidget()
        self.table = DataTableView()
        self.model = DataTableModel(
            [
                ("Дата", "occurred_at", lambda v: str(v)),
                ("Категорія", "category", lambda v: CAT_UA.get(v, v)),
                ("Заголовок", "title", None),
                ("Результат", "result", lambda v: v or "—"),
            ]
        )
        self.table.setModel(self.model)
        self.table.selection_changed_rows.connect(lambda rows: self.btn_edit.setEnabled(len(rows) == 1))
        self.table.row_activated.connect(lambda _: self._edit())
        self.empty = EmptyState("Журнал порожній", "Додайте перший запис кураторської роботи.", "Новий запис")
        self.empty.action_clicked.connect(self._add)
        self.stack.addWidget(self.table)
        self.stack.addWidget(self.empty)
        body.addWidget(self.stack, stretch=2)
        self.feed = TimelineView()
        body.addWidget(self.feed, stretch=1)
        root.addLayout(body, stretch=1)
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
                self.gateway.c.curator_logs.list,
                CuratorLogFilter(
                    query=self.filters.search.text().strip() or None,
                    offset=self._offset,
                    limit=50,
                ),
            )
            self.model.set_rows(page.items)
            self.pagination.set_result(page.total, page.offset, page.limit)
            self.stack.setCurrentWidget(self.table if page.items else self.empty)
            # feed as timeline-like objects
            feed_items = []
            for e in page.items:
                feed_items.append(
                    type(
                        "T",
                        (),
                        {
                            "kind": "curator_log",
                            "title": e.title,
                            "summary": e.description[:200] if e.description else None,
                            "status": e.category,
                            "occurred_at": e.occurred_at,
                        },
                    )()
                )
            self.feed.set_items(feed_items)
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add(self) -> None:
        dlg = CuratorLogDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Запис додано")
            self.reload()

    def _edit(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        dlg = CuratorLogDialog(self.gateway, entry=rows[0], parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Оновлено")
            self.reload()

    def _page(self, offset: int) -> None:
        self._offset = offset
        self.reload()

    def _clear(self) -> None:
        self.filters.search.clear()
        self._offset = 0
        self.reload()
