from gui.gateway import BackendGateway
from gui.ui.controllers.academic_controller import AcademicController


def test_academic_numeric_and_credit(container, sample_group):
    ctrl = AcademicController(BackendGateway(container))
    subject = ctrl.create_subject({"name": "Програмування", "code": "PROG"})
    student = container.students.create(
        {
            "student_number": "AC-01",
            "last_name": "Оцінко",
            "first_name": "Олег",
            "group_id": sample_group.id,
        }
    )
    rec = ctrl.create_record(
        {
            "student_id": student.id,
            "subject_id": subject.id,
            "record_date": "2026-02-01",
            "control_type": "exam",
            "grade_scale": "numeric",
            "score": 85,
            "max_score": 100,
        }
    )
    assert rec.score == 85
    avg = ctrl.average(student.id)
    assert avg == 85

    credit = ctrl.create_record(
        {
            "student_id": student.id,
            "subject_id": subject.id,
            "record_date": "2026-02-10",
            "control_type": "credit",
            "grade_scale": "credit_pass",
            "text_result": "залік",
        }
    )
    assert credit.text_result == "залік"
    # average still numeric-only
    assert ctrl.average(student.id) == 85

    page = ctrl.list_records(student_id=student.id)
    assert page.total >= 2
