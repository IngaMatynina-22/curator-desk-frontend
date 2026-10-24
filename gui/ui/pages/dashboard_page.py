from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import call, user_message
from gui.ui.dialogs.assignment_dialog import AssignmentDialog
from gui.ui.icons import icon
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.kanban_board import KanbanBoard
from gui.ui.widgets.page_scroll import PageScroll

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class DashboardPage(QWidget):
    def __init__(
        self,
        gateway: BackendGateway,
        *,
        toast: ToastManager | None = None,
        navigate: Callable[[str], None] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast
        self.navigate = navigate

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = PageScroll()
        outer.addWidget(scroll)
        root = scroll.body_layout
        root.setSpacing(16)

        title = QLabel("Огляд дня")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        self.error = ErrorBanner()
        root.addWidget(self.error)

        self.kpi = QGridLayout()
        self.kpi.setSpacing(12)
        self.kpi_labels: dict[str, QLabel] = {}
        for i, (key, caption, ikey) in enumerate(
            [
                ("students", "Активні студенти", "users"),
                ("today", "Справи сьогодні", "today"),
                ("overdue", "Прострочено", "overdue"),
                ("unread", "Непрочитані", "unread"),
            ]
        ):
            box = QFrame()
            box.setObjectName("kpiPanel")
            lay = QHBoxLayout(box)
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(12)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon(ikey, color="#1A7A6D", size=28).pixmap(28, 28))
            lay.addWidget(icon_lbl)
            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            cap = QLabel(caption)
            cap.setObjectName("kpiCaption")
            val = QLabel("—")
            val.setObjectName("kpiValue")
            text_col.addWidget(cap)
            text_col.addWidget(val)
            lay.addLayout(text_col, stretch=1)
            self.kpi_labels[key] = val
            box.mousePressEvent = lambda e, k=key: self._kpi_click(k)  # type: ignore[method-assign]
            self.kpi.addWidget(box, 0, i)
        root.addLayout(self.kpi)

        quick = QHBoxLayout()
        quick.setSpacing(8)
        for text, target in [
            ("Студенти", "students"),
            ("Відвідуваність", "attendance"),
            ("Доручення", "assignments"),
            ("Календар", "calendar"),
        ]:
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, t=target: self._go(t))
            quick.addWidget(b)
        quick.addStretch()
        root.addLayout(quick)

        self.board = KanbanBoard(
            [
                ("new", "Нові"),
                ("in_progress", "В роботі"),
                ("overdue", "Прострочені"),
            ]
        )
        self.board.setMinimumHeight(320)
        self.board.add_requested.connect(self._add_assignment)
        self.board.card_activated.connect(self._edit_assignment)
        root.addWidget(self.board)

        recent_head = QLabel("Останні дії")
        recent_head.setObjectName("pageTitle")
        recent_head.setStyleSheet("font-size: 16px;")
        root.addWidget(recent_head)
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(120)
        root.addWidget(self.recent_list)

    def refresh(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.error.clear()
        try:
            students = call(self.gateway.c.students.list, {"limit": 1})
            self.kpi_labels["students"].setText(str(students.total))

            agenda = call(self.gateway.c.calendar.get_agenda, "day")
            items = agenda.get("items") or []
            self.kpi_labels["today"].setText(str(len(items)))

            overdue = call(self.gateway.c.assignments.overdue)
            self.kpi_labels["overdue"].setText(str(len(overdue)))
            unread = call(self.gateway.c.notifications.count_pending)
            self.kpi_labels["unread"].setText(str(unread))

            new_page = call(self.gateway.c.assignments.list, {"status": "new", "limit": 50})
            prog_page = call(
                self.gateway.c.assignments.list, {"status": "in_progress", "limit": 50}
            )
            overdue_ids = {a.id for a in overdue}
            self.board.set_column_items(
                "new",
                [a for a in new_page.items if a.id not in overdue_ids],
            )
            self.board.set_column_items(
                "in_progress",
                [a for a in prog_page.items if a.id not in overdue_ids],
            )
            self.board.set_column_items("overdue", list(overdue))

            self.recent_list.clear()
            for entry in call(self.gateway.c.audit.recent, 15):
                self.recent_list.addItem(
                    f"{getattr(entry, 'operation', '')} "
                    f"{getattr(entry, 'entity_type', '')}#{getattr(entry, 'entity_id', '')}"
                )
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add_assignment(self, _column_key: str = "") -> None:
        dlg = AssignmentDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Доручення створено")
            self.reload()

    def _edit_assignment(self, assignment) -> None:
        try:
            full = call(self.gateway.c.assignments.get, assignment.id)
        except AppError as exc:
            self.error.show_error(user_message(exc))
            return
        dlg = AssignmentDialog(self.gateway, assignment=full, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Доручення оновлено")
            self.reload()

    def _go(self, key: str) -> None:
        if self.navigate:
            self.navigate(key)

    def _kpi_click(self, key: str) -> None:
        mapping = {
            "students": "students",
            "today": "calendar",
            "overdue": "assignments",
            "unread": "notifications",
        }
        self._go(mapping.get(key, "dashboard"))
