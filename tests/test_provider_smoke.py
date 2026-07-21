from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import master_character.providers.factory as factory
from master_character.cli import app
from master_character.domain import ModelUsage
from master_character.store import Store

runner = CliRunner()


class FakeProvider:
    def __init__(self, cost_usd: float):
        self.cost_usd = cost_usd

    async def structured(self, *, response_model, correlation_id=None, **kwargs):
        usage = ModelUsage(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            input_tokens=200,
            output_tokens=20,
            calls=1,
            stop_reason="tool_use",
            correlation_id=correlation_id,
            estimated_cost_usd=self.cost_usd,
        )
        return response_model(message="smoke-ok"), usage


@pytest.fixture
def smoke_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "smoke.db"
    monkeypatch.setenv("MASTER_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-secret")
    monkeypatch.setenv("MASTER_DB_PATH", str(db_path))
    monkeypatch.setenv("MASTER_WORKSPACE", str(tmp_path / "workspace"))
    return db_path


def test_smoke_succeeds_with_nonzero_ledger(smoke_env, monkeypatch):
    monkeypatch.setattr(factory, "create_provider", lambda s, st=None: FakeProvider(0.0012))
    result = runner.invoke(app, ["provider-smoke", "--budget-usd", "0.10"])
    assert result.exit_code == 0, result.output
    assert "smoke-ok" in result.output
    assert "sk-test-secret" not in result.output
    store = Store(smoke_env)
    assert store.daily_cost() == pytest.approx(0.0012)


def test_smoke_fails_on_zero_cost_success(smoke_env, monkeypatch):
    monkeypatch.setattr(factory, "create_provider", lambda s, st=None: FakeProvider(0.0))
    result = runner.invoke(app, ["provider-smoke", "--budget-usd", "0.10"])
    assert result.exit_code == 1
    assert "zero cost" in result.output


def test_smoke_fails_on_budget_breach(smoke_env, monkeypatch):
    monkeypatch.setattr(factory, "create_provider", lambda s, st=None: FakeProvider(0.5))
    result = runner.invoke(app, ["provider-smoke", "--budget-usd", "0.10"])
    assert result.exit_code == 1
    assert "breached" in result.output


def test_smoke_refuses_without_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("MASTER_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("MASTER_DB_PATH", str(tmp_path / "smoke.db"))
    monkeypatch.setenv("MASTER_WORKSPACE", str(tmp_path / "workspace"))
    monkeypatch.chdir(tmp_path)  # avoid picking up a repo-root .env
    result = runner.invoke(app, ["provider-smoke"])
    assert result.exit_code == 2
