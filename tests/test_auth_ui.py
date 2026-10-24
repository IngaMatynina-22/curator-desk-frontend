"""Auth flow tests against real AuthService."""

from __future__ import annotations

import pytest

from app.core.exceptions import AuthError

from gui.gateway import BackendGateway, call, user_message
from gui.ui.auth_window import AuthWindow


def test_register_login_logout(container):
    gw = BackendGateway(container)
    user = call(
        gw.c.auth.register,
        {
            "username": "gui_anna",
            "password": "secret12",
            "full_name": "Anna GUI",
        },
    )
    assert user.username == "gui_anna"

    session = call(gw.c.auth.login, {"username": "gui_anna", "password": "secret12"})
    assert session.user.id == user.id
    assert call(gw.c.auth.current_user).username == "gui_anna"

    call(gw.c.auth.logout)
    assert call(gw.c.auth.current_user) is None


def test_invalid_password_message(container):
    call(
        container.auth.register,
        {"username": "gui_bob", "password": "secret12", "full_name": "Bob"},
    )
    with pytest.raises(AuthError) as exc:
        call(container.auth.login, {"username": "gui_bob", "password": "wrongpass"})
    assert "Невірний" in user_message(exc.value) or "password" in str(exc.value).lower()


def test_auth_window_smoke(qtbot, container):
    win = AuthWindow(container)
    qtbot.addWidget(win)
    win.show()
    assert win.tabs.count() == 2
    win.login_user.setText("nobody")
    win.login_pass.setText("badpass1")
    win._do_login()
    assert win.error.isVisible()


def test_auth_window_register_emits(qtbot, container):
    win = AuthWindow(container)
    qtbot.addWidget(win)
    seen = []

    def on_user(u):
        seen.append(u)

    win.authenticated.connect(on_user)
    win.tabs.setCurrentIndex(1)
    win.reg_user.setText("gui_carl")
    win.reg_name.setText("Carl GUI")
    win.reg_pass.setText("secret12")
    win.reg_pass2.setText("secret12")
    win._do_register()
    assert len(seen) == 1
    assert seen[0].username == "gui_carl"
    assert call(container.auth.current_user).username == "gui_carl"
