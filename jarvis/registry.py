"""Skill registry: holds local tools and dispatches the model's tool calls."""

from __future__ import annotations

from typing import Any

from .skills import BUILTIN_SKILLS
from .skills.base import Skill, SkillContext, SkillError


class SkillRegistry:
    def __init__(self, skills: list[Skill] | None = None):
        self._skills: dict[str, Skill] = {}
        for skill in skills if skills is not None else [cls() for cls in BUILTIN_SKILLS]:
            self.register(skill)

    def register(self, skill: Skill) -> None:
        if skill.name in self._skills:
            raise ValueError(f"Duplicate skill name: {skill.name}")
        self._skills[skill.name] = skill

    def names(self) -> list[str]:
        return list(self._skills)

    def to_tool_params(self) -> list[dict[str, Any]]:
        return [skill.to_tool_param() for skill in self._skills.values()]

    def dispatch(self, name: str, tool_input: dict[str, Any], ctx: SkillContext) -> tuple[str, bool]:
        """Run a skill. Returns ``(result_text, is_error)``.

        Errors are captured and reported back to the model rather than raised,
        so a bad tool call never crashes the conversation loop.
        """
        skill = self._skills.get(name)
        if skill is None:
            return f"Unknown tool: {name}", True
        try:
            return skill.run(ctx, **tool_input), False
        except SkillError as exc:
            return str(exc), True
        except Exception as exc:  # noqa: BLE001 — surface to the model, keep the loop alive
            return f"{type(exc).__name__}: {exc}", True
