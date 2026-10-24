from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import call, user_message
from gui.ui.dialogs.import_wizard import ImportWizard
from gui.ui.widgets.error_banner import ErrorBanner
from gui.workers import submit_worker

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager

EXPORTS = {
    "students": ("Студенти", "export_students"),
    "attendance": ("Відвідуваність", "export_attendance"),
    "assignments": ("Доручення", "export_assignments"),
    "duties": ("Чергування", "export_duties"),
    "events": ("Заходи", "export_events"),
    "curator_log": ("Журнал", "export_curator_log"),
    "summary": ("Підсумок", "export_summary"),
}


class ReportsPage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast

        root = QVBoxLayout(self)
        title = QLabel("Звіти та імпорт")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        self.error = ErrorBanner()
        root.addWidget(self.error)

        form = QFormLayout()
        self.report_type = QComboBox()
        for key, (label, _) in EXPORTS.items():
            self.report_type.addItem(label, key)
        self.fmt = QComboBox()
        self.fmt.addItem("CSV", "csv")
        self.fmt.addItem("XLSX", "xlsx")
        self.fmt.addItem("PDF", "pdf")
        form.addRow("Тип звіту", self.report_type)
        form.addRow("Формат", self.fmt)
        root.addLayout(form)

        row = QHBoxLayout()
        export_btn = QPushButton("Експортувати")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self._export)
        import_btn = QPushButton("Імпорт студентів…")
        import_btn.clicked.connect(self._import)
        row.addWidget(export_btn)
        row.addWidget(import_btn)
        row.addStretch()
        root.addLayout(row)

        self.result = QLabel()
        self.result.setWordWrap(True)
        root.addWidget(self.result)
        root.addStretch()

    def refresh(self) -> None:
        self.error.clear()

    def _export(self) -> None:
        self.error.clear()
        key = self.report_type.currentData()
        method_name = EXPORTS[key][1]
        fmt = self.fmt.currentData()

        def work(container, *_a, **_k):
            method = getattr(container.reports, method_name)
            return method(fmt=fmt)

        self.result.setText("Формування звіту…")

        def done(result):
            path = Path(result.path)
            dest, _ = QFileDialog.getSaveFileName(
                self,
                "Зберегти звіт",
                str(path.name),
                "All (*.*)",
            )
            if dest:
                Path(dest).write_bytes(path.read_bytes())
                self.result.setText(f"Збережено {result.rows} записів → {dest}")
            else:
                self.result.setText(f"Звіт готовий: {path} ({result.rows} рядків)")
            if self.toast:
                self.toast.success("Експорт завершено")

        def err(msg: str):
            self.error.show_error(msg)
            self.result.setText("")

        submit_worker(work, on_finished=done, on_error=err)

    def _import(self) -> None:
        dlg = ImportWizard(self.gateway, parent=self)
        if dlg.exec():
            if self.toast:
                self.toast.success("Імпорт завершено")
