from gui.gateway import BackendGateway, call, user_message
from app.core.exceptions import ValidationError, NotFoundError


def test_user_message_maps_validation():
    msg = user_message(ValidationError("invalid email format"))
    assert "invalid email" in msg.lower() or "Перевірте" in msg


def test_gateway_lists_students(container, sample_group):
    gw = BackendGateway(container)
    student = call(
        gw.c.students.create,
        {
            "student_number": "KN-2101",
            "last_name": "Іваненко",
            "first_name": "Іван",
            "group_id": sample_group.id,
        },
    )
    page = call(gw.c.students.list, {"query": "Іван"})
    assert page.total >= 1
    assert any(s.id == student.id for s in page.items)


def test_not_found_message():
    msg = user_message(NotFoundError("Student not found"))
    assert "не знайдено" in msg.lower() or "Student" in msg
