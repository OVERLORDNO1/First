"""Terminal chat interface, built on rich."""

from __future__ import annotations

import anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..agent import Jarvis
from ..scheduler import ReminderService

_HELP = """\
Commands:
  /help        show this help
  /reminders   list pending reminders
  /facts       list everything JARVIS remembers
  /quit        exit

Anything else is a message to JARVIS."""


def run_cli(jarvis: Jarvis) -> None:
    console = Console()
    name = jarvis.settings.assistant_name

    def notify(text: str) -> None:
        console.print()
        console.print(Panel(text, title=name, border_style="cyan"))

    service = ReminderService(
        jarvis.store,
        notify,
        poll_seconds=jarvis.settings.reminder_poll_seconds,
        briefing_time=jarvis.settings.briefing_time,
        briefing=lambda: jarvis.converse("Give me my daily briefing."),
    )
    service.start()

    console.print(Panel(jarvis.greeting(), title=name, border_style="cyan"))
    console.print("[dim]Type /help for commands, /quit to exit.[/dim]\n")

    try:
        while True:
            try:
                user_text = console.input("[bold green]You ›[/bold green] ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_text:
                continue
            if user_text in ("/quit", "/exit"):
                break
            if user_text == "/help":
                console.print(_HELP)
                continue
            if user_text == "/reminders":
                reminders = jarvis.store.pending_reminders()
                if not reminders:
                    console.print("[dim]No pending reminders.[/dim]")
                for r in reminders:
                    console.print(
                        f"  #{r.id} {r.due_at.strftime('%a %Y-%m-%d %H:%M')}: {r.text}"
                    )
                continue
            if user_text == "/facts":
                facts = jarvis.store.recall()
                if not facts:
                    console.print("[dim]Memory is empty.[/dim]")
                for key, value in facts:
                    console.print(f"  {key}: {value}")
                continue

            try:
                with console.status(f"[cyan]{name} is thinking…[/cyan]"):
                    reply = jarvis.converse(user_text)
                console.print(Panel(Markdown(reply), title=name, border_style="cyan"))
            except anthropic.AuthenticationError:
                console.print(
                    "[red]Invalid or missing ANTHROPIC_API_KEY — set it in .env "
                    "or the environment.[/red]"
                )
            except anthropic.RateLimitError:
                console.print("[yellow]Rate limited — give it a moment and retry.[/yellow]")
            except anthropic.APIConnectionError:
                console.print("[red]Network error reaching the Claude API.[/red]")
            except anthropic.APIStatusError as exc:
                console.print(f"[red]API error {exc.status_code}: {exc.message}[/red]")
    finally:
        service.stop()
        console.print(f"\n[dim]{name}: Until next time.[/dim]")
