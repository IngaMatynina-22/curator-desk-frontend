# CuratorDesk GUI

Desktop CRM для куратора академічної групи (PyQt6). Усі бізнес-операції йдуть через backend `create_container()`.

## Встановлення

Спочатку editable-інсталяція backend (пакет `app` / `curatordesk`), потім GUI:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ../curator-desk-backend"[dev]"
pip install -e ".[dev]"
```

Backend має бути встановлений у тому ж середовищі, щоб `from app.container import create_container` працював.

## Запуск

```bash
python main.py
```

Спочатку з’явиться екран **Вхід / Реєстрація** (`c.auth`). Після seed можна увійти як `curator` / `curator123`. Тема світла/темна — у топ-барі або в Налаштуваннях.

## Тести

```bash
pytest -q
```

## Архітектура

`MainWindow → pages/controllers → gateway → ServiceContainer → services → SQLite`

Пакет UI — `gui/` (не `app/`), щоб не конфліктувати з backend namespace.
