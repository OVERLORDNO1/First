"""Reminder skills — the agent's interface to the reminder queue.

The background scheduler (jarvis.scheduler) is what actually fires these.
"""

from __future__ import annotations

from typing import Any

from dateutil import parser as dtparser

from ..memory import RECURRENCES
from .base import Skill, SkillContext, SkillError


class AddReminder(Skill):
    name = "add_reminder"
    description = (
        "Schedule a reminder that will be delivered to the user at a specific "
        "time, even if the conversation has ended. Use for anything the user "
        "wants to be reminded about: tasks, events, birthdays, deadlines. "
        "Resolve relative times ('tomorrow at 9') into a concrete ISO 8601 "
        "local timestamp yourself, using the current time from the context "
        "envelope."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "What to remind the user about."},
            "due_at": {
                "type": "string",
                "description": "ISO 8601 local timestamp, e.g. '2026-07-21T09:00'.",
            },
            "recurrence": {
                "type": "string",
                "enum": list(RECURRENCES),
                "description": "Optional repeat interval. Omit for a one-off reminder.",
            },
        },
        "required": ["text", "due_at"],
    }

    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        try:
            due_at = dtparser.isoparse(kwargs["due_at"])
        except (ValueError, OverflowError) as exc:
            raise SkillError(
                f"Could not parse due_at {kwargs['due_at']!r} as ISO 8601: {exc}"
            ) from exc
        recurrence = kwargs.get("recurrence", "")
        if not recurrence and due_at <= ctx.now():
            raise SkillError(
                f"due_at {due_at.isoformat()} is in the past (now: "
                f"{ctx.now().replace(microsecond=0).isoformat()}). Pick a future time."
            )
        reminder_id = ctx.store.add_reminder(kwargs["text"], due_at, recurrence)
        suffix = f", repeating {recurrence}" if recurrence else ""
        return (
            f"Reminder #{reminder_id} set for {due_at.strftime('%a %Y-%m-%d %H:%M')}{suffix}."
        )


class ListReminders(Skill):
    name = "list_reminders"
    description = (
        "List all pending reminders with their IDs and due times. Use before "
        "cancelling, or when the user asks what's coming up."
    )
    input_schema = {"type": "object", "properties": {}, "required": []}

    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        reminders = ctx.store.pending_reminders()
        if not reminders:
            return "No pending reminders."
        lines = []
        for r in reminders:
            suffix = f" (repeats {r.recurrence})" if r.recurrence else ""
            lines.append(
                f"- #{r.id} {r.due_at.strftime('%a %Y-%m-%d %H:%M')}: {r.text}{suffix}"
            )
        return "\n".join(lines)


class CancelReminder(Skill):
    name = "cancel_reminder"
    description = (
        "Cancel a pending reminder by its numeric ID. Use list_reminders first "
        "if the ID is unknown."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "reminder_id": {"type": "integer", "description": "ID from list_reminders."}
        },
        "required": ["reminder_id"],
    }

    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        if ctx.store.cancel_reminder(int(kwargs["reminder_id"])):
            return f"Reminder #{kwargs['reminder_id']} cancelled."
        return f"No pending reminder with ID {kwargs['reminder_id']}."
