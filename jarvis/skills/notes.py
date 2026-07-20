"""Note skills — freeform capture, distinct from keyed facts."""

from __future__ import annotations

from typing import Any

from .base import Skill, SkillContext


class AddNote(Skill):
    name = "add_note"
    description = (
        "Save a freeform note (an idea, a meeting takeaway, a link, a thought). "
        "Use notes for prose worth keeping; use remember_fact for discrete "
        "key/value facts."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The note content."},
            "tags": {
                "type": "string",
                "description": "Optional comma-separated tags, e.g. 'work,ideas'.",
            },
        },
        "required": ["text"],
    }

    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        note_id = ctx.store.add_note(kwargs["text"], kwargs.get("tags", ""))
        return f"Note #{note_id} saved."


class SearchNotes(Skill):
    name = "search_notes"
    description = (
        "Search saved notes by substring or tag. An empty query returns the "
        "most recent notes."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Substring or tag to search for."}
        },
        "required": [],
    }

    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        notes = ctx.store.search_notes(kwargs.get("query", ""))
        if not notes:
            return "No matching notes."
        lines = []
        for note_id, text, tags, created_at in notes:
            tag_str = f" [{tags}]" if tags else ""
            lines.append(f"- #{note_id} ({created_at}){tag_str}: {text}")
        return "\n".join(lines)
