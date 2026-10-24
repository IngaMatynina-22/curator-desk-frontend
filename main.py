"""CuratorDesk GUI entry point with auth gate."""

from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from app.container import create_container
from app.schemas.auth import UserOut

from gui.ui.auth_window import AuthWindow
from gui.ui.main_window import MainWindow
from gui.ui.theme import apply_theme, load_saved_theme


class AppShell:
    """Keeps one container; switches AuthWindow <-> MainWindow."""

    def __init__(self, qt_app: QApplication) -> None:
        self.qt_app = qt_app
        self.container = create_container(init_db=True)
        apply_theme(qt_app, load_saved_theme(self.container))
        self.auth_window: AuthWindow | None = None
        self.main_window: MainWindow | None = None

    def start(self) -> int:
        # Always show login first; clear sticky session from prior run / seed.
        try:
            self.container.auth.logout()
        except Exception:  # noqa: BLE001
            logging.getLogger(__name__).exception("startup logout failed")
        self._show_auth()
        try:
            return self.qt_app.exec()
        finally:
            self.container.close()

    def _show_auth(self) -> None:
        if self.main_window is not None:
            self.main_window.hide()
            self.main_window.deleteLater()
            self.main_window = None
        self.auth_window = AuthWindow(
            self.container,
            on_authenticated=self._on_authenticated,
        )
        self.auth_window.show()

    def _on_authenticated(self, user: UserOut) -> None:
        if self.auth_window is not None:
            self.auth_window.hide()
            self.auth_window.deleteLater()
            self.auth_window = None
        self._show_main(user)

    def _show_main(self, user: UserOut) -> None:
        self.main_window = MainWindow(
            self.container,
            on_logout=self._on_logout,
            current_user=user,
        )
        self.main_window.show()

    def _on_logout(self) -> None:
        try:
            self.container.auth.logout()
        except Exception:  # noqa: BLE001
            logging.getLogger(__name__).exception("logout failed")
        self._show_auth()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("CuratorDesk")
    qt_app.setOrganizationName("CuratorDesk")
    return AppShell(qt_app).start()


if __name__ == "__main__":
    raise SystemExit(main())
