from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    provider: str = Field(default="mock", alias="MASTER_PROVIDER")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com", alias="ANTHROPIC_BASE_URL"
    )
    anthropic_version: str = Field(default="2023-06-01", alias="ANTHROPIC_VERSION")

    reasoning_model: str = Field(
        default="claude-sonnet-4-20250514", alias="MASTER_REASONING_MODEL"
    )
    worker_model: str = Field(
        default="claude-3-5-haiku-20241022", alias="MASTER_WORKER_MODEL"
    )
    critic_model: str = Field(
        default="claude-sonnet-4-20250514", alias="MASTER_CRITIC_MODEL"
    )

    db_path: Path = Field(default=Path("./data/master_character.db"), alias="MASTER_DB_PATH")
    workspace: Path = Field(default=Path("./workspace"), alias="MASTER_WORKSPACE")
    host: str = Field(default="127.0.0.1", alias="MASTER_HOST")
    port: int = Field(default=8765, alias="MASTER_PORT")
    tick_seconds: int = Field(default=10, alias="MASTER_TICK_SECONDS")
    research_interval_minutes: int = Field(
        default=60, alias="MASTER_RESEARCH_INTERVAL_MINUTES"
    )
    max_tasks_per_step: int = Field(default=3, alias="MASTER_MAX_TASKS_PER_STEP")
    max_model_turns: int = Field(default=8, alias="MASTER_MAX_MODEL_TURNS")
    max_task_cost_usd: float = Field(default=0.75, alias="MASTER_MAX_TASK_COST_USD")
    max_daily_cost_usd: float = Field(default=5.0, alias="MASTER_MAX_DAILY_COST_USD")
    prompt_cache: bool = Field(default=True, alias="MASTER_PROMPT_CACHE")
    auto_promote_prompt_mutations: bool = Field(
        default=False, alias="MASTER_AUTO_PROMOTE_PROMPT_MUTATIONS"
    )
    log_level: str = Field(default="INFO", alias="MASTER_LOG_LEVEL")

    @property
    def root(self) -> Path:
        return Path.cwd()

    @property
    def charter_path(self) -> Path:
        return self.root / "charter" / "MASTER_CHARACTER_CHARTER.md"

    @property
    def rules_path(self) -> Path:
        return self.root / "config" / "immutable_rules.yaml"

    @property
    def capability_path(self) -> Path:
        return self.root / "config" / "capabilities.yaml"

    @property
    def candidate_workspace(self) -> Path:
        return self.workspace / "candidates"

    def ensure_directories(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.candidate_workspace.mkdir(parents=True, exist_ok=True)
