"""Ukrainian display labels for backend enums / statuses."""

from __future__ import annotations

STUDENT_STATUS = {
    "active": "Активний",
    "academic_leave": "Академічна відпустка",
    "expelled": "Відрахований",
    "transferred": "Переведений",
    "graduated": "Випускник",
}

STUDY_FORM = {
    "full_time": "Денна",
    "part_time": "Заочна",
    "distance": "Дистанційна",
}

ATTENDANCE_STATUS = {
    "present": "Присутній",
    "absent": "Відсутній",
    "late": "Запізнився",
    "excused": "Поважна причина",
}

ASSIGNMENT_STATUS = {
    "new": "Нове",
    "in_progress": "В роботі",
    "done": "Виконано",
    "cancelled": "Скасовано",
}

ASSIGNMENT_PRIORITY = {
    "low": "Низький",
    "medium": "Середній",
    "high": "Високий",
}

TIMELINE_KIND = {
    "attendance": "Відвідуваність",
    "academic": "Навчання",
    "assignment": "Доручення",
    "duty": "Чергування",
    "event": "Захід",
    "meeting": "Зустріч",
    "curator_log": "Журнал",
    "note": "Нотатка",
}


def label(mapping: dict[str, str], value: str | None, fallback: str | None = None) -> str:
    if value is None:
        return fallback or "—"
    return mapping.get(value, fallback or value)
