"""Long-term memory skills: durable facts about the user and their world."""

from __future__ import annotations

from typing import Any

from .base import Skill, SkillContext


class RememberFact(Skill):
    name = "remember_fact"
    description = (
        "Store a durable fact about the user or their world in long-term memory "
        "(preferences, people, dates, ongoing projects). Call this proactively "
        "whenever the user mentions something worth keeping — do not wait to be "
        "asked. Writing to an existing key overwrites it."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Short snake_case identifier, e.g. 'sister_birthday' or 'preferred_editor'.",
            },
            "value": {"type": "string", "description": "The fact itself, one or two sentences."},
        },
        "required": ["key", "value"],
    }

    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        ctx.store.remember(kwargs["key"], kwargs["value"])
        return f"Stored fact '{kwargs['key'].strip().lower()}'."


class RecallFacts(Skill):
    name = "recall_facts"
    description = (
        "Search long-term memory for stored facts. Call this whenever personal "
        "context might be relevant to the user's request (their preferences, "
        "people they've mentioned, dates, projects). An empty query lists everything."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Substring to search keys and values for. Empty lists all facts.",
            }
        },
        "required": [],
    }

    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        facts = ctx.store.recall(kwargs.get("query", ""))
        if not facts:
            return "No matching facts in memory."
        return "\n".join(f"- {key}: {value}" for key, value in facts)


class ForgetFact(Skill):
    name = "forget_fact"
    description = (
        "Delete a fact from long-term memory by its exact key. Use recall_facts "
        "first if unsure of the key. Confirm with the user before forgetting "
        "anything they did not explicitly ask to remove."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Exact key of the fact to delete."}
        },
        "required": ["key"],
    }

    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        if ctx.store.forget(kwargs["key"]):
            return f"Forgot '{kwargs['key'].strip().lower()}'."
        return f"No fact stored under '{kwargs['key'].strip().lower()}'."
