from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import call, user_message
from gui.ui.dialogs.change_password_dialog import ChangePasswordDialog
from gui.ui.dialogs.confirm_dialog import ConfirmDialog
from gui.ui.dialogs.group_dialog import GroupDialog
from gui.ui.theme import apply_theme, save_theme
from gui.ui.widgets.data_table import DataTableModel, DataTableView
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.page_scroll import PageScroll
from gui.workers import submit_worker

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class SettingsPage(QWidget):
    def __init__(
        self,
        gateway: BackendGateway,
        *,
        toast: ToastManager | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = PageScroll()
        outer.addWidget(scroll)
        root = scroll.body_layout
        root.setSpacing(14)

        title = QLabel("Налаштування")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        form = QFormLayout()
        self.account_label = QLabel("—")
        form.addRow("Обліковий запис", self.account_label)
        change_pwd = QPushButton("Змінити пароль")
        change_pwd.clicked.connect(self._change_password)
        form.addRow("", change_pwd)

        self.theme = QComboBox()
        self.theme.addItem("Світла", "light")
        self.theme.addItem("Темна", "dark")
        self.theme.currentIndexChanged.connect(self._apply_theme)
        form.addRow("Тема оформлення", self.theme)

        self.date_format = QLabel()
        form.addRow("Формат дати (backend)", self.date_format)

        self.event_hours = QSpinBox()
        self.event_hours.setRange(0, 168)
        self.meeting_hours = QSpinBox()
        self.meeting_hours.setRange(0, 168)
        self.duty_hours = QSpinBox()
        self.duty_hours.setRange(0, 168)
        self.assignment_hours = QSpinBox()
        self.assignment_hours.setRange(0, 168)
        form.addRow("Нагадування: заходи (год)", self.event_hours)
        form.addRow("Нагадування: зустрічі (год)", self.meeting_hours)
        form.addRow("Нагадування: чергування (год)", self.duty_hours)
        form.addRow("Нагадування: доручення (год)", self.assignment_hours)
        save_rem = QPushButton("Зберегти нагадування")
        save_rem.clicked.connect(self._save_reminders)
        form.addRow("", save_rem)

        self.version = QLabel("GUI 0.1.0")
        form.addRow("Версія", self.version)
        root.addLayout(form)

        ops = QHBoxLayout()
        for text, slot in [
            ("Створити резервну копію", self._backup),
            ("Відновити з копії…", self._restore),
            ("Перевірка цілісності", self._integrity),
            ("Додати період", self._add_period),
        ]:
            b = QPushButton(text)
            b.clicked.connect(slot)
            ops.addWidget(b)
        ops.addStretch()
        root.addLayout(ops)
        self.ops_info = QLabel()
        self.ops_info.setWordWrap(True)
        self.ops_info.setObjectName("mutedLabel")
        root.addWidget(self.ops_info)

        groups_header = QHBoxLayout()
        groups_title = QLabel("Групи")
        groups_title.setObjectName("pageTitle")
        groups_title.setStyleSheet("font-size: 16px;")
        groups_header.addWidget(groups_title)
        groups_header.addStretch()
        add_group = QPushButton("Додати групу")
        add_group.setObjectName("primaryButton")
        add_group.clicked.connect(self._add_group)
        groups_header.addWidget(add_group)
        root.addLayout(groups_header)

        self.groups_table = DataTableView()
        self.groups_model = DataTableModel(
            [
                ("Назва", "name", None),
                ("Курс", "course", lambda v: str(v)),
                ("Рік", "academic_year", None),
                ("Спеціальність", "specialty", None),
                ("Студентів", "active_students", lambda v: "—" if v is None else str(v)),
            ]
        )
        self.groups_table.setModel(self.groups_model)
        self.groups_table.setMinimumHeight(180)
        root.addWidget(self.groups_table)

        periods_title = QLabel("Навчальні періоди")
        periods_title.setObjectName("pageTitle")
        periods_title.setStyleSheet("font-size: 16px;")
        root.addWidget(periods_title)
        self.periods_table = DataTableView()
        self.periods_model = DataTableModel(
            [
                ("Назва", "name", None),
                ("Рік", "academic_year", None),
                ("Початок", "starts_on", lambda v: str(v)),
                ("Кінець", "ends_on", lambda v: str(v)),
                ("Поточний", "is_current", lambda v: "Так" if v else "Ні"),
            ]
        )
        self.periods_table.setModel(self.periods_model)
        self.periods_table.setMinimumHeight(180)
        root.addWidget(self.periods_table)
        root.addStretch()

    def refresh(self) -> None:
        self.error.clear()
        try:
            user = call(self.gateway.c.auth.current_user)
            if user is not None:
                self.account_label.setText(f"{user.full_name} (@{user.username})")
            else:
                self.account_label.setText("Не авторизовано")

            theme = self.gateway.c.settings.get("ui_theme", "light")
            idx = self.theme.findData(theme if theme in {"light", "dark"} else "light")
            self.theme.blockSignals(True)
            if idx >= 0:
                self.theme.setCurrentIndex(idx)
            self.theme.blockSignals(False)

            fmt = self.gateway.c.settings.get("date_format", "%Y-%m-%d")
            self.date_format.setText(str(fmt))

            rem = call(self.gateway.c.settings.get_reminder_settings)
            self.event_hours.setValue(rem.event_hours_before)
            self.meeting_hours.setValue(rem.meeting_hours_before)
            self.duty_hours.setValue(rem.duty_hours_before)
            self.assignment_hours.setValue(rem.assignment_hours_before)

            page = call(self.gateway.c.groups.list, {"limit": 200, "include_archived": True})
            self.groups_model.set_rows(page.items)

            periods = call(self.gateway.c.periods.list)
            self.periods_model.set_rows(
                periods if isinstance(periods, list) else getattr(periods, "items", periods)
            )
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _apply_theme(self, _index: int = 0) -> None:
        theme = self.theme.currentData() or "light"
        save_theme(theme, self.gateway.c)
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, theme)
        if self.toast:
            self.toast.success("Тему збережено")

    def _change_password(self) -> None:
        user = call(self.gateway.c.auth.current_user)
        if user is None:
            self.error.show_error("Потрібна авторизація.")
            return
        dlg = ChangePasswordDialog(self.gateway, user.id, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Пароль змінено")

    def _save_reminders(self) -> None:
        try:
            call(
                self.gateway.c.settings.set_reminder_settings,
                {
                    "event_hours_before": self.event_hours.value(),
                    "meeting_hours_before": self.meeting_hours.value(),
                    "duty_hours_before": self.duty_hours.value(),
                    "assignment_hours_before": self.assignment_hours.value(),
                },
            )
            if self.toast:
                self.toast.success("Нагадування збережено")
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add_group(self) -> None:
        dlg = GroupDialog(self.gateway, parent=self)
        if dlg.exec() and dlg.saved_group:
            if self.toast:
                self.toast.success("Групу створено")
            self.refresh()

    def _backup(self) -> None:
        def work(container, *_a, **_k):
            return container.backup.create_backup("manual")

        def done(path):
            self.ops_info.setText(f"Резервну копію створено: {path}")
            if self.toast:
                self.toast.success("Backup готовий")

        submit_worker(work, on_finished=done, on_error=lambda m: self.error.show_error(m))

    def _restore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Файл резервної копії", "", "DB (*.db *;*)")
        if not path:
            return
        if not ConfirmDialog.ask(
            self,
            "Відновлення",
            "Відновлення замінить поточну базу даних. Продовжити?",
            confirm_text="Відновити",
            danger=True,
        ):
            return

        def work(container, *_a, **_k):
            return container.backup.restore(path)

        def done(result):
            self.ops_info.setText(f"Відновлено. Safety backup: {result}")
            if self.toast:
                self.toast.success("Базу відновлено")

        submit_worker(work, on_finished=done, on_error=lambda m: self.error.show_error(m))

    def _integrity(self) -> None:
        try:
            report = call(self.gateway.c.integrity.run_checks)
            data = report.model_dump() if hasattr(report, "model_dump") else str(report)
            self.ops_info.setText(f"Перевірка цілісності: {data}")
            if self.toast:
                self.toast.success("Перевірку виконано")
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add_period(self) -> None:
        today = date.today()
        try:
            call(
                self.gateway.c.periods.create,
                {
                    "name": f"Семестр {today.year}",
                    "academic_year": f"{today.year}/{today.year + 1}",
                    "kind": "semester",
                    "starts_on": today.replace(month=9, day=1)
                    if today.month >= 9
                    else today.replace(month=2, day=1),
                    "ends_on": today.replace(month=12, day=31)
                    if today.month >= 9
                    else today.replace(month=6, day=30),
                    "is_current": True,
                },
            )
            if self.toast:
                self.toast.success("Період створено")
            self.refresh()
        except AppError as exc:
            self.error.show_error(user_message(exc))
