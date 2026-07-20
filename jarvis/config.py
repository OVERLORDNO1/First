"""Runtime configuration, loaded from environment variables and `.env`.

All JARVIS-specific settings use the ``JARVIS_`` prefix. Third-party
credentials (``ANTHROPIC_API_KEY``, ``TELEGRAM_BOT_TOKEN``) keep their
conventional names via aliases.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JARVIS_", env_file=".env", extra="ignore"
    )

    # --- model -----------------------------------------------------------
    model: str = "claude-opus-4-8"
    max_tokens: int = 16000
    effort: str = "high"  # low | medium | high | xhigh | max

    # --- persona ---------------------------------------------------------
    assistant_name: str = "JARVIS"
    user_name: str = "Boss"
    honorific: str = "sir"
    extra_persona: str = ""  # freeform additions to the system prompt

    # --- storage & history ----------------------------------------------
    db_path: Path = Path("jarvis.db")
    max_history_messages: int = 60  # in-context message cap (soft, turn-aligned)
    reload_history_turns: int = 20  # text turns restored after a restart

    # --- scheduler -------------------------------------------------------
    reminder_poll_seconds: int = 20
    briefing_time: str = ""  # "HH:MM" local time; empty disables the daily briefing

    # --- interfaces ------------------------------------------------------
    telegram_bot_token: str = Field(
        default="",
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "JARVIS_TELEGRAM_BOT_TOKEN"),
    )
    telegram_allowed_user_id: int = Field(
        default=0,
        validation_alias=AliasChoices(
            "TELEGRAM_ALLOWED_USER_ID", "JARVIS_TELEGRAM_ALLOWED_USER_ID"
        ),
    )

    # --- plugins ---------------------------------------------------------
    mcp_config_path: Path = Path("mcp_servers.json")

    def mcp_servers(self) -> list[dict]:
        """Load remote MCP server definitions, if the config file exists.

        Expected format — a JSON array of objects with at least ``name`` and
        ``url``; ``authorization_token`` is optional::

            [{"name": "composio", "url": "https://...", "authorization_token": "..."}]
        """
        if not self.mcp_config_path.exists():
            return []
        data = json.loads(self.mcp_config_path.read_text())
        if not isinstance(data, list):
            raise ValueError(
                f"{self.mcp_config_path} must contain a JSON array of MCP server objects"
            )
        servers = []
        for entry in data:
            if "name" not in entry or "url" not in entry:
                raise ValueError(
                    f"MCP server entry missing 'name' or 'url': {entry!r}"
                )
            server = {"type": "url", "name": entry["name"], "url": entry["url"]}
            if entry.get("authorization_token"):
                server["authorization_token"] = entry["authorization_token"]
            servers.append(server)
        return servers
