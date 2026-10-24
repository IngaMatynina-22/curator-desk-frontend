from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import call, user_message
from gui.ui.dialogs.duty_dialog import DutyDialog
from gui.ui.dialogs.event_dialog import EventDialog
from gui.ui.dialogs.meeting_dialog import MeetingDialog
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.marked_calendar import MarkedCalendar

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager

KIND_UA = {
    "event": "Захід",
    "meeting": "Зустріч",
    "duty": "Чергування",
    "assignment_overdue": "Простр. доручення",
}


def _item_date(item: dict) -> date | None:
    raw = item.get("starts_at") or item.get("duty_date") or item.get("due_date")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw)
    try:
        if "T" in text or " " in text:
            return datetime.fromisoformat(text.replace("Z", "")).date()
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


class CalendarPage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast
        self._mode = "day"
        self._items: list[dict] = []

        root = QVBoxLayout(self)
        title_row = QHBoxLayout()
        title = QLabel("Календар")
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        for text, mode in [("День", "day"), ("Тиждень", "week"), ("Місяць", "month"), ("Список", "list")]:
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, m=mode: self._set_mode(m))
            title_row.addWidget(b)
        for text, slot, primary in [
            ("Захід", self._add_event, True),
            ("Зустріч", self._add_meeting, False),
            ("Чергування", self._add_duty, False),
        ]:
            b = QPushButton(text)
            if primary:
                b.setObjectName("primaryButton")
            b.clicked.connect(slot)
            title_row.addWidget(b)
        root.addLayout(title_row)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        body = QHBoxLayout()
        body.setSpacing(16)
        self.calendar = MarkedCalendar()
        self.calendar.selectionChanged.connect(self.reload)
        self.calendar.currentPageChanged.connect(self._on_page_changed)
        body.addWidget(self.calendar, stretch=6)

        agenda = QFrame()
        agenda.setObjectName("agendaPanel")
        right = QVBoxLayout(agenda)
        right.setContentsMargins(16, 14, 16, 14)
        self.agenda_title = QLabel("Події")
        self.agenda_title.setObjectName("pageTitle")
        self.agenda_title.setStyleSheet("font-size: 16px;")
        right.addWidget(self.agenda_title)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._open_item)
        right.addWidget(self.list, stretch=1)
        btn_reschedule = QPushButton("Перенести вибраний захід…")
        btn_reschedule.clicked.connect(self._reschedule)
        right.addWidget(btn_reschedule)
        body.addWidget(agenda, stretch=4)
        root.addLayout(body, stretch=1)

        self._refresh_markers()

    def refresh(self) -> None:
        self.reload()

    def create_new(self) -> None:
        self._add_event()

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        self.reload()

    def _selected_date(self) -> date:
        q = self.calendar.selectedDate()
        return date(q.year(), q.month(), q.day())

    def _on_page_changed(self, year: int, month: int) -> None:
        self._refresh_markers(year, month)

    def _refresh_markers(self, year: int | None = None, month: int | None = None) -> None:
        if year is None or month is None:
            year = self.calendar.yearShown()
            month = self.calendar.monthShown()
        try:
            items = call(self.gateway.c.calendar.for_month, year, month)
            marked: set[date] = set()
            for item in items:
                d = _item_date(item)
                if d is not None:
                    marked.add(d)
            self.calendar.set_marked_dates(marked)
        except AppError:
            pass

    def reload(self) -> None:
        self.error.clear()
        day = self._selected_date()
        try:
            if self._mode == "day":
                self._items = call(self.gateway.c.calendar.for_day, day)
                self.agenda_title.setText(f"День · {day.isoformat()}")
            elif self._mode == "week":
                self._items = call(self.gateway.c.calendar.for_week, day)
                self.agenda_title.setText(f"Тиждень від {day.isoformat()}")
            elif self._mode == "month":
                self._items = call(self.gateway.c.calendar.for_month, day.year, day.month)
                self.agenda_title.setText(f"Місяць {day.month}/{day.year}")
            else:
                self._items = call(self.gateway.c.calendar.upcoming, limit=50)
                self.agenda_title.setText("Найближчі події")
            self.list.clear()
            for item in self._items:
                kind = item.get("kind", "")
                title = item.get("title", "")
                starts = item.get("starts_at") or item.get("duty_date") or ""
                status = item.get("status") or ""
                text = f"[{KIND_UA.get(kind, kind)}] {title} · {starts} · {status}"
                li = QListWidgetItem(text)
                li.setData(256, item)
                self.list.addItem(li)
            if not self._items:
                self.list.addItem("Немає подій за цей період.")
            self._refresh_markers()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _add_event(self) -> None:
        dlg = EventDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Захід збережено")
            self.reload()

    def _add_meeting(self) -> None:
        dlg = MeetingDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Зустріч збережено")
            self.reload()

    def _add_duty(self) -> None:
        dlg = DutyDialog(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Чергування збережено")
            self.reload()

    def _open_item(self, item: QListWidgetItem) -> None:
        data = item.data(256)
        if not isinstance(data, dict):
            return
        kind = data.get("kind")
        eid = data.get("id")
        try:
            if kind == "event" and eid:
                ev = call(self.gateway.c.events.get, eid)
                dlg = EventDialog(self.gateway, event=ev, parent=self)
                if dlg.exec():
                    self.reload()
            elif kind == "meeting" and eid:
                m = call(self.gateway.c.meetings.get, eid)
                dlg = MeetingDialog(self.gateway, meeting=m, parent=self)
                if dlg.exec():
                    self.reload()
            elif kind == "duty" and eid:
                d = call(self.gateway.c.duties.get, eid)
                dlg = DutyDialog(self.gateway, duty=d, parent=self)
                if dlg.exec():
                    self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _reschedule(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        data = item.data(256)
        if not isinstance(data, dict) or data.get("kind") != "event":
            QMessageBox.information(self, "Перенесення", "Оберіть захід зі списку.")
            return
        ev = call(self.gateway.c.events.get, data["id"])
        dlg = EventDialog(self.gateway, event=ev, parent=self)
        if dlg.exec() and dlg.saved:
            if self.toast:
                self.toast.success("Захід оновлено")
            self.reload()
