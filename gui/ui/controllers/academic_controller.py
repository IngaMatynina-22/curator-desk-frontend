from __future__ import annotations

from app.core.enums import GradeScale
from app.schemas.academic_record import AcademicRecordFilter

from gui.gateway import BackendGateway, call


class AcademicController:
    def __init__(self, gateway: BackendGateway) -> None:
        self.gateway = gateway

    def list_records(self, **kwargs):
        status = kwargs.pop("grade_scale", None)
        if status:
            kwargs["grade_scale"] = GradeScale(status)
        return call(self.gateway.c.academic.list_records, AcademicRecordFilter(**kwargs))

    def create_record(self, data: dict):
        return call(self.gateway.c.academic.create_record, data)

    def update_record(self, record_id: int, data: dict):
        return call(self.gateway.c.academic.update_record, record_id, data)

    def average(self, student_id: int):
        return call(self.gateway.c.academic.average_for_student, student_id)

    def list_subjects(self, include_archived: bool = False):
        return call(self.gateway.c.academic.list_subjects, include_archived)

    def create_subject(self, data: dict):
        return call(self.gateway.c.academic.create_subject, data)

    def update_subject(self, subject_id: int, data: dict):
        return call(self.gateway.c.academic.update_subject, subject_id, data)

    def student_name_map(self) -> dict[int, str]:
        page = call(self.gateway.c.students.list, {"limit": 500, "include_archived": True})
        return {s.id: (s.full_name or f"{s.last_name} {s.first_name}") for s in page.items}
