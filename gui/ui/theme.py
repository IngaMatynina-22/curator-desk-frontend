"""Ink & Chalk Desk — light/dark design system for CuratorDesk."""

from __future__ import annotations

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from app.container import ServiceContainer

# Tokens (documented for painters / inline styles)
INK = "#0C2A35"
INK_DARK = "#06151C"
CHALK = "#E8EEF1"
CHALK_DARK = "#0E1C22"
PAPER = "#F7FAFB"
PAPER_DARK = "#132830"
ACCENT = "#1A7A6D"
ACCENT_DARK = "#3DBBA8"
MUTED = "#5A6B73"
DANGER = "#9B2C2C"

LIGHT_QSS = """
QWidget {
    background-color: #E8EEF1;
    color: #0C2A35;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}
QLabel {
    background-color: transparent;
}
QMainWindow, QDialog {
    background-color: #E8EEF1;
}
QWidget#canvas {
    background-color: #E8EEF1;
}
QFrame#brandRail {
    background-color: #1A7A6D;
    max-width: 4px;
    min-width: 4px;
}
QFrame#brandPane {
    background-color: #0C2A35;
    color: #E8EEF1;
}
QFrame#brandPane QLabel {
    background-color: transparent;
}
QLabel#brandHero {
    font-family: "Candara", "Calibri Light", "Segoe UI", sans-serif;
    font-size: 42px;
    font-weight: 600;
    color: #F7FAFB;
    background-color: transparent;
}
QLabel#brandTagline {
    font-family: "Candara", "Calibri", "Segoe UI", sans-serif;
    font-size: 15px;
    color: #8FA3AB;
    background-color: transparent;
}
QFrame#authFormPane {
    background-color: #E8EEF1;
}
QFrame#authCard QLabel, QWidget#authCard QLabel {
    background-color: transparent;
}
QWidget#authCard, QFrame#authCard {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 6px;
}
QFrame#sidebar {
    background-color: #0C2A35;
    border: none;
    color: #E8EEF1;
}
QFrame#sidebar QLabel {
    background: transparent;
    color: #E8EEF1;
}
QLabel#sidebarBrand {
    font-family: "Candara", "Calibri Light", "Segoe UI", sans-serif;
    font-size: 26px;
    font-weight: 600;
    color: #F7FAFB;
}
QLabel#sidebarSub {
    font-size: 12px;
    color: #8FA3AB;
}
QListWidget#navList {
    background-color: transparent;
    border: none;
    outline: none;
    color: #E8EEF1;
    padding: 8px 6px;
}
QListWidget#navList::item {
    padding: 10px 12px 10px 10px;
    border-radius: 4px;
    margin: 2px 4px;
    color: #C5D0D6;
    min-height: 22px;
}
QListWidget#navList::item:selected {
    background-color: #1A7A6D;
    color: #F7FAFB;
    font-weight: 600;
    border-left: 3px solid #F7FAFB;
}
QListWidget#navList::item:hover:!selected {
    background-color: #143A48;
    color: #F7FAFB;
}
QFrame#topBar {
    background-color: #F7FAFB;
    border-bottom: 1px solid rgba(12, 42, 53, 0.12);
}
QFrame#workspace {
    background-color: #E8EEF1;
}
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit, QPlainTextEdit, QDateTimeEdit {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 5px;
    padding: 7px 10px;
    selection-background-color: #C5E8E2;
    color: #0C2A35;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #1A7A6D;
}
QPushButton {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 5px;
    padding: 7px 14px;
    color: #0C2A35;
}
QPushButton:hover {
    background-color: #DCE4E8;
}
QPushButton:disabled {
    color: #8FA3AB;
    background-color: #E8EEF1;
}
QPushButton#primaryButton {
    background-color: #0C2A35;
    color: #F7FAFB;
    border: 1px solid #0C2A35;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: #143A48;
}
QPushButton#dangerButton {
    background-color: #9B2C2C;
    color: #F7FAFB;
    border: 1px solid #9B2C2C;
    border-radius: 5px;
}
QPushButton#ghostButton {
    background: transparent;
    border: none;
    color: #5A6B73;
    padding: 6px 8px;
}
QPushButton#ghostButton:hover {
    color: #0C2A35;
    background-color: #DCE4E8;
}
QTableView, QTableWidget {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 5px;
    gridline-color: #E8EEF1;
    selection-background-color: #C5E8E2;
    selection-color: #0C2A35;
    alternate-background-color: #EEF3F5;
    color: #0C2A35;
}
QTableView::item, QTableWidget::item {
    padding: 6px 8px;
    color: #0C2A35;
    border: none;
}
QTableView::item:alternate, QTableWidget::item:alternate {
    background-color: #EEF3F5;
    color: #0C2A35;
}
QTableView::item:selected, QTableWidget::item:selected {
    background-color: #C5E8E2;
    color: #0C2A35;
}
QHeaderView::section {
    background-color: #E8EEF1;
    color: #5A6B73;
    border: none;
    border-bottom: 1px solid #C5D0D6;
    padding: 9px;
    font-weight: 600;
}
QFrame#filterBar {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 5px;
}
QFrame#kanbanColumn {
    background-color: #DCE4E8;
    border-radius: 6px;
}
QLabel#kanbanColumnTitle {
    font-weight: 600;
    color: #0C2A35;
}
QFrame#kanbanCard {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 5px;
}
QLabel#kanbanCardTitle {
    font-weight: 600;
    color: #0C2A35;
}
QFrame#infoGrid, QFrame#chartPanel, QFrame#inboxList, QFrame#inboxDetail, QFrame#agendaPanel {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 6px;
}
QLabel#infoValue {
    font-size: 14px;
    font-weight: 600;
    color: #0C2A35;
}
QFrame#inboxRow {
    background: transparent;
    border-bottom: 1px solid #E8EEF1;
}
QFrame#inboxRow:hover {
    background-color: #EEF3F5;
}
QLabel#inboxSubjectUnread {
    font-weight: 700;
    color: #0C2A35;
}
QLabel#inboxSubject {
    font-weight: 500;
    color: #0C2A35;
}
QTabWidget::pane {
    border: 1px solid #C5D0D6;
    border-radius: 5px;
    background: #F7FAFB;
}
QTabBar::tab {
    background: #E8EEF1;
    border: 1px solid #C5D0D6;
    border-bottom: none;
    padding: 8px 14px;
    margin-right: 3px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #5A6B73;
}
QTabBar::tab:selected {
    background: #F7FAFB;
    color: #0C2A35;
    font-weight: 600;
}
QLabel#pageTitle {
    font-family: "Candara", "Calibri Light", "Segoe UI", sans-serif;
    font-size: 24px;
    font-weight: 600;
    color: #0C2A35;
    background-color: transparent;
}
QLabel#mutedLabel {
    color: #5A6B73;
    background-color: transparent;
}
QFrame#errorBanner {
    background-color: #FCE8E8;
    border: 1px solid #E8B4B4;
    border-radius: 5px;
}
QFrame#emptyState {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 6px;
}
QFrame#kpiPanel {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 5px;
}
QFrame#kpiPanel:hover {
    border-color: #1A7A6D;
}
QLabel#kpiValue {
    font-family: "Candara", "Calibri Light", "Segoe UI", sans-serif;
    font-size: 28px;
    font-weight: 600;
    color: #0C2A35;
}
QLabel#kpiCaption {
    color: #5A6B73;
    font-size: 12px;
}
QStatusBar {
    background: #F7FAFB;
    border-top: 1px solid rgba(12, 42, 53, 0.12);
}
QListWidget {
    background-color: #F7FAFB;
    border: 1px solid #C5D0D6;
    border-radius: 5px;
}
QCalendarWidget {
    background: #F7FAFB;
    border-radius: 5px;
}
QScrollArea {
    background: transparent;
    border: none;
}
QWidget#pageScrollBody {
    background-color: transparent;
}
QAbstractScrollArea::corner {
    background: transparent;
}
QScrollBar:vertical {
    background: #E8EEF1;
    width: 10px;
    margin: 2px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #A8B8C0;
    min-height: 28px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #1A7A6D;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: #E8EEF1;
    height: 10px;
    margin: 2px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #A8B8C0;
    min-width: 28px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #1A7A6D;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""

DARK_QSS = """
QWidget {
    background-color: #0E1C22;
    color: #E8EEF1;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}
QLabel {
    background-color: transparent;
}
QMainWindow, QDialog {
    background-color: #0E1C22;
}
QWidget#canvas {
    background-color: #0E1C22;
}
QFrame#brandRail {
    background-color: #3DBBA8;
    max-width: 4px;
    min-width: 4px;
}
QFrame#brandPane {
    background-color: #06151C;
    color: #E8EEF1;
}
QFrame#brandPane QLabel {
    background-color: transparent;
}
QLabel#brandHero {
    font-family: "Candara", "Calibri Light", "Segoe UI", sans-serif;
    font-size: 42px;
    font-weight: 600;
    color: #E8EEF1;
    background-color: transparent;
}
QLabel#brandTagline {
    font-family: "Candara", "Calibri", "Segoe UI", sans-serif;
    font-size: 15px;
    color: #8FA3AB;
    background-color: transparent;
}
QFrame#authFormPane {
    background-color: #0E1C22;
}
QFrame#authCard QLabel, QWidget#authCard QLabel {
    background-color: transparent;
}
QWidget#authCard, QFrame#authCard {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 6px;
}
QFrame#sidebar {
    background-color: #06151C;
    border: none;
    color: #E8EEF1;
}
QFrame#sidebar QLabel {
    background: transparent;
    color: #E8EEF1;
}
QLabel#sidebarBrand {
    font-family: "Candara", "Calibri Light", "Segoe UI", sans-serif;
    font-size: 26px;
    font-weight: 600;
    color: #E8EEF1;
}
QLabel#sidebarSub {
    font-size: 12px;
    color: #8FA3AB;
}
QListWidget#navList {
    background-color: transparent;
    border: none;
    outline: none;
    color: #E8EEF1;
    padding: 8px 6px;
}
QListWidget#navList::item {
    padding: 11px 12px 11px 14px;
    border-radius: 4px;
    margin: 2px 4px;
    color: #8FA3AB;
}
QListWidget#navList::item:selected {
    background-color: #1A7A6D;
    color: #F7FAFB;
    font-weight: 600;
    border-left: 3px solid #3DBBA8;
}
QListWidget#navList::item:hover:!selected {
    background-color: #0C2A35;
    color: #E8EEF1;
}
QFrame#topBar {
    background-color: #132830;
    border-bottom: 1px solid #1F3A44;
}
QFrame#workspace {
    background-color: #0E1C22;
}
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit, QPlainTextEdit, QDateTimeEdit {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 5px;
    padding: 7px 10px;
    color: #E8EEF1;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #3DBBA8;
}
QPushButton {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 5px;
    padding: 7px 14px;
    color: #E8EEF1;
}
QPushButton:hover {
    background-color: #1A3540;
}
QPushButton:disabled {
    color: #5A6B73;
    background-color: #0E1C22;
}
QPushButton#primaryButton {
    background-color: #E8EEF1;
    color: #06151C;
    border: 1px solid #E8EEF1;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: #FFFFFF;
}
QPushButton#dangerButton {
    background-color: #E06C6C;
    color: #06151C;
    border: 1px solid #E06C6C;
}
QPushButton#ghostButton {
    background: transparent;
    border: none;
    color: #8FA3AB;
}
QPushButton#ghostButton:hover {
    color: #E8EEF1;
    background-color: #1A3540;
}
QTableView, QTableWidget {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 5px;
    gridline-color: #0E1C22;
    selection-background-color: #1A7A6D;
    selection-color: #F7FAFB;
    alternate-background-color: #0E1C22;
    color: #E8EEF1;
}
QTableView::item, QTableWidget::item {
    padding: 6px 8px;
    color: #E8EEF1;
    border: none;
}
QTableView::item:alternate, QTableWidget::item:alternate {
    background-color: #0E1C22;
    color: #E8EEF1;
}
QTableView::item:selected, QTableWidget::item:selected {
    background-color: #1A7A6D;
    color: #F7FAFB;
}
QHeaderView::section {
    background-color: #0E1C22;
    color: #8FA3AB;
    border: none;
    border-bottom: 1px solid #1F3A44;
    padding: 9px;
    font-weight: 600;
}
QFrame#filterBar {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 5px;
}
QFrame#kanbanColumn {
    background-color: #0A1820;
    border-radius: 6px;
}
QLabel#kanbanColumnTitle {
    font-weight: 600;
    color: #E8EEF1;
}
QFrame#kanbanCard {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 5px;
}
QLabel#kanbanCardTitle {
    font-weight: 600;
    color: #E8EEF1;
}
QFrame#infoGrid, QFrame#chartPanel, QFrame#inboxList, QFrame#inboxDetail, QFrame#agendaPanel {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 6px;
}
QLabel#infoValue {
    font-size: 14px;
    font-weight: 600;
    color: #E8EEF1;
}
QFrame#inboxRow {
    background: transparent;
    border-bottom: 1px solid #1F3A44;
}
QFrame#inboxRow:hover {
    background-color: #0E1C22;
}
QLabel#inboxSubjectUnread {
    font-weight: 700;
    color: #E8EEF1;
}
QLabel#inboxSubject {
    font-weight: 500;
    color: #C5D0D6;
}
QTabWidget::pane {
    border: 1px solid #1F3A44;
    border-radius: 5px;
    background: #132830;
}
QTabBar::tab {
    background: #0E1C22;
    border: 1px solid #1F3A44;
    padding: 8px 14px;
    margin-right: 3px;
    border-radius: 4px;
    color: #8FA3AB;
}
QTabBar::tab:selected {
    background: #1A7A6D;
    color: #F7FAFB;
    font-weight: 600;
}
QLabel#pageTitle {
    font-family: "Candara", "Calibri Light", "Segoe UI", sans-serif;
    font-size: 24px;
    font-weight: 600;
    color: #E8EEF1;
    background-color: transparent;
}
QLabel#mutedLabel {
    color: #8FA3AB;
    background-color: transparent;
}
QFrame#errorBanner {
    background-color: #3A1A1A;
    border: 1px solid #6E2C2C;
    border-radius: 5px;
}
QFrame#emptyState {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 6px;
}
QFrame#kpiPanel {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 5px;
}
QFrame#kpiPanel:hover {
    border-color: #3DBBA8;
}
QLabel#kpiValue {
    font-family: "Candara", "Calibri Light", "Segoe UI", sans-serif;
    font-size: 28px;
    font-weight: 600;
    color: #E8EEF1;
}
QLabel#kpiCaption {
    color: #8FA3AB;
    font-size: 12px;
}
QStatusBar {
    background: #132830;
    border-top: 1px solid #1F3A44;
}
QListWidget {
    background-color: #132830;
    border: 1px solid #1F3A44;
    border-radius: 5px;
}
QCalendarWidget {
    background: #132830;
    border-radius: 5px;
}
QScrollArea {
    background: transparent;
    border: none;
}
QWidget#pageScrollBody {
    background-color: transparent;
}
QAbstractScrollArea::corner {
    background: transparent;
}
QScrollBar:vertical {
    background: #0E1C22;
    width: 10px;
    margin: 2px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #3A5560;
    min-height: 28px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #3DBBA8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: #0E1C22;
    height: 10px;
    margin: 2px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #3A5560;
    min-width: 28px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #3DBBA8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""


def apply_theme(app: QApplication, theme: str = "light") -> None:
    app.setStyleSheet(DARK_QSS if theme == "dark" else LIGHT_QSS)
    QSettings().setValue("ui/theme", theme)


def load_saved_theme(container: ServiceContainer | None = None) -> str:
    settings = QSettings()
    theme = settings.value("ui/theme", "light")
    if isinstance(theme, str) and theme in {"light", "dark"}:
        if container is not None:
            try:
                stored = container.settings.get("ui_theme")
                if stored in {"light", "dark"}:
                    return stored
            except Exception:  # noqa: BLE001
                pass
        return theme
    return "light"


def save_theme(theme: str, container: ServiceContainer | None = None) -> None:
    QSettings().setValue("ui/theme", theme)
    if container is not None:
        try:
            container.settings.set("ui_theme", theme)
        except Exception:  # noqa: BLE001
            pass


def toggle_theme(app: QApplication, container: ServiceContainer | None = None) -> str:
    current = load_saved_theme(container)
    nxt = "dark" if current == "light" else "light"
    save_theme(nxt, container)
    apply_theme(app, nxt)
    return nxt
