"""The agent core: conversation state, the Claude tool loop, and context.

Design notes
------------
- The persona system prompt is byte-stable and carries a ``cache_control``
  breakpoint, so the (large) fixed prefix is served from the prompt cache on
  every turn. Dynamic state (time, upcoming reminders) travels in a per-turn
  <context> envelope at the *end* of the prompt, which invalidates nothing.
- Local skills run through :class:`SkillRegistry`. Remote MCP servers
  (Composio, etc.) are attached via the API's MCP connector — the server-side
  tools need no local execution at all.
- The loop handles ``tool_use``, ``pause_turn`` (server-side tool
  continuation), and ``refusal`` stop reasons explicitly.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import anthropic

from .config import Settings
from .memory import Store
from .persona import Persona
from .registry import SkillRegistry
from .skills.base import SkillContext

log = logging.getLogger(__name__)

_MCP_BETA = "mcp-client-2025-11-20"
_MAX_TOOL_ROUNDS = 25


class Jarvis:
    def __init__(
        self,
        settings: Settings,
        store: Store,
        registry: SkillRegistry | None = None,
        client: Any | None = None,
    ):
        self.settings = settings
        self.store = store
        self.registry = registry or SkillRegistry()
        self.client = client if client is not None else anthropic.Anthropic()
        self.persona = Persona.from_settings(settings)
        self.mcp_servers = settings.mcp_servers()
        self.ctx = SkillContext(store=store, settings=settings)

        # Byte-stable system prompt with a cache breakpoint.
        self._system = [
            {
                "type": "text",
                "text": self.persona.system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ]
        # In-session message history (full content blocks).
        self.messages: list[dict[str, Any]] = []
        self._restore_history()

    # -- public API -------------------------------------------------------

    def converse(self, user_text: str) -> str:
        """One full user turn: returns the assistant's final text reply."""
        self.store.append_message("user", user_text)
        self.messages.append(
            {"role": "user", "content": user_text + self._context_envelope()}
        )

        reply = self._run_loop()

        self.store.append_message("assistant", reply)
        self._trim_history()
        return reply

    def greeting(self) -> str:
        now = datetime.now()
        hour = now.hour
        part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        pending = self.store.pending_reminders(before=now + timedelta(hours=24))
        extra = (
            f" You have {len(pending)} reminder(s) in the next 24 hours."
            if pending
            else ""
        )
        return (
            f"Good {part}, {self.settings.honorific}. "
            f"{self.settings.assistant_name} at your service.{extra}"
        )

    # -- the loop ---------------------------------------------------------

    def _run_loop(self) -> str:
        for _ in range(_MAX_TOOL_ROUNDS):
            response = self._request()

            if response.stop_reason == "refusal":
                return (
                    "I'm afraid I must decline that one, "
                    f"{self.settings.honorific}."
                )

            if response.stop_reason == "pause_turn":
                # Server-side tool loop paused; append and re-send to resume.
                self.messages.append(
                    {"role": "assistant", "content": response.content}
                )
                continue

            if response.stop_reason == "tool_use":
                self.messages.append(
                    {"role": "assistant", "content": response.content}
                )
                self.messages.append(
                    {"role": "user", "content": self._run_tools(response)}
                )
                continue

            # end_turn / max_tokens: extract text and finish.
            self.messages.append({"role": "assistant", "content": response.content})
            text = "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
            return text or "(no reply)"

        return (
            f"I seem to have gone down a rabbit hole, {self.settings.honorific} — "
            "that took more tool calls than I'm allowed. Could you rephrase?"
        )

    def _request(self) -> Any:
        kwargs: dict[str, Any] = dict(
            model=self.settings.model,
            max_tokens=self.settings.max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": self.settings.effort},
            system=self._system,
            messages=self.messages,
            tools=self._tools(),
        )
        if self.mcp_servers:
            return self.client.beta.messages.create(
                betas=[_MCP_BETA], mcp_servers=self.mcp_servers, **kwargs
            )
        return self.client.messages.create(**kwargs)

    def _tools(self) -> list[dict[str, Any]]:
        tools = self.registry.to_tool_params()
        for server in self.mcp_servers:
            tools.append({"type": "mcp_toolset", "mcp_server_name": server["name"]})
        return tools

    def _run_tools(self, response: Any) -> list[dict[str, Any]]:
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            log.info("tool call: %s(%s)", block.name, block.input)
            output, is_error = self.registry.dispatch(block.name, block.input, self.ctx)
            result: dict[str, Any] = {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            }
            if is_error:
                result["is_error"] = True
            results.append(result)
        return results

    # -- context & history ------------------------------------------------

    def _context_envelope(self) -> str:
        now = datetime.now()
        lines = [f"local time: {now.strftime('%A %Y-%m-%d %H:%M')}"]
        upcoming = self.store.pending_reminders(before=now + timedelta(hours=24))
        if upcoming:
            lines.append("reminders due within 24h:")
            lines.extend(
                f"  - #{r.id} {r.due_at.strftime('%a %H:%M')}: {r.text}"
                for r in upcoming[:10]
            )
        return "\n\n<context>\n" + "\n".join(lines) + "\n</context>"

    def _restore_history(self) -> None:
        """Reload recent text turns so JARVIS remembers across restarts."""
        for role, text in self.store.recent_messages(
            self.settings.reload_history_turns
        ):
            self.messages.append({"role": role, "content": text})

    def _trim_history(self) -> None:
        """Bound in-context history, cutting only at user-text boundaries.

        Never severs a tool_use/tool_result pair: trimming always drops from
        the front up to the next message that is a plain-string user turn.
        """
        limit = self.settings.max_history_messages
        while len(self.messages) > limit:
            cut = None
            for i in range(1, len(self.messages)):
                m = self.messages[i]
                if m["role"] == "user" and isinstance(m["content"], str):
                    cut = i
                    break
            if cut is None or len(self.messages) - cut < 2:
                break  # nothing safe to trim
            del self.messages[:cut]
            if len(self.messages) <= limit:
                break
