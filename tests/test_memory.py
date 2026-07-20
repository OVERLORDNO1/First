from __future__ import annotations

from datetime import datetime, timedelta

import pytest


def test_facts_roundtrip(store):
    store.remember("Sister_Birthday", "June 3rd")
    store.remember("editor", "VS Code")
    assert ("sister_birthday", "June 3rd") in store.recall()
    assert store.recall("birthday") == [("sister_birthday", "June 3rd")]
    store.remember("editor", "Neovim")  # overwrite
    assert dict(store.recall())["editor"] == "Neovim"
    assert store.forget("editor") is True
    assert store.forget("editor") is False


def test_notes(store):
    note_id = store.add_note("Idea: build a rocket", tags="ideas")
    assert note_id == 1
    assert store.search_notes("rocket")[0][1] == "Idea: build a rocket"
    assert store.search_notes("ideas")  # tag match
    assert store.search_notes("nonexistent") == []


def test_reminder_lifecycle(store):
    due = datetime.now() + timedelta(hours=1)
    rid = store.add_reminder("Call mom", due)
    pending = store.pending_reminders()
    assert [r.id for r in pending] == [rid]
    # not yet due
    assert store.pending_reminders(before=datetime.now()) == []
    # due filter includes it once past
    assert store.pending_reminders(before=due + timedelta(minutes=1))[0].text == "Call mom"
    # one-off completes
    assert store.complete_or_reschedule(pending[0]) is None
    assert store.pending_reminders() == []


def test_reminder_cancel(store):
    rid = store.add_reminder("Standup", datetime.now() + timedelta(days=1))
    assert store.cancel_reminder(rid) is True
    assert store.cancel_reminder(rid) is False
    assert store.pending_reminders() == []


def test_recurring_reminder_reschedules_past_downtime(store):
    # Fired reminder whose next few occurrences are already in the past
    # (simulating downtime) must land on the next *future* occurrence.
    due = datetime.now() - timedelta(days=3)
    store.add_reminder("Daily review", due, recurrence="daily")
    reminder = store.pending_reminders()[0]
    next_due = store.complete_or_reschedule(reminder)
    assert next_due is not None and next_due > datetime.now()
    assert next_due - datetime.now() < timedelta(days=1)
    # still pending, with the new due date
    assert store.pending_reminders()[0].due_at == next_due


def test_invalid_recurrence_rejected(store):
    with pytest.raises(ValueError):
        store.add_reminder("x", datetime.now(), recurrence="hourly")


def test_history(store):
    store.append_message("user", "hello")
    store.append_message("assistant", "Good evening, sir.")
    assert store.recent_messages() == [
        ("user", "hello"),
        ("assistant", "Good evening, sir."),
    ]
    assert store.recent_messages(limit=1) == [("assistant", "Good evening, sir.")]
