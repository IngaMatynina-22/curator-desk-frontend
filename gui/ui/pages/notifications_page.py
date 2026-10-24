from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import call, user_message
from gui.ui.widgets.empty_state import EmptyState
from gui.ui.widgets.error_banner import ErrorBanner

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class _InboxRow(QFrame):
    def __init__(self, notification: Any, selected: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.notification = notification
        self.setObjectName("inboxRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)
        unread = getattr(notification, "status", "") == "pending"
        subj = QLabel(getattr(notification, "title", "—"))
        subj.setObjectName("inboxSubjectUnread" if unread else "inboxSubject")
        subj.setWordWrap(True)
        lay.addWidget(subj)
        kind = getattr(notification, "kind", "") or ""
        due = getattr(notification, "due_at", None)
        meta = QLabel(f"{kind} · {due}" if due else kind)
        meta.setObjectName("mutedLabel")
        lay.addWidget(meta)
        if selected:
            self.setStyleSheet("QFrame#inboxRow { background-color: #C5E8E2; }")


class NotificationsPage(QWidget):
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
        self._items: list[Any] = []
        self._current: Any | None = None
        self._opened_ids: set[int] = set()

        root = QVBoxLayout(self)
        row = QHBoxLayout()
        title = QLabel("Сповіщення")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        row.addStretch()
        self.btn_gen = QPushButton("Оновити нагадування")
        self.btn_gen.setObjectName("ghostButton")
        self.btn_gen.clicked.connect(self._generate)
        row.addWidget(self.btn_gen)
        root.addLayout(row)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        self.stack = QStackedWidget()
        self.empty = EmptyState(
            "Немає непрочитаних сповіщень",
            "Це нормальний стан. Нагадування з'являться за розкладом, поки програма відкрита.",
        )

        self.inbox = QSplitter(Qt.Orientation.Horizontal)

        left = QFrame()
        left.setObjectName("inboxList")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)
        self._list_host = QWidget()
        self._list_lay = QVBoxLayout(self._list_host)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(0)
        self._list_lay.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self._list_host)
        left_lay.addWidget(scroll)
        self.inbox.addWidget(left)

        right = QFrame()
        right.setObjectName("inboxDetail")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(20, 18, 20, 18)
        right_lay.setSpacing(12)
        self.detail_title = QLabel("Оберіть сповіщення")
        self.detail_title.setObjectName("pageTitle")
        self.detail_title.setStyleSheet("font-size: 18px;")
        self.detail_title.setWordWrap(True)
        right_lay.addWidget(self.detail_title)
        self.detail_meta = QLabel("")
        self.detail_meta.setObjectName("mutedLabel")
        right_lay.addWidget(self.detail_meta)
        self.detail_body = QLabel("")
        self.detail_body.setWordWrap(True)
        self.detail_body.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_lay.addWidget(self.detail_body, stretch=1)

        actions = QHBoxLayout()
        self.btn_read = QPushButton("Прочитано")
        self.btn_snooze = QPushButton("Відкласти на 1 день")
        self.btn_dismiss = QPushButton("Відхилити")
        self.btn_open = QPushButton("Відкрити джерело")
        self.btn_open.setObjectName("primaryButton")
        for b in (self.btn_read, self.btn_snooze, self.btn_dismiss, self.btn_open):
            b.setEnabled(False)
            actions.addWidget(b)
        actions.addStretch()
        self.btn_read.clicked.connect(self._read)
        self.btn_snooze.clicked.connect(self._snooze)
        self.btn_dismiss.clicked.connect(self._dismiss)
        self.btn_open.clicked.connect(self._jump_source)
        right_lay.addLayout(actions)
        self.inbox.addWidget(right)
        self.inbox.setStretchFactor(0, 4)
        self.inbox.setStretchFactor(1, 6)

        self.stack.addWidget(self.inbox)
        self.stack.addWidget(self.empty)
        root.addWidget(self.stack, stretch=1)

    def refresh(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.error.clear()
        try:
            self._items = list(call(self.gateway.c.notifications.get_pending))
            self._rebuild_list()
            if self._items:
                self.stack.setCurrentWidget(self.inbox)
                cur_id = getattr(self._current, "id", None) if self._current else None
                match = next((n for n in self._items if n.id == cur_id), None)
                self._select(match or self._items[0], mark_read=False)
            else:
                self._current = None
                self.stack.setCurrentWidget(self.empty)
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _rebuild_list(self) -> None:
        while self._list_lay.count() > 1:
            item = self._list_lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        cur_id = getattr(self._current, "id", None) if self._current else None
        for n in self._items:
            row = _InboxRow(n, selected=(n.id == cur_id))
            row.mousePressEvent = (  # type: ignore[method-assign]
                lambda e, notif=n: self._on_row_click(e, notif)
            )
            self._list_lay.insertWidget(self._list_lay.count() - 1, row)

    def _on_row_click(self, event, notif) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._select(notif, mark_read=True)

    def _select(self, n: Any, *, mark_read: bool) -> None:
        self._current = n
        self._rebuild_list()
        self.detail_title.setText(getattr(n, "title", "—"))
        kind = getattr(n, "kind", "") or ""
        due = getattr(n, "due_at", None)
        src = getattr(n, "source_type", "") or ""
        self.detail_meta.setText(f"{kind} · джерело: {src}" + (f" · {due}" if due else ""))
        body = getattr(n, "body", None) or getattr(n, "message", None) or "Немає додаткового тексту."
        self.detail_body.setText(str(body))
        for b in (self.btn_read, self.btn_snooze, self.btn_dismiss, self.btn_open):
            b.setEnabled(True)
        if mark_read and getattr(n, "status", "") == "pending" and n.id not in self._opened_ids:
            self._opened_ids.add(n.id)
            try:
                call(self.gateway.c.notifications.mark_as_read, n.id)
            except AppError:
                pass

    def _read(self) -> None:
        if not self._current:
            return
        try:
            call(self.gateway.c.notifications.mark_as_read, self._current.id)
            if self.toast:
                self.toast.success("Позначено прочитаним")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _snooze(self) -> None:
        if not self._current:
            return
        try:
            call(
                self.gateway.c.notifications.snooze,
                self._current.id,
                datetime.now() + timedelta(days=1),
            )
            if self.toast:
                self.toast.success("Відкладено")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _dismiss(self) -> None:
        if not self._current:
            return
        try:
            call(self.gateway.c.notifications.dismiss, self._current.id)
            if self.toast:
                self.toast.success("Відхилено")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _generate(self) -> None:
        try:
            call(self.gateway.c.notifications.generate_due_notifications)
            if self.toast:
                self.toast.success("Нагадування оновлено")
            self.reload()
        except AppError as exc:
            self.error.show_error(user_message(exc))

    def _jump_source(self) -> None:
        if not self._current:
            return
        mapping = {
            "assignment": "assignments",
            "event": "calendar",
            "meeting": "meetings",
            "duty": "duties",
            "attendance": "attendance",
        }
        target = mapping.get(getattr(self._current, "source_type", None))
        if target and self.navigate:
            self.navigate(target)
