"""Thin adapter around ServiceContainer — no business rules here."""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from app.container import ServiceContainer
from app.core.exceptions import (
    AppError,
    AuthError,
    ConflictError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

ERROR_HINTS: dict[type[AppError], str] = {
    ValidationError: "Перевірте введені дані.",
    NotFoundError: "Запис не знайдено.",
    ConflictError: "Конфлікт із наявними даними.",
    DatabaseError: "Помилка збереження. Спробуйте ще раз.",
    AuthError: "",
}

_AUTH_UA = {
    "invalid username or password": "Невірний логін або пароль.",
    "authentication required": "Потрібна авторизація.",
}


def user_message(exc: BaseException) -> str:
    """Map backend/domain errors to Ukrainian UI text."""
    if isinstance(exc, AuthError):
        base = (exc.message or str(exc)).strip()
        return _AUTH_UA.get(base.lower(), base or "Помилка авторизації.")
    if isinstance(exc, AppError):
        hint = ERROR_HINTS.get(type(exc), "")
        base = exc.message or str(exc)
        return f"{base} {hint}".strip() if hint and hint not in base else base
    logger.exception("Unexpected error")
    return "Сталася неочікувана помилка. Деталі записано в журнал."


def call(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Invoke a service method; re-raise AppError unchanged, wrap others."""
    try:
        return fn(*args, **kwargs)
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001 — boundary for GUI
        logger.exception("Service call failed: %s", fn)
        text = str(exc)
        if "no such column" in text or "OperationalError" in type(exc).__name__:
            raise DatabaseError(
                "Схема бази застаріла відносно backend. "
                "Видаліть або перемістіть файл БД і перезапустіть застосунок "
                "(init_database створить актуальну схему). Деталі: "
                + text
            ) from exc
        raise DatabaseError(text) from exc


class BackendGateway:
    """Holds the shared container for the main GUI thread."""

    def __init__(self, container: ServiceContainer) -> None:
        self.container = container

    @property
    def c(self) -> ServiceContainer:
        return self.container
