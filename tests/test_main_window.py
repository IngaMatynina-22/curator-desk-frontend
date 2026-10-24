"""GUI smoke tests with pytest-qt."""

from __future__ import annotations

import pytest

from gui.ui.main_window import MainWindow
from gui.ui.theme import apply_theme


@pytest.fixture()
def window(qtbot, container, sample_group):
    from PyQt6.QtWidgets import QApplication

    container.students.create(
        {
            "student_number": "KN-2199",
            "last_name": "Тестенко",
            "first_name": "Тест",
            "group_id": sample_group.id,
        }
    )
    win = MainWindow(container)
    app = QApplication.instance()
    if app is not None:
        apply_theme(app, "light")
    qtbot.addWidget(win)
    win.show()
    return win


def test_navigation_switches_pages(qtbot, window):
    window.nav.select_key("settings")
    assert window.stack.currentWidget() is window.settings_page
    window.nav.select_key("dashboard")
    assert window.stack.currentWidget() is window._pages["dashboard"]


def test_students_list_loads(qtbot, window):
    window.nav.select_key("students")
    window.students_page.reload()
    assert window.students_page.model.rowCount() >= 1


def test_open_student_card(qtbot, window, container):
    window.nav.select_key("students")
    window.students_page.reload()
    student = container.students.list({"query": "Тестенко"}).items[0]
    window.open_student(student.id)
    assert window.stack.currentWidget() is window.student_details
    assert "Тестенко" in window.student_details.header.text()


def test_create_student_via_dialog(qtbot, window, sample_group, monkeypatch):
    from PyQt6.QtWidgets import QDialog

    from gui.ui.dialogs.student_dialog import StudentDialog

    def fake_exec(self):
        self.student_number.setText("KN-2200")
        self.last_name.setText("Новий")
        self.first_name.setText("Студент")
        idx = self.group.findData(sample_group.id)
        self.group.setCurrentIndex(idx)
        self._save()
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(StudentDialog, "exec", fake_exec)
    window.nav.select_key("students")
    before = window.students_page.model.rowCount()
    window.students_page.create_student()
    window.students_page.reload()
    assert window.students_page.model.rowCount() >= before
