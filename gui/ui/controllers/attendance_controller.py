from __future__ import annotations

from datetime import date

from app.core.enums import AttendanceStatus
from app.schemas.attendance import AttendanceFilter

from gui.gateway import BackendGateway, call


class AttendanceController:
    def __init__(self, gateway: BackendGateway) -> None:
        self.gateway = gateway

    def list_records(
        self,
        *,
        student_id: int | None = None,
        subject_id: int | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        offset: int = 0,
        limit: int = 100,
    ):
        return call(
            self.gateway.c.attendance.list,
            AttendanceFilter(
                student_id=student_id,
                subject_id=subject_id,
                status=AttendanceStatus(status) if status else None,
                date_from=date_from,
                date_to=date_to,
                offset=offset,
                limit=limit,
            ),
        )

    def create_lesson(self, data: dict):
        return call(self.gateway.c.attendance.create_lesson, data)

    def update_record(self, record_id: int, data: dict):
        return call(self.gateway.c.attendance.update, record_id, data)

    def preview_group(self, lesson_id: int, group_id: int, default_status: str = "present"):
        return call(
            self.gateway.c.bulk.preview_group_attendance,
            lesson_id,
            group_id,
            AttendanceStatus(default_status),
        )

    def mark_group(self, lesson_id: int, group_id: int, default_status: str = "present"):
        return call(
            self.gateway.c.bulk.mark_group_attendance,
            {
                "lesson_id": lesson_id,
                "group_id": group_id,
                "default_status": AttendanceStatus(default_status),
                "preview": False,
            },
        )

    def bulk_mark_custom(self, lesson_id: int, marks: list[dict]):
        return call(
            self.gateway.c.attendance.bulk_mark,
            {"lesson_id": lesson_id, "marks": marks},
        )

    def student_stats(self, student_id: int, date_from=None, date_to=None):
        return call(self.gateway.c.attendance.student_stats, student_id, date_from, date_to)

    def top_absentees(self, limit: int = 10):
        return call(self.gateway.c.attendance.top_absentees, limit)

    def list_subjects(self):
        return call(self.gateway.c.academic.list_subjects, False)

    def list_groups(self):
        return call(self.gateway.c.groups.list, {"limit": 200})

    def student_name_map(self) -> dict[int, str]:
        page = call(self.gateway.c.students.list, {"limit": 500, "include_archived": True})
        return {
            s.id: (s.full_name or f"{s.last_name} {s.first_name}")
            for s in page.items
        }
