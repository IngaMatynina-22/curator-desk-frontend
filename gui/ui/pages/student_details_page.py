from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import user_message
from gui.ui.controllers.students_controller import StudentsController
from gui.ui.dialogs.confirm_dialog import ConfirmDialog
from gui.ui.dialogs.student_dialog import StudentDialog
from gui.gateway import call
from gui.ui.labels import ATTENDANCE_STATUS, STUDENT_STATUS, STUDY_FORM, label
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.info_grid import InfoGrid
from gui.ui.widgets.status_badge import StatusBadge
from gui.ui.widgets.timeline_widget import TimelineView

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class StudentDetailsPage(QWidget):
    def __init__(
        self,
        gateway: BackendGateway,
        *,
        toast: ToastManager | None = None,
        on_back: Callable[[], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.controller = StudentsController(gateway)
        self.toast = toast
        self.on_back = on_back
        self._student_id: int | None = None
        self._timeline_loaded = False

        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.btn_back = QPushButton("← До списку")
        self.btn_back.clicked.connect(self._go_back)
        top.addWidget(self.btn_back)
        top.addStretch()
        self.btn_edit = QPushButton("Редагувати")
        self.btn_edit.clicked.connect(self._edit)
        self.btn_archive = QPushButton("Архівувати")
        self.btn_archive.clicked.connect(self._archive)
        self.btn_restore = QPushButton("Відновити")
        self.btn_restore.clicked.connect(self._restore)
        top.addWidget(self.btn_edit)
        top.addWidget(self.btn_archive)
        top.addWidget(self.btn_restore)
        root.addLayout(top)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        self.header = QLabel("Картка студента")
        self.header.setObjectName("pageTitle")
        root.addWidget(self.header)

        meta = QHBoxLayout()
        self.meta_label = QLabel()
        self.status_badge = StatusBadge()
        meta.addWidget(self.meta_label)
        meta.addWidget(self.status_badge)
        meta.addStretch()
        root.addLayout(meta)

        self.tabs = QTabWidget()

        # Personal — paper info grid
        self.personal = QWidget()
        personal_lay = QVBoxLayout(self.personal)
        personal_lay.setContentsMargins(8, 8, 8, 8)
        self.info_grid = InfoGrid("Особисті дані")
        for key, title in [
            ("full_name", "ПІБ"),
            ("student_number", "Навчальний номер"),
            ("group", "Група"),
            ("course", "Курс"),
            ("specialty", "Спеціальність"),
            ("study_form", "Форма навчання"),
            ("phone", "Телефон"),
            ("email", "Email"),
            ("address", "Адреса"),
            ("birth_date", "Дата народження"),
            ("enrollment_date", "Дата зарахування"),
            ("personal_notes", "Нотатки"),
        ]:
            self.info_grid.add_field(key, title)
        personal_lay.addWidget(self.info_grid)
        personal_lay.addStretch()
        self.tabs.addTab(self.personal, "Особисті дані")

        self.learning = QWidget()
        learn_lay = QVBoxLayout(self.learning)
        self.summary_labels = {
            "absences": QLabel("Пропуски: —"),
            "excused": QLabel("Поважні: —"),
            "assignments": QLabel("Активні доручення: —"),
            "events": QLabel("Заходи: —"),
            "meetings": QLabel("Зустрічі: —"),
            "average": QLabel("Середній бал: —"),
        }
        for w in self.summary_labels.values():
            learn_lay.addWidget(w)
        self.academic_table = DataTableView()
        self.academic_model = DataTableModel(
            [
                ("Дата", "record_date", lambda v: str(v)),
                ("Дисципліна", "subject_id", str),
                ("Шкала", "grade_scale", None),
                ("Бал", "score", lambda v: "—" if v is None else str(v)),
                ("Результат", "text_result", lambda v: v or "—"),
            ]
        )
        self.academic_table.setModel(self.academic_model)
        learn_lay.addWidget(self.academic_table, stretch=1)
        self.tabs.addTab(self.learning, "Навчання")

        self.attendance_tab = QWidget()
        att_lay = QVBoxLayout(self.attendance_tab)
        self.att_stats = QLabel("Статистика: —")
        att_lay.addWidget(self.att_stats)
        self.att_table = DataTableView()
        self.att_model = DataTableModel(
            [
                ("Заняття", "lesson_id", str),
                ("Статус", "status", lambda v: label(ATTENDANCE_STATUS, v)),
                ("Годин", "hours_missed", lambda v: str(v)),
                ("Причина", "reason", lambda v: v or "—"),
            ]
        )
        self.att_table.setModel(self.att_model)
        att_lay.addWidget(self.att_table, stretch=1)
        self.tabs.addTab(self.attendance_tab, "Відвідуваність")

        self.assignments_tab = QWidget()
        asg_lay = QVBoxLayout(self.assignments_tab)
        self.asg_table = DataTableView()
        self.asg_model = DataTableModel(
            [
                ("Назва", "title", None),
                ("Строк", "due_date", lambda v: str(v)),
                ("Статус", "status", None),
                ("Прострочено", "is_overdue", lambda v: "Так" if v else "Ні"),
            ]
        )
        self.asg_table.setModel(self.asg_model)
        asg_lay.addWidget(self.asg_table, stretch=1)
        self.tabs.addTab(self.assignments_tab, "Доручення")

        self.timeline = TimelineView()
        self.tabs.addTab(self.timeline, "Хронологія")
        self.tabs.currentChanged.connect(self._on_tab)
        self._lazy_loaded: set[str] = set()

        root.addWidget(self.tabs, stretch=1)

    def load_student(self, student_id: int) -> None:
        self._student_id = student_id
        self._timeline_loaded = False
        self._lazy_loaded = set()
        self.tabs.setCurrentIndex(0)
        self.refresh()

    def refresh(self) -> None:
        if self._student_id is None:
            return
        self.error.clear()
        try:
            student = self.controller.get(self._student_id)
            groups = self.controller.group_name_map()
            full = student.full_name or f"{student.last_name} {student.first_name}".strip()
            self.header.setText(full)
            self.meta_label.setText(
                f"№ {student.student_number} · "
                f"{groups.get(student.group_id, 'група ?')} · "
                f"{'архів' if student.is_archived else 'активний'}"
            )
            self.status_badge.set_status(
                label(STUDENT_STATUS, student.status), student.status
            )
            self.info_grid.set_value("full_name", full)
            self.info_grid.set_value("student_number", student.student_number)
            self.info_grid.set_value("group", groups.get(student.group_id, str(student.group_id)))
            self.info_grid.set_value(
                "course",
                "—" if student.course is None else str(student.course),
            )
            self.info_grid.set_value("specialty", student.specialty or "—")
            self.info_grid.set_value("study_form", label(STUDY_FORM, student.study_form))
            self.info_grid.set_value("phone", student.phone or "—")
            self.info_grid.set_value("email", student.email or "—")
            self.info_grid.set_value("address", student.address or "—")
            self.info_grid.set_value(
                "birth_date",
                student.birth_date.isoformat() if student.birth_date else "—",
            )
            self.info_grid.set_value(
                "enrollment_date",
                student.enrollment_date.isoformat() if student.enrollment_date else "—",
            )
            self.info_grid.set_value("personal_notes", student.personal_notes or "—")

            self.btn_archive.setVisible(not student.is_archived)
            self.btn_restore.setVisible(student.is_archived)
            self.btn_edit.setEnabled(not student.is_archived)

            summary = self.controller.summary(self._student_id)
            self.summary_labels["absences"].setText(
                f"Пропуски: {summary.attendance_absences}"
            )
            self.summary_labels["excused"].setText(
                f"Поважні: {summary.attendance_excused}"
            )
            self.summary_labels["assignments"].setText(
                f"Активні доручення: {summary.open_assignments}"
            )
            self.summary_labels["events"].setText(f"Заходи: {summary.events_count}")
            self.summary_labels["meetings"].setText(f"Зустрічі: {summary.meetings_count}")
            avg = call(self.gateway.c.academic.average_for_student, self._student_id)
            self.summary_labels["average"].setText(
                f"Середній бал: {avg if avg is not None else '—'}"
            )

            self._on_tab(self.tabs.currentIndex())
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _on_tab(self, index: int) -> None:
        if self._student_id is None:
            return
        widget = self.tabs.widget(index)
        if widget is self.timeline and not self._timeline_loaded:
            self._load_timeline()
        elif widget is self.learning and "academic" not in self._lazy_loaded:
            self._load_academic()
        elif widget is self.attendance_tab and "attendance" not in self._lazy_loaded:
            self._load_attendance()
        elif widget is self.assignments_tab and "assignments" not in self._lazy_loaded:
            self._load_assignments()

    def _load_academic(self) -> None:
        try:
            page = call(
                self.gateway.c.academic.list_records,
                {"student_id": self._student_id, "limit": 100},
            )
            self.academic_model.set_rows(page.items)
            self._lazy_loaded.add("academic")
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _load_attendance(self) -> None:
        try:
            stats = call(self.gateway.c.attendance.student_stats, self._student_id)
            self.att_stats.setText(
                f"Пропуски: {stats.absences}, поважні: {stats.excused}, "
                f"запізнення: {stats.late}, годин: {stats.hours_missed}"
            )
            page = call(
                self.gateway.c.attendance.list,
                {"student_id": self._student_id, "limit": 100},
            )
            self.att_model.set_rows(page.items)
            self._lazy_loaded.add("attendance")
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _load_assignments(self) -> None:
        try:
            page = call(
                self.gateway.c.assignments.list,
                {"student_id": self._student_id, "limit": 100},
            )
            self.asg_model.set_rows(page.items)
            self._lazy_loaded.add("assignments")
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _load_timeline(self) -> None:
        if self._student_id is None:
            return
        try:
            page = self.controller.timeline(self._student_id, limit=100)
            self.timeline.set_items(page.items)
            self._timeline_loaded = True
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _edit(self) -> None:
        if self._student_id is None:
            return
        student = self.controller.get(self._student_id)
        dlg = StudentDialog(self.gateway, student=student, parent=self)
        if dlg.exec() and dlg.saved_student:
            if self.toast:
                self.toast.success("Картку оновлено")
            self.refresh()

    def _archive(self) -> None:
        if self._student_id is None:
            return
        if not ConfirmDialog.ask(
            self,
            "Архівування",
            "Архівувати цього студента?",
            confirm_text="Архівувати",
            danger=True,
        ):
            return
        try:
            self.controller.archive(self._student_id)
            if self.toast:
                self.toast.success("Студента архівовано")
            self.refresh()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _restore(self) -> None:
        if self._student_id is None:
            return
        try:
            self.controller.restore(self._student_id)
            if self.toast:
                self.toast.success("Студента відновлено")
            self.refresh()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _go_back(self) -> None:
        if self.on_back:
            self.on_back()
