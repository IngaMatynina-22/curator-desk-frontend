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

from app.core.exceptions import AppError

from gui.gateway import user_message
from gui.ui.controllers.attendance_controller import AttendanceController
from gui.ui.dialogs.attendance_edit_dialog import AttendanceEditDialog
from gui.ui.dialogs.bulk_attendance_dialog import BulkAttendanceDialog
from gui.ui.labels import ATTENDANCE_STATUS, label
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.empty_state import EmptyState
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.filter_panel import FilterPanel
from gui.ui.widgets.pagination import PaginationControls

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class AttendancePage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast
        self.ctrl = AttendanceController(gateway)
        self._offset = 0
        self._limit = 100
        self._names: dict[int, str] = {}
        self._subjects: dict[int, str] = {}

        root = QVBoxLayout(self)
        title_row = QHBoxLayout()
        title = QLabel("Відвідуваність")
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        self.btn_bulk = QPushButton("Масова відмітка")
        self.btn_bulk.setObjectName("primaryButton")
        self.btn_bulk.clicked.connect(self._bulk)
        self.btn_edit = QPushButton("Редагувати")
        self.btn_edit.clicked.connect(self._edit)
        self.btn_edit.setEnabled(False)
        title_row.addWidget(self.btn_bulk)
        title_row.addWidget(self.btn_edit)
        root.addLayout(title_row)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        self.filters = FilterPanel(search_placeholder="(фільтри нижче)")
        self.filters.search.hide()
        self.status_filter = QComboBox()
        self.status_filter.addItem("Усі статуси", None)
        for k, t in ATTENDANCE_STATUS.items():
            self.status_filter.addItem(t, k)
        self.subject_filter = QComboBox()
        self.subject_filter.addItem("Усі дисципліни", None)
        self.filters.add_filter_widget("Статус", self.status_filter)
        self.filters.add_filter_widget("Дисципліна", self.subject_filter)
        self.filters.cleared.connect(self._clear)
        self.filters.refresh_requested.connect(self.reload)
        self.status_filter.currentIndexChanged.connect(lambda _: self.reload())
        self.subject_filter.currentIndexChanged.connect(lambda _: self.reload())
        root.addWidget(self.filters)

        self.summary = QLabel()
        root.addWidget(self.summary)

        self.stack = QStackedWidget()
        self.table = DataTableView()
        self.model = DataTableModel(
            [
                ("Студент", "student_id", lambda v: self._names.get(v, str(v))),
                ("Заняття", "lesson_id", str),
                ("Статус", "status", lambda v: label(ATTENDANCE_STATUS, v)),
                ("Годин", "hours_missed", lambda v: str(v)),
                ("Причина", "reason", lambda v: v or "—"),
            ]
        )
        self.table.setModel(self.model)
        self.table.selection_changed_rows.connect(self._on_sel)
        self.table.row_activated.connect(lambda r: self._edit())
        self.empty = EmptyState(
            "Немає відміток",
            "Створіть заняття та зробіть масову відмітку групи.",
            "Масова відмітка",
        )
        self.empty.action_clicked.connect(self._bulk)
        self.stack.addWidget(self.table)
        self.stack.addWidget(self.empty)
        root.addWidget(self.stack, stretch=1)

        self.pagination = PaginationControls(self._limit)
        self.pagination.page_changed.connect(self._page)
        root.addWidget(self.pagination)

    def refresh(self) -> None:
        self.reload()

    def create_new(self) -> None:
        self._bulk()

    def reload(self) -> None:
        self.error.clear()
        try:
            self._names = self.ctrl.student_name_map()
            subjects = self.ctrl.list_subjects()
            self._subjects = {s.id: s.name for s in subjects}
            cur = self.subject_filter.currentData()
            self.subject_filter.blockSignals(True)
            self.subject_filter.clear()
            self.subject_filter.addItem("Усі дисципліни", None)
            for s in subjects:
                self.subject_filter.addItem(s.name, s.id)
            if cur is not None:
                i = self.subject_filter.findData(cur)
                if i >= 0:
                    self.subject_filter.setCurrentIndex(i)
            self.subject_filter.blockSignals(False)

            page = self.ctrl.list_records(
                subject_id=self.subject_filter.currentData(),
                status=self.status_filter.currentData(),
                offset=self._offset,
                limit=self._limit,
            )
            self.model.set_rows(page.items)
            self.pagination.set_result(page.total, page.offset, page.limit)
            self.stack.setCurrentWidget(self.table if page.items else self.empty)

            top = self.ctrl.top_absentees(5)
            if top:
                parts = []
                for row in top:
                    # may be dict or object
                    if isinstance(row, dict):
                        sid = row.get("student_id")
                        absences = row.get("absences", row.get("count", "?"))
                    else:
                        sid = getattr(row, "student_id", None)
                        absences = getattr(row, "absences", getattr(row, "count", "?"))
                    parts.append(f"{self._names.get(sid, sid)}: {absences}")
                self.summary.setText("Топ пропусків: " + "; ".join(parts))
            else:
                self.summary.setText("")
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _bulk(self) -> None:
        dlg = BulkAttendanceDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Відмітки збережено")
            self.reload()

    def _edit(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        dlg = AttendanceEditDialog(self.gateway, rows[0], parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Відмітку оновлено")
            self.reload()

    def _on_sel(self, rows: list) -> None:
        self.btn_edit.setEnabled(len(rows) == 1)

    def _page(self, offset: int) -> None:
        self._offset = offset
        self.reload()

    def _clear(self) -> None:
        self.status_filter.setCurrentIndex(0)
        self.subject_filter.setCurrentIndex(0)
        self._offset = 0
        self.reload()
