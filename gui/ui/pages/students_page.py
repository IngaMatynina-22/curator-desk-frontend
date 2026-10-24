from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import user_message
from gui.ui.controllers.students_controller import StudentsController
from gui.ui.dialogs.confirm_dialog import ConfirmDialog
from gui.ui.dialogs.group_dialog import GroupDialog
from gui.ui.dialogs.preview_dialog import PreviewDialog
from gui.ui.dialogs.student_dialog import StudentDialog
from gui.ui.labels import STUDENT_STATUS, label
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.empty_state import EmptyState
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.filter_panel import FilterPanel
from gui.ui.widgets.pagination import PaginationControls

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class StudentsPage(QWidget):
    def __init__(
        self,
        gateway: BackendGateway,
        *,
        toast: ToastManager | None = None,
        open_details: Callable[[int], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.controller = StudentsController(gateway)
        self.toast = toast
        self.open_details = open_details
        self._offset = 0
        self._limit = 50
        self._group_names: dict[int, str] = {}

        root = QVBoxLayout(self)
        title_row = QHBoxLayout()
        title = QLabel("Студенти")
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        self.btn_add = QPushButton("Додати студента")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self.create_student)
        self.btn_group = QPushButton("Нова група")
        self.btn_group.clicked.connect(self.create_group)
        self.btn_edit = QPushButton("Редагувати")
        self.btn_edit.clicked.connect(self.edit_selected)
        self.btn_archive = QPushButton("Архівувати")
        self.btn_archive.clicked.connect(self.archive_selected)
        self.btn_restore = QPushButton("Відновити")
        self.btn_restore.clicked.connect(self.restore_selected)
        self.btn_export = QPushButton("Експорт")
        self.btn_export.clicked.connect(self.export_list)
        for b in (
            self.btn_add,
            self.btn_group,
            self.btn_edit,
            self.btn_archive,
            self.btn_restore,
            self.btn_export,
        ):
            title_row.addWidget(b)
        root.addLayout(title_row)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        self.filters = FilterPanel(search_placeholder="Пошук за ПІБ або номером…")
        self.group_filter = QComboBox()
        self.group_filter.addItem("Усі групи", None)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Усі статуси", None)
        for key, text in STUDENT_STATUS.items():
            self.status_filter.addItem(text, key)
        self.archived_cb = QCheckBox("Показувати архів")
        self.filters.add_filter_widget("Група", self.group_filter)
        self.filters.add_filter_widget("Статус", self.status_filter)
        self.filters.add_filter_widget("", self.archived_cb)
        self.filters.search_changed.connect(lambda _t: self.reload())
        self.filters.cleared.connect(self._clear_filters)
        self.filters.refresh_requested.connect(self.reload)
        self.group_filter.currentIndexChanged.connect(lambda _i: self.reload())
        self.status_filter.currentIndexChanged.connect(lambda _i: self.reload())
        self.archived_cb.toggled.connect(lambda _v: self.reload())
        root.addWidget(self.filters)

        self.stack = QStackedWidget()
        self.table = DataTableView()
        self.model = DataTableModel(
            [
                ("ПІБ", "full_name", None),
                ("Група", "group_id", self._fmt_group),
                ("Номер", "student_number", None),
                ("Курс", "course", lambda v: "—" if v is None else str(v)),
                ("Статус", "status", lambda v: label(STUDENT_STATUS, v)),
                ("Архів", "is_archived", lambda v: "Так" if v else "Ні"),
            ]
        )
        self.table.setModel(self.model)
        self.table.row_activated.connect(self._on_activated)
        self.table.selection_changed_rows.connect(self._on_selection)
        self.empty = EmptyState(
            title="Студентів не знайдено",
            description="Додайте першого студента або змініть умови фільтрації.",
            action_text="Додати студента",
        )
        self.empty.action_clicked.connect(self.create_student)
        self.stack.addWidget(self.table)
        self.stack.addWidget(self.empty)
        root.addWidget(self.stack, stretch=1)

        self.pagination = PaginationControls(self._limit)
        self.pagination.page_changed.connect(self._on_page)
        root.addWidget(self.pagination)

        self._update_actions([])

    def focus_search(self) -> None:
        self.filters.search.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def create_new(self) -> None:
        self.create_student()

    def refresh(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.error.clear()
        try:
            self._group_names = self.controller.group_name_map()
            self._reload_group_combo()
            page = self.controller.list_students(
                query=self.filters.search.text().strip() or None,
                group_id=self.group_filter.currentData(),
                status=self.status_filter.currentData(),
                include_archived=self.archived_cb.isChecked(),
                offset=self._offset,
                limit=self._limit,
            )
            rows = []
            for s in page.items:
                if not s.full_name:
                    s.full_name = " ".join(
                        p for p in (s.last_name, s.first_name, s.middle_name) if p
                    )
                rows.append(s)
            self.model.set_rows(rows)
            self.pagination.set_result(page.total, page.offset, page.limit)
            self.stack.setCurrentWidget(self.table if rows else self.empty)
            if not rows and (
                self.filters.search.text()
                or self.group_filter.currentData()
                or self.status_filter.currentData()
            ):
                self.empty.configure(
                    "Нічого не знайдено",
                    "Спробуйте змінити фільтри або очистити умови пошуку.",
                    "Очистити фільтри",
                )
                try:
                    self.empty.action_clicked.disconnect()
                except TypeError:
                    pass
                self.empty.action_clicked.connect(self._clear_filters)
            else:
                self.empty.configure(
                    "Студентів ще немає",
                    "Створіть картку студента, щоб почати роботу з групою.",
                    "Додати студента",
                )
                try:
                    self.empty.action_clicked.disconnect()
                except TypeError:
                    pass
                self.empty.action_clicked.connect(self.create_student)
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def create_student(self) -> None:
        dlg = StudentDialog(
            self.gateway,
            default_group_id=self.group_filter.currentData(),
            parent=self,
        )
        if dlg.exec() and dlg.saved_student and self.toast:
            self.toast.success("Студента збережено")
            self.reload()

    def create_group(self) -> None:
        dlg = GroupDialog(self.gateway, parent=self)
        if dlg.exec() and dlg.saved_group:
            if self.toast:
                self.toast.success(f"Групу «{dlg.saved_group.name}» створено")
            self.reload()

    def edit_selected(self) -> None:
        rows = self.table.selected_rows()
        if len(rows) != 1:
            return
        dlg = StudentDialog(self.gateway, student=rows[0], parent=self)
        if dlg.exec() and dlg.saved_student:
            if self.toast:
                self.toast.success("Зміни збережено")
            self.reload()

    def archive_selected(self) -> None:
        rows = [r for r in self.table.selected_rows() if not r.is_archived]
        if not rows:
            return
        ids = [r.id for r in rows]
        try:
            preview = self.controller.preview_archive(ids)
        except AppError as exc:
            self.error.show_error(user_message(exc))
            return
        planned = preview.applied or len(preview.details)
        summary = (
            f"Буде архівовано: {planned}, пропущено: {preview.skipped}."
        )
        dlg = PreviewDialog(
            "Попередній перегляд архівування",
            summary,
            details=preview.details,
            warnings=preview.warnings or preview.errors,
            parent=self,
        )
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        if not ConfirmDialog.ask(
            self,
            "Підтвердження",
            "Архівувати вибраних студентів? Записи залишаться в архіві.",
            confirm_text="Архівувати",
            danger=True,
        ):
            return
        try:
            result = self.controller.apply_archive(ids)
            if self.toast:
                self.toast.success(f"Архівовано: {result.applied}")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def restore_selected(self) -> None:
        rows = [r for r in self.table.selected_rows() if r.is_archived]
        if not rows:
            return
        if not ConfirmDialog.ask(
            self,
            "Відновлення",
            f"Відновити {len(rows)} студент(ів) з архіву?",
            confirm_text="Відновити",
        ):
            return
        try:
            for r in rows:
                self.controller.restore(r.id)
            if self.toast:
                self.toast.success("Відновлено")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def export_list(self) -> None:
        try:
            result = self.controller.export_students(
                group_id=self.group_filter.currentData(),
                fmt="csv",
            )
            path = str(result.path)
            if self.toast:
                self.toast.success(f"Експортовано {result.rows} записів: {path}")
            else:
                QMessageBox.information(self, "Експорт", f"Файл збережено:\n{path}")
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _on_activated(self, student) -> None:
        if self.open_details:
            self.open_details(student.id)

    def _on_selection(self, rows: list) -> None:
        self._update_actions(rows)

    def _update_actions(self, rows: list) -> None:
        one = len(rows) == 1
        any_active = any(not r.is_archived for r in rows)
        any_arch = any(r.is_archived for r in rows)
        self.btn_edit.setEnabled(one)
        self.btn_archive.setEnabled(any_active)
        self.btn_restore.setEnabled(any_arch)

    def _on_page(self, offset: int) -> None:
        self._offset = offset
        self.reload()

    def _clear_filters(self) -> None:
        self.filters.search.clear()
        self.group_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.archived_cb.setChecked(False)
        self._offset = 0
        self.reload()

    def _reload_group_combo(self) -> None:
        current = self.group_filter.currentData()
        self.group_filter.blockSignals(True)
        self.group_filter.clear()
        self.group_filter.addItem("Усі групи", None)
        for gid, name in sorted(self._group_names.items(), key=lambda x: x[1]):
            self.group_filter.addItem(name, gid)
        if current is not None:
            idx = self.group_filter.findData(current)
            if idx >= 0:
                self.group_filter.setCurrentIndex(idx)
        self.group_filter.blockSignals(False)

    def _fmt_group(self, group_id: int | None) -> str:
        if group_id is None:
            return "—"
        return self._group_names.get(group_id, str(group_id))
