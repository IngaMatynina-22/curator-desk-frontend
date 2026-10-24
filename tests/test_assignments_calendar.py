from datetime import date, datetime, timedelta

from gui.gateway import BackendGateway, call


def test_assignment_create_complete_bulk(container, sample_group):
    student = container.students.create(
        {
            "student_number": "ASG-01",
            "last_name": "Задачко",
            "first_name": "Зіна",
            "group_id": sample_group.id,
        }
    )
    a = call(
        container.assignments.create,
        {
            "title": "Звіт",
            "due_date": date.today() - timedelta(days=1),
            "student_ids": [student.id],
        },
    )
    overdue = call(container.assignments.overdue)
    assert any(x.id == a.id for x in overdue)

    preview = call(
        container.bulk.bulk_update_assignments,
        {"ids": [a.id], "status": "in_progress", "preview": True},
    )
    assert preview.preview_only is True

    call(container.assignments.complete, a.id, "готово")
    got = call(container.assignments.get, a.id)
    assert got.status == "done"


def test_calendar_event_day(container):
    starts = datetime.now().replace(microsecond=0)
    ends = starts + timedelta(hours=2)
    ev = call(
        container.events.create,
        {
            "title": "Збори",
            "starts_at": starts,
            "ends_at": ends,
            "event_type": "group_meeting",
        },
    )
    items = call(container.calendar.for_day, starts.date())
    assert any(i.get("id") == ev.id or i.get("title") == "Збори" for i in items)


def test_notification_mark_read(container):
    call(container.notifications.generate_due_notifications)
    pending = call(container.notifications.get_pending)
    if pending:
        call(container.notifications.mark_as_read, pending[0].id)
        after = {n.id for n in call(container.notifications.get_pending)}
        assert pending[0].id not in after
