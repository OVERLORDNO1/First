"""Built-in skills (local tools) for JARVIS."""

from .base import Skill, SkillContext, SkillError
from .memory_skills import ForgetFact, RecallFacts, RememberFact
from .notes import AddNote, SearchNotes
from .reminders import AddReminder, CancelReminder, ListReminders

BUILTIN_SKILLS: list[type[Skill]] = [
    RememberFact,
    RecallFacts,
    ForgetFact,
    AddReminder,
    ListReminders,
    CancelReminder,
    AddNote,
    SearchNotes,
]

__all__ = [
    "Skill",
    "SkillContext",
    "SkillError",
    "BUILTIN_SKILLS",
]
