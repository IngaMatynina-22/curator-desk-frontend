from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import BackendGateway, call, user_message


class ImportWizard(QDialog):
    def __init__(self, gateway: BackendGateway, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        self.setWindowTitle("Імпорт студентів")
        self.resize(560, 420)
        self._path: str | None = None
        self._job_id: int | None = None
        self._report = None

        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()

        # Step 0: file
        s0 = QWidget()
        l0 = QVBoxLayout(s0)
        self.file_label = QLabel("Файл не вибрано")
        btn = QDialogButtonBox()
        pick = btn.addButton("Вибрати CSV/XLSX…", QDialogButtonBox.ButtonRole.ActionRole)
        pick.clicked.connect(self._pick)
        l0.addWidget(QLabel("Крок 1. Вибір файлу"))
        l0.addWidget(self.file_label)
        l0.addWidget(btn)
        self.group = QComboBox()
        self.group.addItem("Без групи", None)
        for g in call(gateway.c.groups.list, {"limit": 200}).items:
            self.group.addItem(g.name, g.id)
        l0.addWidget(QLabel("Група за замовчуванням"))
        l0.addWidget(self.group)
        self.stack.addWidget(s0)

        # Step 1: mapping
        s1 = QWidget()
        l1 = QFormLayout(s1)
        self.map_fields = {}
        for field, default in [
            ("student_number", "student_number"),
            ("last_name", "last_name"),
            ("first_name", "first_name"),
            ("middle_name", "middle_name"),
            ("email", "email"),
            ("phone", "phone"),
        ]:
            edit = QLineEdit(default)
            self.map_fields[field] = edit
            l1.addRow(field, edit)
        wrap1 = QWidget()
        wrap1.setLayout(l1)
        outer1 = QVBoxLayout()
        outer1.addWidget(QLabel("Крок 2. Співставлення колонок"))
        outer1.addWidget(wrap1)
        w1 = QWidget()
        w1.setLayout(outer1)
        self.stack.addWidget(w1)

        # Step 2: preview
        s2 = QWidget()
        l2 = QVBoxLayout(s2)
        l2.addWidget(QLabel("Крок 3. Попередня перевірка"))
        self.preview_list = QListWidget()
        l2.addWidget(self.preview_list)
        self.stack.addWidget(s2)

        # Step 3: confirm info
        s3 = QWidget()
        l3 = QVBoxLayout(s3)
        l3.addWidget(QLabel("Крок 4. Підтвердження"))
        self.confirm_label = QLabel()
        self.confirm_label.setWordWrap(True)
        l3.addWidget(self.confirm_label)
        self.stack.addWidget(s3)

        # Step 4: result
        s4 = QWidget()
        l4 = QVBoxLayout(s4)
        l4.addWidget(QLabel("Крок 5. Результат"))
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        l4.addWidget(self.result_label)
        self.stack.addWidget(s4)

        layout.addWidget(self.stack)
        self.nav = QDialogButtonBox()
        self.btn_back = self.nav.addButton("Назад", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_next = self.nav.addButton("Далі", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_close = self.nav.addButton("Закрити", QDialogButtonBox.ButtonRole.RejectRole)
        self.btn_back.clicked.connect(self._back)
        self.btn_next.clicked.connect(self._next)
        self.btn_close.clicked.connect(self.reject)
        layout.addWidget(self.nav)
        self._update_nav()

    def _pick(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Файл імпорту", "", "Data (*.csv *.xlsx)"
        )
        if path:
            self._path = path
            self.file_label.setText(path)

    def _mapping(self) -> dict:
        return {k: (v.text().strip() or None) for k, v in self.map_fields.items()}

    def _back(self) -> None:
        i = self.stack.currentIndex()
        if i > 0:
            self.stack.setCurrentIndex(i - 1)
        self._update_nav()

    def _next(self) -> None:
        i = self.stack.currentIndex()
        try:
            if i == 0:
                if not self._path:
                    QMessageBox.warning(self, "Імпорт", "Виберіть файл.")
                    return
                self.stack.setCurrentIndex(1)
            elif i == 1:
                report = call(
                    self.gateway.c.imports.preview_import,
                    self._path,
                    self._mapping(),
                    self.group.currentData(),
                )
                self._report = report
                self._job_id = report.job_id
                self.preview_list.clear()
                self.preview_list.addItem(
                    f"Рядків: {report.total_rows}, до створення: {report.to_create}, "
                    f"valid={report.valid}"
                )
                for err in report.errors[:20]:
                    self.preview_list.addItem(f"Помилка: {err}")
                for w in report.warnings[:20]:
                    self.preview_list.addItem(f"⚠ {w}")
                for row in report.rows[:30]:
                    self.preview_list.addItem(
                        f"#{row.row_index} {row.action}: {row.student_number} — {row.message or ''}"
                    )
                self.stack.setCurrentIndex(2)
            elif i == 2:
                if self._job_id is None:
                    return
                report = call(self.gateway.c.imports.validate_import, self._job_id)
                self._report = report
                self.confirm_label.setText(
                    f"Буде створено ≈ {report.to_create} записів.\n"
                    f"Помилок: {len(report.errors)}. Продовжити запис у БД?"
                )
                self.stack.setCurrentIndex(3)
            elif i == 3:
                if self._job_id is None:
                    return
                report = call(self.gateway.c.imports.execute_import, self._job_id)
                self._report = report
                self.result_label.setText(
                    f"Готово. Створено: {report.to_create}, помилок: {len(report.errors)}, "
                    f"попереджень: {len(report.warnings)}."
                )
                self.stack.setCurrentIndex(4)
            elif i == 4:
                self.accept()
                return
        except AppError as exc:
            QMessageBox.warning(self, "Імпорт", user_message(exc))
        self._update_nav()

    def _update_nav(self) -> None:
        i = self.stack.currentIndex()
        self.btn_back.setEnabled(i > 0 and i < 4)
        self.btn_next.setText("Завершити" if i == 4 else ("Імпортувати" if i == 3 else "Далі"))
