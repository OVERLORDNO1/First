from __future__ import annotations

from pathlib import Path

import pytest

from master_character.config import Settings


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    project_root = Path(__file__).parents[1]
    monkeypatch.chdir(project_root)
    return Settings(
        MASTER_PROVIDER="mock",
        MASTER_DB_PATH=tmp_path / "master.db",
        MASTER_WORKSPACE=tmp_path / "workspace",
        MASTER_RESEARCH_INTERVAL_MINUTES=0,
        MASTER_AUTO_PROMOTE_PROMPT_MUTATIONS=False,
    )
