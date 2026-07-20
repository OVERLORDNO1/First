from __future__ import annotations

import pytest

from jarvis.config import Settings
from jarvis.memory import Store


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(
        db_path=tmp_path / "test.db",
        mcp_config_path=tmp_path / "mcp_servers.json",
        _env_file=None,
    )


@pytest.fixture()
def store(settings) -> Store:
    s = Store(settings.db_path)
    yield s
    s.close()
