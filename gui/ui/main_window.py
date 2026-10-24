from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.container import ServiceContainer
from app.core.exceptions import AppError
from app.schemas.auth import UserOut

from gui.gateway import BackendGateway, call, user_message
from gui.ui.navigation import NavigationList
from gui.ui.pages.academic_page import AcademicPage
from gui.ui.pages.analytics_page import AnalyticsPage
from gui.ui.pages.archive_page import ArchivePage
from gui.ui.pages.assignments_page import AssignmentsPage
from gui.ui.pages.attendance_page import AttendancePage
from gui.ui.pages.calendar_page import CalendarPage
from gui.ui.pages.curator_log_page import CuratorLogPage
from gui.ui.pages.dashboard_page import DashboardPage
from gui.ui.pages.duties_page import DutiesPage
from gui.ui.pages.meetings_page import MeetingsPage
from gui.ui.pages.notifications_page import NotificationsPage
from gui.ui.pages.reports_page import ReportsPage
from gui.ui.pages.settings_page import SettingsPage
from gui.ui.pages.student_details_page import StudentDetailsPage
from gui.ui.pages.students_page import StudentsPage
from gui.ui.theme import load_saved_theme, toggle_theme
from gui.ui.widgets.pattern_backdrop import PatternBackdrop
from gui.ui.widgets.toast import ToastManager


class MainWindow(QMainWindow):
    def __init__(
        self,
        container: ServiceContainer,
        *,
        on_logout: Callable[[], None] | None = None,
        current_user: UserOut | None = None,
    ) -> None:
        super().__init__()
        self.container = container
        self.gateway = BackendGateway(container)
        self._on_logout = on_logout
        self.current_user = current_user or call(container.auth.current_user)
        self.setWindowTitle("CuratorDesk")
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)

        canvas = PatternBackdrop(self)
        theme = load_saved_theme(container)
        if theme == "dark":
            canvas.set_grid_color("#E8EEF1", 0.05)
        else:
            canvas.set_grid_color("#0C2A35", 0.07)
        self._canvas = canvas
        self.setCentralWidget(canvas)

        outer = QHBoxLayout(canvas)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Ink sidebar with accent rail
        side_wrap = QHBoxLayout()
        side_wrap.setContentsMargins(0, 0, 0, 0)
        side_wrap.setSpacing(0)

        rail = QFrame()
        rail.setObjectName("brandRail")
        rail.setFixedWidth(4)
        side_wrap.addWidget(rail)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(248)
        side_lay = QVBoxLayout(sidebar)
        side_lay.setContentsMargins(16, 24, 12, 16)
        side_lay.setSpacing(4)

        brand = QLabel("CuratorDesk")
        brand.setObjectName("sidebarBrand")
        side_lay.addWidget(brand)
        sub = QLabel("Кураторська панель")
        sub.setObjectName("sidebarSub")
        side_lay.addWidget(sub)
        side_lay.addSpacing(16)

        self.nav = NavigationList()
        self.nav.navigated.connect(self._on_navigate)
        side_lay.addWidget(self.nav, stretch=1)
        side_wrap.addWidget(sidebar)

        side_host = QWidget()
        side_host.setLayout(side_wrap)
        outer.addWidget(side_host)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        top = QFrame()
        top.setObjectName("topBar")
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(20, 12, 20, 12)
        top_lay.setSpacing(12)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Глобальний пошук (Ctrl+F)…")
        self.search.returnPressed.connect(self._global_search)
        top_lay.addWidget(self.search, stretch=1)

        name = (
            self.current_user.full_name
            if self.current_user is not None
            else "Користувач"
        )
        self.user_label = QLabel(name)
        self.user_label.setObjectName("mutedLabel")
        top_lay.addWidget(self.user_label)

        self.theme_btn = QPushButton("Темна" if theme == "light" else "Світла")
        self.theme_btn.setObjectName("ghostButton")
        self.theme_btn.setToolTip("Перемкнути світлу / темну тему")
        self.theme_btn.clicked.connect(self._toggle_theme)
        top_lay.addWidget(self.theme_btn)

        self.notif_btn = QPushButton("Сповіщення (0)")
        self.notif_btn.setObjectName("ghostButton")
        self.notif_btn.clicked.connect(lambda: self.nav.select_key("notifications"))
        top_lay.addWidget(self.notif_btn)

        self.logout_btn = QPushButton("Вийти")
        self.logout_btn.setObjectName("ghostButton")
        self.logout_btn.clicked.connect(self._logout)
        top_lay.addWidget(self.logout_btn)
        right.addWidget(top)

        workspace = QFrame()
        workspace.setObjectName("workspace")
        ws_lay = QVBoxLayout(workspace)
        ws_lay.setContentsMargins(24, 20, 24, 20)
        ws_lay.setSpacing(0)

        self.stack = QStackedWidget()
        ws_lay.addWidget(self.stack, stretch=1)
        right.addWidget(workspace, stretch=1)
        outer.addLayout(right, stretch=1)

        self.toast = ToastManager(self.statusBar())

        self._pages: dict[str, QWidget] = {}
        self._build_pages()
        self._setup_shortcuts()

        self._notif_timer = QTimer(self)
        self._notif_timer.setInterval(60_000)
        self._notif_timer.timeout.connect(self._tick_notifications)
        self._notif_timer.start()
        self._tick_notifications()

        self.nav.select_key("dashboard")

    def _add_page(self, key: str, page: QWidget) -> None:
        self._pages[key] = page
        self.stack.addWidget(page)

    def _build_pages(self) -> None:
        self._add_page(
            "dashboard",
            DashboardPage(self.gateway, toast=self.toast, navigate=self.nav.select_key),
        )
        self.students_page = StudentsPage(
            self.gateway, toast=self.toast, open_details=self.open_student
        )
        self._add_page("students", self.students_page)
        self._add_page("attendance", AttendancePage(self.gateway, toast=self.toast))
        self._add_page("academic", AcademicPage(self.gateway, toast=self.toast))
        self._add_page("calendar", CalendarPage(self.gateway, toast=self.toast))
        self._add_page("assignments", AssignmentsPage(self.gateway, toast=self.toast))
        self._add_page("duties", DutiesPage(self.gateway, toast=self.toast))
        self._add_page("meetings", MeetingsPage(self.gateway, toast=self.toast))
        self._add_page("curator_log", CuratorLogPage(self.gateway, toast=self.toast))
        self._add_page(
            "notifications",
            NotificationsPage(self.gateway, toast=self.toast, navigate=self.nav.select_key),
        )
        self._add_page("analytics", AnalyticsPage(self.gateway, toast=self.toast))
        self._add_page("reports", ReportsPage(self.gateway, toast=self.toast))
        self._add_page("archive", ArchivePage(self.gateway, toast=self.toast))
        self.settings_page = SettingsPage(self.gateway, toast=self.toast)
        self._add_page("settings", self.settings_page)

        self.student_details = StudentDetailsPage(
            self.gateway,
            toast=self.toast,
            on_back=lambda: self.nav.select_key("students"),
        )
        self._pages["student_details"] = self.student_details
        self.stack.addWidget(self.student_details)

    def _setup_shortcuts(self) -> None:
        find = QAction(self)
        find.setShortcut(QKeySequence.StandardKey.Find)
        find.triggered.connect(self._focus_search)
        self.addAction(find)

        refresh = QAction(self)
        refresh.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh.triggered.connect(self._refresh_current)
        self.addAction(refresh)

        f5 = QAction(self)
        f5.setShortcut(QKeySequence("F5"))
        f5.triggered.connect(self._refresh_current)
        self.addAction(f5)

        create = QAction(self)
        create.setShortcut(QKeySequence("Ctrl+N"))
        create.triggered.connect(self._create_in_current)
        self.addAction(create)

    def _on_navigate(self, key: str) -> None:
        page = self._pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        if hasattr(page, "refresh"):
            page.refresh()

    def open_student(self, student_id: int) -> None:
        self.student_details.load_student(student_id)
        self.stack.setCurrentWidget(self.student_details)

    def _focus_search(self) -> None:
        current = self.stack.currentWidget()
        if current is self.students_page:
            self.students_page.focus_search()
        else:
            self.search.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _refresh_current(self) -> None:
        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()
        self._refresh_notification_count()
        self.toast.success("Оновлено")

    def _create_in_current(self) -> None:
        current = self.stack.currentWidget()
        if hasattr(current, "create_new"):
            current.create_new()

    def _global_search(self) -> None:
        query = self.search.text().strip()
        if not query:
            return
        try:
            result = call(self.gateway.c.search.search, {"query": query, "limit": 20})
            lines: list[str] = []
            for hit in result.students[:10]:
                lines.append(f"Студент: {hit.title}")
            for hit in result.events[:5]:
                lines.append(f"Захід: {hit.title}")
            for hit in result.notes[:5]:
                lines.append(f"Нотатка: {hit.title}")
            for hit in result.curator_logs[:5]:
                lines.append(f"Журнал: {hit.title}")
            text = "\n".join(lines) if lines else "Нічого не знайдено."
            QMessageBox.information(self, "Результати пошуку", text)
            self.nav.select_key("students")
            self.students_page.filters.search.setText(query)
            self.students_page.reload()
        except AppError as exc:
            QMessageBox.warning(self, "Пошук", user_message(exc))

    def _tick_notifications(self) -> None:
        try:
            call(self.gateway.c.notifications.generate_due_notifications)
        except Exception:  # noqa: BLE001
            pass
        self._refresh_notification_count()

    def _refresh_notification_count(self) -> None:
        try:
            count = call(self.gateway.c.notifications.count_pending)
            self.notif_btn.setText(f"Сповіщення ({count})")
        except Exception:  # noqa: BLE001
            self.notif_btn.setText("Сповіщення")

    def _toggle_theme(self) -> None:
        app = QApplication.instance()
        if isinstance(app, QApplication):
            nxt = toggle_theme(app, self.container)
            self.theme_btn.setText("Світла" if nxt == "dark" else "Темна")
            if nxt == "dark":
                self._canvas.set_grid_color("#E8EEF1", 0.05)
            else:
                self._canvas.set_grid_color("#0C2A35", 0.07)
            self.toast.success("Темна тема" if nxt == "dark" else "Світла тема")

    def _logout(self) -> None:
        self._notif_timer.stop()
        if self._on_logout is not None:
            self._on_logout()
        else:
            try:
                call(self.gateway.c.auth.logout)
            except AppError:
                pass
            self.close()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._notif_timer.stop()
        super().closeEvent(event)
