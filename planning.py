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
