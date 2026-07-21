from __future__ import annotations

import asyncio
import json

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from master_character.api import create_app
from master_character.config import Settings
from master_character.core import MasterCharacter

app = typer.Typer(name="master-character", no_args_is_help=True)
console = Console()


def run(coro):
    return asyncio.run(coro)


@app.command()
def birth() -> None:
    character = MasterCharacter(Settings())
    identity = run(character.birth())
    console.print(
        Panel.fit(
            f"{identity.name} v{identity.version} is online.\n"
            "Master, what do you want me to accomplish?",
            title="MASTER CHARACTER",
        )
    )
    console.print("Children: " + ", ".join(agent.key for agent in character.store.list_agents()))


@app.command()
def command(
    statement: str = typer.Argument(...),
    success: list[str] = typer.Option([], "--success"),
    constraint: list[str] = typer.Option([], "--constraint"),
    priority: int = typer.Option(100, "--priority"),
) -> None:
    character = MasterCharacter(Settings())
    directive, mission, tasks = run(
        character.command(statement, success, constraint, priority)
    )
    console.print(Panel.fit(mission.title, title="MISSION CREATED"))
    console.print(f"Directive: {directive.id}")
    console.print(f"Mission: {mission.id}")
    console.print(f"Tasks: {len(tasks)}")


@app.command()
def step(
    max_tasks: int | None = typer.Option(None, "--max-tasks", "-n"),
    until_idle: bool = typer.Option(False, "--until-idle"),
) -> None:
    character = MasterCharacter(Settings())
    processed = run(
        character.run_until_idle() if until_idle else character.step(max_tasks=max_tasks)
    )
    table = Table(title="Heartbeat results")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Attempts")
    for task in processed:
        table.add_row(task.title, task.status.value, str(task.attempts))
    console.print(table)


@app.command()
def status() -> None:
    character = MasterCharacter(Settings())
    console.print_json(character.snapshot().model_dump_json(indent=2))


@app.command()
def approvals() -> None:
    character = MasterCharacter(Settings())
    character.store.initialize()
    table = Table(title="Pending approvals")
    table.add_column("ID")
    table.add_column("Action")
    table.add_column("Risk")
    table.add_column("Reason")
    for item in character.store.list_approvals():
        table.add_row(item.id, item.action, item.risk_level.value, item.reason)
    console.print(table)


@app.command()
def approve(
    approval_id: str,
    reject: bool = typer.Option(False, "--reject"),
    note: str = typer.Option("", "--note"),
) -> None:
    character = MasterCharacter(Settings())
    resolved = character.resolve_approval(approval_id, not reject, note)
    console.print_json(resolved.model_dump_json(indent=2))


@app.command()
def events(limit: int = typer.Option(50, "--limit", "-n")) -> None:
    character = MasterCharacter(Settings())
    character.store.initialize()
    console.print_json(json.dumps(character.store.list_events(limit), indent=2))


@app.command("provider-smoke")
def provider_smoke(
    budget_usd: float = typer.Option(0.10, "--budget-usd", min=0.0),
) -> None:
    """Run one minimal live structured call with a hard cost ceiling."""
    from pydantic import BaseModel

    from master_character.domain import ModelTier
    from master_character.errors import ProviderError
    from master_character.providers.factory import create_provider
    from master_character.store import Store
    from master_character.util import new_id

    settings = Settings()
    if settings.provider.lower().strip() != "anthropic":
        console.print("[red]provider-smoke requires MASTER_PROVIDER=anthropic.[/red]")
        raise typer.Exit(code=2)
    if not settings.anthropic_api_key:
        console.print("[red]ANTHROPIC_API_KEY is not set in the local environment.[/red]")
        raise typer.Exit(code=2)

    settings.ensure_directories()
    store = Store(settings.db_path)
    store.initialize()
    provider = create_provider(settings, store)
    correlation_id = new_id("smoke")

    class SmokeResult(BaseModel):
        message: str

    async def smoke():
        return await provider.structured(
            system="You are a smoke test. Do not use any tool except emit_structured_result.",
            prompt=(
                "This is a provider smoke test. Call emit_structured_result exactly once "
                'with {"message": "smoke-ok"}.'
            ),
            response_model=SmokeResult,
            tier=ModelTier.WORKER,
            max_turns=2,
            cost_budget_usd=budget_usd,
            correlation_id=correlation_id,
        )

    try:
        result, usage = run(smoke())
    except ProviderError as exc:
        console.print(f"[red]Smoke test failed ({exc.category}): {exc}[/red]")
        raise typer.Exit(code=1) from exc

    store.record_usage(usage)
    table = Table(title="Provider smoke result")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("provider", usage.provider)
    table.add_row("model", usage.model)
    table.add_row("calls", str(usage.calls))
    table.add_row("retries", str(usage.retries))
    table.add_row("stop_reason", str(usage.stop_reason))
    table.add_row("input_tokens", str(usage.input_tokens))
    table.add_row("output_tokens", str(usage.output_tokens))
    table.add_row("cache_creation_input_tokens", str(usage.cache_creation_input_tokens))
    table.add_row("cache_read_input_tokens", str(usage.cache_read_input_tokens))
    table.add_row("estimated_cost_usd", f"{usage.estimated_cost_usd:.6f}")
    table.add_row("budget_usd", f"{budget_usd:.6f}")
    table.add_row("result", result.message)
    console.print(table)

    if usage.estimated_cost_usd <= 0:
        console.print(
            "[red]Successful live call recorded zero cost; ledger is untrustworthy.[/red]"
        )
        raise typer.Exit(code=1)
    if usage.estimated_cost_usd > budget_usd:
        console.print("[red]Recorded cost breached the configured budget.[/red]")
        raise typer.Exit(code=1)
    console.print("[green]Smoke test passed with a non-zero, in-budget cost ledger.[/green]")


@app.command()
def daemon() -> None:
    character = MasterCharacter(Settings())
    run(character.run_forever())


@app.command()
def serve(
    host: str | None = typer.Option(None),
    port: int | None = typer.Option(None),
) -> None:
    settings = Settings()
    uvicorn.run(
        create_app(settings),
        host=host or settings.host,
        port=port or settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    app()
