from gui.gateway import BackendGateway
from gui.ui.controllers.students_controller import StudentsController


def test_crud_and_timeline(container, sample_group):
    ctrl = StudentsController(BackendGateway(container))
    created = container.students.create(
        {
            "student_number": "KN-2102",
            "last_name": "Петренко",
            "first_name": "Олена",
            "group_id": sample_group.id,
        }
    )
    page = ctrl.list_students(query="Петренко")
    assert page.total == 1
    assert page.items[0].id == created.id

    got = ctrl.get(created.id)
    assert got.student_number == "KN-2102"

    summary = ctrl.summary(created.id)
    assert summary.student.id == created.id

    tl = ctrl.timeline(created.id)
    assert tl.total >= 0

    archived = ctrl.archive(created.id)
    assert archived.is_archived is True
    restored = ctrl.restore(created.id)
    assert restored.is_archived is False


def test_bulk_archive_preview(container, sample_group):
    ctrl = StudentsController(BackendGateway(container))
    s = container.students.create(
        {
            "student_number": "KN-2103",
            "last_name": "Сидоренко",
            "first_name": "Марія",
            "group_id": sample_group.id,
        }
    )
    preview = ctrl.preview_archive([s.id])
    assert preview.preview_only is True
    assert len(preview.details) >= 1 or preview.applied >= 1
