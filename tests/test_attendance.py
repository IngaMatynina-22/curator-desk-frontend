from app.core.enums import AttendanceStatus
from app.core.exceptions import ConflictError

from gui.gateway import BackendGateway
from gui.ui.controllers.attendance_controller import AttendanceController


def test_lesson_bulk_mark_and_update(container, sample_group):
    subject = container.academic.create_subject({"name": "Математика", "code": "MATH"})
    student = container.students.create(
        {
            "student_number": "ATT-01",
            "last_name": "Аттестов",
            "first_name": "Андрій",
            "group_id": sample_group.id,
        }
    )
    ctrl = AttendanceController(BackendGateway(container))
    lesson = ctrl.create_lesson(
        {"lesson_date": "2026-03-01", "subject_id": subject.id, "topic": "Тема 1"}
    )
    preview = ctrl.preview_group(lesson.id, sample_group.id)
    assert preview.preview_only is True
    assert any(d["student_id"] == student.id for d in preview.details)

    marks = ctrl.bulk_mark_custom(
        lesson.id,
        [{"student_id": student.id, "status": AttendanceStatus.ABSENT}],
    )
    assert len(marks) == 1
    assert marks[0].status == "absent"

    updated = ctrl.update_record(marks[0].id, {"status": AttendanceStatus.LATE})
    assert updated.status == "late"

    page = ctrl.list_records(student_id=student.id)
    assert page.total >= 1

    try:
        ctrl.bulk_mark_custom(
            lesson.id,
            [{"student_id": student.id, "status": AttendanceStatus.PRESENT}],
        )
        # may raise ConflictError depending on backend
    except ConflictError:
        pass

    stats = ctrl.student_stats(student.id)
    assert stats.student_id == student.id
