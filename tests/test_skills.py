from __future__ import annotations

from datetime import datetime, timedelta

from jarvis.registry import SkillRegistry
from jarvis.skills.base import SkillContext


def make_ctx(store, settings) -> SkillContext:
    return SkillContext(store=store, settings=settings)


def test_registry_exposes_valid_tool_params():
    registry = SkillRegistry()
    params = registry.to_tool_params()
    assert len(params) == len(registry.names())
    for p in params:
        assert p["name"] and p["description"]
        assert p["input_schema"]["type"] == "object"


def test_remember_and_recall_via_dispatch(store, settings):
    ctx = make_ctx(store, settings)
    registry = SkillRegistry()
    out, err = registry.dispatch(
        "remember_fact", {"key": "coffee", "value": "flat white, no sugar"}, ctx
    )
    assert not err and "coffee" in out
    out, err = registry.dispatch("recall_facts", {"query": "coffee"}, ctx)
    assert not err and "flat white" in out


def test_add_reminder_parses_iso(store, settings):
    ctx = make_ctx(store, settings)
    registry = SkillRegistry()
    due = (datetime.now() + timedelta(days=1)).replace(microsecond=0)
    out, err = registry.dispatch(
        "add_reminder", {"text": "Dentist", "due_at": due.isoformat()}, ctx
    )
    assert not err and "Reminder #1" in out
    assert store.pending_reminders()[0].due_at == due


def test_add_reminder_rejects_past_and_garbage(store, settings):
    ctx = make_ctx(store, settings)
    registry = SkillRegistry()
    out, err = registry.dispatch(
        "add_reminder", {"text": "x", "due_at": "2001-01-01T00:00"}, ctx
    )
    assert err and "past" in out
    out, err = registry.dispatch(
        "add_reminder", {"text": "x", "due_at": "next tuesday-ish"}, ctx
    )
    assert err and "ISO 8601" in out
    assert store.pending_reminders() == []


def test_cancel_reminder_flow(store, settings):
    ctx = make_ctx(store, settings)
    registry = SkillRegistry()
    due = (datetime.now() + timedelta(hours=2)).isoformat()
    registry.dispatch("add_reminder", {"text": "Gym", "due_at": due}, ctx)
    out, err = registry.dispatch("list_reminders", {}, ctx)
    assert not err and "Gym" in out
    out, err = registry.dispatch("cancel_reminder", {"reminder_id": 1}, ctx)
    assert not err and "cancelled" in out
    out, err = registry.dispatch("cancel_reminder", {"reminder_id": 1}, ctx)
    assert not err and "No pending reminder" in out


def test_unknown_tool_is_reported_not_raised(store, settings):
    registry = SkillRegistry()
    out, err = registry.dispatch("launch_missiles", {}, make_ctx(store, settings))
    assert err and "Unknown tool" in out
