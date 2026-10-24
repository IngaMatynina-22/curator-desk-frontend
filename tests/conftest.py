"""Fixtures — temporary SQLite via backend test helpers."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.container import ServiceContainer
from app.core.config import configure_settings
from app.database.engine import set_engine
from app.database.initialization import create_test_engine
from app.database.session import SessionLocal, configure_session_factory


@pytest.fixture()
def engine(tmp_path):
    db_path = tmp_path / "test.db"
    configure_settings(
        database_path=db_path,
        backups_dir=tmp_path / "backups",
        exports_dir=tmp_path / "exports",
        attachments_dir=tmp_path / "attachments",
    )
    eng = create_test_engine(url=f"sqlite:///{db_path.as_posix()}")
    yield eng
    eng.dispose()
    set_engine(None)


@pytest.fixture()
def session(engine) -> Session:
    configure_session_factory(engine)
    sess = SessionLocal()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def container(session) -> ServiceContainer:
    return ServiceContainer(session)


@pytest.fixture()
def sample_group(container):
    return container.groups.create(
        {
            "name": "КН-21",
            "specialty": "Комп'ютерні науки",
            "course": 3,
            "academic_year": "2025/2026",
        }
    )
