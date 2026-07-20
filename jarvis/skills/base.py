"""Skill: the unit of local capability.

A skill is a tool the model can call. Subclass :class:`Skill`, define
``name`` / ``description`` / ``input_schema``, implement ``run``, and register
it with the :class:`~jarvis.registry.SkillRegistry` — the agent handles the
rest (schema exposure, dispatch, error reporting back to the model).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from ..config import Settings
from ..memory import Store


@dataclass
class SkillContext:
    """Everything a skill may need at execution time."""

    store: Store
    settings: Settings
    now: Callable[[], datetime] = datetime.now


class SkillError(Exception):
    """Raise inside ``run`` for a clean, model-visible error message."""


class Skill(ABC):
    #: Tool name exposed to the model. snake_case, verb_noun.
    name: str
    #: Tells the model when and how to use the tool — be prescriptive.
    description: str
    #: JSON Schema for the tool input.
    input_schema: dict[str, Any]

    def to_tool_param(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    @abstractmethod
    def run(self, ctx: SkillContext, **kwargs: Any) -> str:
        """Execute and return a plain-text result for the model."""
