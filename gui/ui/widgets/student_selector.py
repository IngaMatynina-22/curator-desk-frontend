from __future__ import annotations

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from gui.gateway import BackendGateway, call


class StudentSelector(QWidget):
    """Multi-select list of active students."""

    def __init__(self, gateway: BackendGateway, parent=None) -> None:
        super().__init__(parent)
        self.gateway = gateway
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.list)
        self.reload()

    def reload(self, group_id: int | None = None) -> None:
        self.list.clear()
        filters: dict = {"limit": 500, "include_archived": False}
        if group_id is not None:
            filters["group_id"] = group_id
        page = call(self.gateway.c.students.list, filters)
        for s in page.items:
            name = s.full_name or f"{s.last_name} {s.first_name}"
            item = QListWidgetItem(f"{name} ({s.student_number})")
            item.setData(256, s.id)
            self.list.addItem(item)

    def selected_ids(self) -> list[int]:
        ids: list[int] = []
        for item in self.list.selectedItems():
            sid = item.data(256)
            if sid is not None:
                ids.append(int(sid))
        return ids

    def set_selected_ids(self, ids: list[int]) -> None:
        wanted = set(ids)
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item is None:
                continue
            item.setSelected(item.data(256) in wanted)
