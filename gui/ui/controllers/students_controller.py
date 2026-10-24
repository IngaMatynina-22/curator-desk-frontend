"""Students controller — orchestrates gateway calls for students UI."""

from __future__ import annotations

from app.core.enums import StudentStatus
from app.schemas.common import PageResult
from app.schemas.student import StudentFilter, StudentOut

from gui.gateway import BackendGateway, call


class StudentsController:
    def __init__(self, gateway: BackendGateway) -> None:
        self.gateway = gateway

    def list_students(
        self,
        *,
        query: str | None = None,
        group_id: int | None = None,
        status: str | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 50,
        sort_by: str = "last_name",
        sort_dir: str = "asc",
    ) -> PageResult[StudentOut]:
        filters = StudentFilter(
            query=query or None,
            group_id=group_id,
            status=StudentStatus(status) if status else None,
            include_archived=include_archived,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        return call(self.gateway.c.students.list, filters)

    def get(self, student_id: int) -> StudentOut:
        return call(self.gateway.c.students.get, student_id)

    def summary(self, student_id: int):
        return call(self.gateway.c.students.summary, student_id)

    def archive(self, student_id: int) -> StudentOut:
        return call(self.gateway.c.students.archive, student_id)

    def restore(self, student_id: int) -> StudentOut:
        return call(self.gateway.c.students.restore, student_id)

    def list_groups(self, *, include_archived: bool = False):
        return call(
            self.gateway.c.groups.list,
            {"limit": 200, "include_archived": include_archived},
        )

    def timeline(
        self,
        student_id: int,
        *,
        types: list[str] | None = None,
        offset: int = 0,
        limit: int = 50,
    ):
        return call(
            self.gateway.c.timeline.get_timeline,
            student_id,
            types=types,
            offset=offset,
            limit=limit,
        )

    def preview_archive(self, ids: list[int]):
        return call(self.gateway.c.bulk.bulk_archive_students, ids, preview=True)

    def apply_archive(self, ids: list[int]):
        return call(self.gateway.c.bulk.bulk_archive_students, ids, preview=False)

    def export_students(self, group_id: int | None = None, fmt: str = "csv"):
        return call(self.gateway.c.reports.export_students, fmt=fmt, group_id=group_id)

    def group_name_map(self) -> dict[int, str]:
        page = self.list_groups(include_archived=True)
        return {g.id: g.name for g in page.items}
