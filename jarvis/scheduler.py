"""Background services: reminder delivery and the optional daily briefing.

Interface-agnostic — the owning interface passes a ``notify`` callable
(print to terminal, send a Telegram message, ...) and the scheduler calls it
whenever something fires.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .memory import Store

log = logging.getLogger(__name__)

Notify = Callable[[str], None]


class ReminderService:
    """Polls the reminder queue and delivers due reminders."""

    def __init__(
        self,
        store: Store,
        notify: Notify,
        poll_seconds: int = 20,
        briefing_time: str = "",
        briefing: Callable[[], str] | None = None,
    ):
        self.store = store
        self.notify = notify
        self._scheduler = BackgroundScheduler(daemon=True)
        self._scheduler.add_job(
            self.poll_once, "interval", seconds=poll_seconds, id="reminder-poll"
        )
        if briefing_time and briefing is not None:
            hour, minute = self._parse_hhmm(briefing_time)
            self._scheduler.add_job(
                lambda: self.notify(briefing()),
                CronTrigger(hour=hour, minute=minute),
                id="daily-briefing",
            )

    @staticmethod
    def _parse_hhmm(value: str) -> tuple[int, int]:
        hour, _, minute = value.partition(":")
        return int(hour), int(minute or 0)

    def poll_once(self) -> int:
        """Deliver every due reminder. Returns the number delivered."""
        delivered = 0
        for reminder in self.store.pending_reminders(before=datetime.now()):
            suffix = ""
            next_due = self.store.complete_or_reschedule(reminder)
            if next_due is not None:
                suffix = f" (next: {next_due.strftime('%a %Y-%m-%d %H:%M')})"
            try:
                self.notify(f"⏰ Reminder: {reminder.text}{suffix}")
            except Exception:  # noqa: BLE001 — delivery failure must not kill the poller
                log.exception("failed to deliver reminder #%s", reminder.id)
            delivered += 1
        return delivered

    def start(self) -> None:
        self._scheduler.start()

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
