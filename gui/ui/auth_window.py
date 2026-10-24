"""Login / registration — brand-first split layout (Ink & Chalk)."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.container import ServiceContainer
from app.core.exceptions import AppError
from app.schemas.auth import UserOut

from gui.gateway import BackendGateway, call, user_message
from gui.ui.theme import load_saved_theme
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.pattern_backdrop import PatternBackdrop


class AuthWindow(QMainWindow):
    authenticated = pyqtSignal(object)  # UserOut

    def __init__(
        self,
        container: ServiceContainer,
        *,
        on_authenticated: Callable[[UserOut], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.container = container
        self.gateway = BackendGateway(container)
        self._on_authenticated = on_authenticated
        self.setWindowTitle("CuratorDesk — Вхід")
        self.resize(960, 620)
        self.setMinimumSize(800, 520)

        canvas = PatternBackdrop(self)
        theme = load_saved_theme(container)
        if theme == "dark":
            canvas.set_grid_color("#E8EEF1", 0.05)
        else:
            canvas.set_grid_color("#0C2A35", 0.07)
        self.setCentralWidget(canvas)

        root = QHBoxLayout(canvas)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left brand pane (~45%) — always ink, distinct from form side
        brand = QFrame()
        brand.setObjectName("brandPane")
        brand.setMinimumWidth(380)
        brand_lay = QVBoxLayout(brand)
        brand_lay.setContentsMargins(48, 56, 40, 56)
        brand_lay.addStretch(1)
        hero = QLabel("CuratorDesk")
        hero.setObjectName("brandHero")
        hero.setWordWrap(True)
        brand_lay.addWidget(hero)
        tag = QLabel("Робочий стіл куратора академічної групи")
        tag.setObjectName("brandTagline")
        tag.setWordWrap(True)
        brand_lay.addWidget(tag)
        brand_lay.addStretch(2)
        root.addWidget(brand, stretch=45)

        # Right form pane (~55%) — chalk surface so card contrasts in dark too
        right = QFrame()
        right.setObjectName("authFormPane")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(48, 48, 48, 48)
        right_lay.addStretch()

        self.form_host = QFrame()
        self.form_host.setObjectName("authCard")
        self.form_host.setMinimumWidth(340)
        self.form_host.setMaximumWidth(440)
        form_lay = QVBoxLayout(self.form_host)
        form_lay.setContentsMargins(28, 28, 28, 28)
        form_lay.setSpacing(14)

        self.form_title = QLabel("Увійти до системи")
        self.form_title.setObjectName("pageTitle")
        form_lay.addWidget(self.form_title)

        self.error = ErrorBanner()
        form_lay.addWidget(self.error)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_login_tab(), "Вхід")
        self.tabs.addTab(self._build_register_tab(), "Реєстрація")
        self.tabs.currentChanged.connect(self._on_tab)
        form_lay.addWidget(self.tabs)

        hint = QLabel("Демо після seed: curator / curator123")
        hint.setObjectName("mutedLabel")
        form_lay.addWidget(hint)

        wrap = QHBoxLayout()
        wrap.addStretch()
        wrap.addWidget(self.form_host)
        wrap.addStretch()
        right_lay.addLayout(wrap)
        right_lay.addStretch()
        root.addWidget(right, stretch=55)

        self._opacity = QGraphicsOpacityEffect(self.form_host)
        self.form_host.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(220)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        if on_authenticated is not None:
            self.authenticated.connect(on_authenticated)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._opacity.setOpacity(0.0)
        self._fade.start()

    def _on_tab(self, index: int) -> None:
        self.form_title.setText("Реєстрація" if index == 1 else "Увійти до системи")

    def _build_login_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        form = QFormLayout()
        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Логін")
        self.login_pass = QLineEdit()
        self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_pass.setPlaceholderText("Пароль")
        self.login_pass.returnPressed.connect(self._do_login)
        form.addRow("Логін", self.login_user)
        form.addRow("Пароль", self.login_pass)
        lay.addLayout(form)
        self.btn_login = QPushButton("Увійти")
        self.btn_login.setObjectName("primaryButton")
        self.btn_login.setMinimumHeight(42)
        self.btn_login.clicked.connect(self._do_login)
        lay.addWidget(self.btn_login)
        lay.addStretch()
        return w

    def _build_register_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        form = QFormLayout()
        self.reg_user = QLineEdit()
        self.reg_name = QLineEdit()
        self.reg_email = QLineEdit()
        self.reg_pass = QLineEdit()
        self.reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pass2 = QLineEdit()
        self.reg_pass2.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Логін *", self.reg_user)
        form.addRow("ПІБ *", self.reg_name)
        form.addRow("Email", self.reg_email)
        form.addRow("Пароль *", self.reg_pass)
        form.addRow("Підтвердження *", self.reg_pass2)
        lay.addLayout(form)
        self.btn_register = QPushButton("Зареєструватися")
        self.btn_register.setObjectName("primaryButton")
        self.btn_register.setMinimumHeight(42)
        self.btn_register.clicked.connect(self._do_register)
        lay.addWidget(self.btn_register)
        lay.addStretch()
        return w

    def _emit_user(self, user: UserOut) -> None:
        self.authenticated.emit(user)

    def _do_login(self) -> None:
        self.error.clear()
        username = self.login_user.text().strip()
        password = self.login_pass.text()
        if not username or not password:
            self.error.show_error("Введіть логін і пароль.")
            return
        self.btn_login.setEnabled(False)
        try:
            session = call(
                self.gateway.c.auth.login,
                {"username": username, "password": password},
            )
            self._emit_user(session.user)
        except AppError as exc:
            self.error.show_error(user_message(exc))
        finally:
            self.btn_login.setEnabled(True)

    def _do_register(self) -> None:
        self.error.clear()
        username = self.reg_user.text().strip()
        full_name = self.reg_name.text().strip()
        email = self.reg_email.text().strip() or None
        password = self.reg_pass.text()
        password2 = self.reg_pass2.text()
        if not username or not full_name or not password:
            self.error.show_error("Заповніть обов'язкові поля.")
            return
        if password != password2:
            self.error.show_error("Паролі не збігаються.")
            return
        self.btn_register.setEnabled(False)
        try:
            call(
                self.gateway.c.auth.register,
                {
                    "username": username,
                    "password": password,
                    "full_name": full_name,
                    "email": email,
                },
            )
            session = call(
                self.gateway.c.auth.login,
                {"username": username, "password": password},
            )
            self._emit_user(session.user)
        except AppError as exc:
            self.error.show_error(user_message(exc))
        finally:
            self.btn_register.setEnabled(True)

    def reset_form(self) -> None:
        self.error.clear()
        self.login_pass.clear()
        self.reg_pass.clear()
        self.reg_pass2.clear()
        self.tabs.setCurrentIndex(0)
