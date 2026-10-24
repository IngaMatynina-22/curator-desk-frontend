from __future__ import annotations

from typing import Any, Callable, Sequence

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableView


class DataTableModel(QAbstractTableModel):
    def __init__(
        self,
        columns: Sequence[tuple[str, str, Callable[[Any], Any] | None]],
        parent=None,
    ) -> None:
        """columns: (header, attr_or_key, optional formatter)."""
        super().__init__(parent)
        self._columns = list(columns)
        self._rows: list[Any] = []

    def set_rows(self, rows: Sequence[Any]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None
        row = self._rows[index.row()]
        _header, key, fmt = self._columns[index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._get(row, key)
            if fmt is not None:
                return fmt(value)
            return "" if value is None else str(value)
        if role == Qt.ItemDataRole.UserRole:
            return row
        return None

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self._columns):
            return self._columns[section][0]
        return None

    def row_at(self, row: int) -> Any | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    @staticmethod
    def _get(row: Any, key: str) -> Any:
        if isinstance(row, dict):
            return row.get(key)
        return getattr(row, key, None)


class DataTableView(QTableView):
    row_activated = pyqtSignal(object)
    selection_changed_rows = pyqtSignal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.setWordWrap(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(36)
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(72)
        self.setShowGrid(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setStyleSheet("")  # rely on global QSS item colors
        self.doubleClicked.connect(self._on_double_click)
        self.selectionModel()  # may be None until model set

    def setModel(self, model) -> None:  # noqa: N802
        super().setModel(model)
        if self.selectionModel() is not None:
            self.selectionModel().selectionChanged.connect(self._on_selection)
        # Stretch columns to available width so tables don't clip sideways
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _on_double_click(self, index: QModelIndex) -> None:
        model = self.model()
        if isinstance(model, DataTableModel):
            row = model.row_at(index.row())
            if row is not None:
                self.row_activated.emit(row)

    def _on_selection(self, *_args) -> None:
        model = self.model()
        if not isinstance(model, DataTableModel):
            return
        rows = []
        for idx in self.selectionModel().selectedRows():
            item = model.row_at(idx.row())
            if item is not None:
                rows.append(item)
        self.selection_changed_rows.emit(rows)

    def selected_rows(self) -> list[Any]:
        model = self.model()
        if not isinstance(model, DataTableModel) or self.selectionModel() is None:
            return []
        result = []
        for idx in self.selectionModel().selectedRows():
            item = model.row_at(idx.row())
            if item is not None:
                result.append(item)
        return result
