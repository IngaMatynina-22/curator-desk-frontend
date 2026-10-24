from __future__ import annotations

from PyQt6.QtWidgets import QLabel

# Ink & Chalk palette — muted ink/sea tones, no neon
STATUS_COLORS = {
    "active": ("#0C5C4C", "#D8EDE8"),
    "academic_leave": ("#7A5A1E", "#F3EBD8"),
    "expelled": ("#9B2C2C", "#F5E0E0"),
    "transferred": ("#1A4A5C", "#D8E6EC"),
    "graduated": ("#3A4A52", "#E2E8EA"),
    "new": ("#1A4A5C", "#D8E6EC"),
    "in_progress": ("#7A5A1E", "#F3EBD8"),
    "done": ("#0C5C4C", "#D8EDE8"),
    "cancelled": ("#3A4A52", "#E2E8EA"),
    "present": ("#0C5C4C", "#D8EDE8"),
    "absent": ("#9B2C2C", "#F5E0E0"),
    "late": ("#7A5A1E", "#F3EBD8"),
    "excused": ("#1A4A5C", "#D8E6EC"),
}


class StatusBadge(QLabel):
    def __init__(self, text: str = "", status_key: str | None = None, parent=None) -> None:
        super().__init__(text, parent)
        self.set_status(text, status_key)

    def set_status(self, text: str, status_key: str | None = None) -> None:
        self.setText(text)
        key = status_key or ""
        fg, bg = STATUS_COLORS.get(key, ("#3A4A52", "#E2E8EA"))
        self.setStyleSheet(
            f"QLabel {{ color: {fg}; background: {bg}; border-radius: 4px; "
            f"padding: 2px 8px; font-weight: 600; }}"
        )
