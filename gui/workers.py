"""Background work for long operations — own container/session per task."""

from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from app.container import create_container
from app.core.exceptions import AppError

from gui.gateway import user_message

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)


class ContainerWorker(QRunnable):
    """Runs ``fn(container, *args, **kwargs)`` on a worker thread with a fresh container."""

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        init_db: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.init_db = init_db
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:
        container = None
        try:
            container = create_container(init_db=self.init_db)
            result = self.fn(container, *self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except AppError as exc:
            self.signals.error.emit(user_message(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error("Worker failed:\n%s", traceback.format_exc())
            self.signals.error.emit(user_message(exc))
        finally:
            if container is not None:
                container.close()


def submit_worker(
    fn: Callable[..., Any],
    *args: Any,
    on_finished: Callable[[Any], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    init_db: bool = False,
    **kwargs: Any,
) -> ContainerWorker:
    worker = ContainerWorker(fn, *args, init_db=init_db, **kwargs)
    if on_finished is not None:
        worker.signals.finished.connect(on_finished)
    if on_error is not None:
        worker.signals.error.connect(on_error)
    QThreadPool.globalInstance().start(worker)
    return worker
