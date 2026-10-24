from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

from gui.ui.icons import icon


@dataclass(frozen=True)
class NavItem:
    key: str
    title: str
    icon_key: str


NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem("dashboard", "Огляд", "dashboard"),
    NavItem("students", "Студенти", "students"),
    NavItem("attendance", "Відвідуваність", "attendance"),
    NavItem("academic", "Успішність", "academic"),
    NavItem("calendar", "Календар", "calendar"),
    NavItem("assignments", "Доручення", "assignments"),
    NavItem("duties", "Чергування", "duties"),
    NavItem("meetings", "Зустрічі", "meetings"),
    NavItem("curator_log", "Журнал куратора", "log"),
    NavItem("notifications", "Сповіщення", "notifications"),
    NavItem("analytics", "Аналітика", "analytics"),
    NavItem("reports", "Звіти та імпорт", "reports"),
    NavItem("archive", "Архів", "archive"),
    NavItem("settings", "Налаштування", "settings"),
)

_USER_ROLE = Qt.ItemDataRole.UserRole


class NavigationList(QListWidget):
    navigated = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("navList")
        self.setSpacing(0)
        self.setIconSize(QSize(18, 18))
        for item in NAV_ITEMS:
            list_item = QListWidgetItem(icon(item.icon_key, color="#C5D0D6", size=18), item.title)
            list_item.setData(_USER_ROLE, item.key)
            self.addItem(list_item)
        self.currentRowChanged.connect(self._on_row)
        if self.count():
            self.setCurrentRow(0)

    def _on_row(self, row: int) -> None:
        item = self.item(row)
        if item is None:
            return
        key = item.data(_USER_ROLE)
        if isinstance(key, str):
            # Refresh selected icon contrast
            for i in range(self.count()):
                it = self.item(i)
                if it is None:
                    continue
                nav = NAV_ITEMS[i]
                color = "#F7FAFB" if i == row else "#C5D0D6"
                it.setIcon(icon(nav.icon_key, color=color, size=18))
            self.navigated.emit(key)

    def select_key(self, key: str) -> None:
        for i in range(self.count()):
            item = self.item(i)
            if item is not None and item.data(_USER_ROLE) == key:
                self.blockSignals(True)
                self.setCurrentRow(i)
                self.blockSignals(False)
                self._on_row(i)
                return
