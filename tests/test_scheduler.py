from __future__ import annotations

from datetime import datetime, timedelta

from jarvis.scheduler import ReminderService


def test_poll_delivers_due_and_leaves_future(store, settings):
    store.add_reminder("due now", datetime.now() - timedelta(minutes=1))
    store.add_reminder("later", datetime.now() + timedelta(hours=5))

    delivered: list[str] = []
    service = ReminderService(store, delivered.append, poll_seconds=3600)

    assert service.poll_once() == 1
    assert "due now" in delivered[0]
    # future reminder untouched, delivered one is done
    pending = store.pending_reminders()
    assert [r.text for r in pending] == ["later"]
    # second poll is a no-op
    assert service.poll_once() == 0


def test_poll_reschedules_recurring(store, settings):
    store.add_reminder(
        "daily standup", datetime.now() - timedelta(minutes=1), recurrence="daily"
    )
    delivered: list[str] = []
    service = ReminderService(store, delivered.append, poll_seconds=3600)
    assert service.poll_once() == 1
    assert "next:" in delivered[0]
    pending = store.pending_reminders()
    assert len(pending) == 1 and pending[0].due_at > datetime.now()


def test_notify_failure_does_not_kill_poller(store, settings):
    store.add_reminder("boom", datetime.now() - timedelta(minutes=1))

    def bad_notify(_: str) -> None:
        raise RuntimeError("channel down")

    service = ReminderService(store, bad_notify, poll_seconds=3600)
    assert service.poll_once() == 1  # no exception escapes


def test_parse_hhmm():
    assert ReminderService._parse_hhmm("07:30") == (7, 30)
    assert ReminderService._parse_hhmm("9") == (9, 0)
