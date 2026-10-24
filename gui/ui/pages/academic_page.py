from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.core.exceptions import AppError

from gui.gateway import user_message
from gui.ui.controllers.academic_controller import AcademicController
from gui.ui.dialogs.academic_record_dialog import AcademicRecordDialog, SCALE_UA
from gui.ui.dialogs.subject_dialog import SubjectDialog
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.empty_state import EmptyState
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.filter_panel import FilterPanel
from gui.ui.widgets.pagination import PaginationControls

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class AcademicPage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast
        self.ctrl = AcademicController(gateway)
        self._offset = 0
        self._names: dict[int, str] = {}
        self._subjects: dict[int, str] = {}

        root = QVBoxLayout(self)
        row = QHBoxLayout()
        title = QLabel("Успішність")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        row.addStretch()
        for text, slot, primary in [
            ("Додати запис", self._add, True),
            ("Редагувати", self._edit, False),
            ("Дисципліни", self._subject, False),
        ]:
            b = QPushButton(text)
            if primary:
                b.setObjectName("primaryButton")
            b.clicked.connect(slot)
            row.addWidget(b)
            if text == "Редагувати":
                self.btn_edit = b
                b.setEnabled(False)
        root.addLayout(row)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        self.filters = FilterPanel()
        self.filters.search.hide()
        self.subject_filter = QComboBox()
        self.subject_filter.addItem("Усі дисципліни", None)
        self.scale_filter = QComboBox()
        self.scale_filter.addItem("Усі шкали", None)
        for k, t in SCALE_UA.items():
            self.scale_filter.addItem(t, k)
        self.filters.add_filter_widget("Дисципліна", self.subject_filter)
        self.filters.add_filter_widget("Шкала", self.scale_filter)
        self.filters.cleared.connect(self._clear)
        self.filters.refresh_requested.connect(self.reload)
        self.subject_filter.currentIndexChanged.connect(lambda _: self.reload())
        self.scale_filter.currentIndexChanged.connect(lambda _: self.reload())
        root.addWidget(self.filters)

        self.stack = QStackedWidget()
        self.table = DataTableView()
        self.model = DataTableModel(
            [
                ("Студент", "student_id", lambda v: self._names.get(v, str(v))),
                ("Дисципліна", "subject_id", lambda v: self._subjects.get(v, str(v))),
                ("Дата", "record_date", lambda v: str(v)),
                ("Шкала", "grade_scale", lambda v: SCALE_UA.get(v, v)),
                ("Бал", "score", lambda v: "—" if v is None else str(v)),
                ("Результат", "text_result", lambda v: v or "—"),
            ]
        )
        self.table.setModel(self.model)
        self.table.selection_changed_rows.connect(lambda rows: self.btn_edit.setEnabled(len(rows) == 1))
        self.table.row_activated.connect(lambda _: self._edit())
        self.empty = EmptyState("Немає записів", "Додайте оцінку або результат контролю.", "Додати запис")
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
                grade_scale=self.scale_filter.currentData(),
                offset=self._offset,
                limit=50,
            )
            self.model.set_rows(page.items)
            self.pagination.set_result(page.total, page.offset, page.limit)
            self.stack.setCurrentWidget(self.table if page.items else self.empty)
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add(self) -> None:
        dlg = AcademicRecordDialog(self.gateway, parent=self)
        if dlg.exec() and self.toast:
            self.toast.success("Запис збережено")
            self.reload()
        elif dlg.saved:
            self.reload()

    def _edit(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        dlg = AcademicRecordDialog(self.gateway, record=rows[0], parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Оновлено")
            self.reload()

    def _subject(self) -> None:
        dlg = SubjectDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Дисципліну збережено")
            self.reload()

    def _page(self, offset: int) -> None:
        self._offset = offset
        self.reload()

    def _clear(self) -> None:
        self.subject_filter.setCurrentIndex(0)
        self.scale_filter.setCurrentIndex(0)
        self._offset = 0
        self.reload()
