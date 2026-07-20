"""Persistent storage: facts, notes, reminders, and conversation history.

A single SQLite file, no ORM. Every public method is safe to call from the
scheduler thread as well as the main thread (each call uses the shared
connection guarded by SQLite's serialized mode).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta

RECURRENCES = ("daily", "weekly", "monthly", "yearly")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,
    tags       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reminders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,
    due_at     TEXT NOT NULL,
    recurrence TEXT NOT NULL DEFAULT '',
    status     TEXT NOT NULL DEFAULT 'pending',  -- pending | done | cancelled
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT NOT NULL,   -- user | assistant
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Reminder:
    id: int
    text: str
    due_at: datetime
    recurrence: str
    status: str


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


class Store:
    def __init__(self, path: Path | str):
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- facts ------------------------------------------------------------

    def remember(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO facts(key, value, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key.strip().lower(), value.strip(), _iso(datetime.now())),
        )
        self._conn.commit()

    def recall(self, query: str = "") -> list[tuple[str, str]]:
        if query:
            like = f"%{query.strip().lower()}%"
            rows = self._conn.execute(
                "SELECT key, value FROM facts WHERE key LIKE ? OR lower(value) LIKE ? ORDER BY key",
                (like, like),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT key, value FROM facts ORDER BY key"
            ).fetchall()
        return [(r["key"], r["value"]) for r in rows]

    def forget(self, key: str) -> bool:
        cur = self._conn.execute(
            "DELETE FROM facts WHERE key=?", (key.strip().lower(),)
        )
        self._conn.commit()
        return cur.rowcount > 0

    # -- notes ------------------------------------------------------------

    def add_note(self, text: str, tags: str = "") -> int:
        cur = self._conn.execute(
            "INSERT INTO notes(text, tags, created_at) VALUES(?,?,?)",
            (text.strip(), tags.strip().lower(), _iso(datetime.now())),
        )
        self._conn.commit()
        return cur.lastrowid

    def search_notes(self, query: str = "") -> list[tuple[int, str, str, str]]:
        if query:
            like = f"%{query.strip().lower()}%"
            rows = self._conn.execute(
                "SELECT * FROM notes WHERE lower(text) LIKE ? OR tags LIKE ? "
                "ORDER BY id DESC LIMIT 50",
                (like, like),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM notes ORDER BY id DESC LIMIT 50"
            ).fetchall()
        return [(r["id"], r["text"], r["tags"], r["created_at"]) for r in rows]

    # -- reminders --------------------------------------------------------

    def add_reminder(self, text: str, due_at: datetime, recurrence: str = "") -> int:
        recurrence = recurrence.strip().lower()
        if recurrence and recurrence not in RECURRENCES:
            raise ValueError(
                f"recurrence must be one of {RECURRENCES} or empty, got {recurrence!r}"
            )
        cur = self._conn.execute(
            "INSERT INTO reminders(text, due_at, recurrence, created_at) VALUES(?,?,?,?)",
            (text.strip(), _iso(due_at), recurrence, _iso(datetime.now())),
        )
        self._conn.commit()
        return cur.lastrowid

    def _row_to_reminder(self, r: sqlite3.Row) -> Reminder:
        return Reminder(
            id=r["id"],
            text=r["text"],
            due_at=datetime.fromisoformat(r["due_at"]),
            recurrence=r["recurrence"],
            status=r["status"],
        )

    def pending_reminders(self, before: datetime | None = None) -> list[Reminder]:
        sql = "SELECT * FROM reminders WHERE status='pending'"
        args: tuple = ()
        if before is not None:
            sql += " AND due_at <= ?"
            args = (_iso(before),)
        sql += " ORDER BY due_at"
        return [self._row_to_reminder(r) for r in self._conn.execute(sql, args)]

    def cancel_reminder(self, reminder_id: int) -> bool:
        cur = self._conn.execute(
            "UPDATE reminders SET status='cancelled' WHERE id=? AND status='pending'",
            (reminder_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def complete_or_reschedule(self, reminder: Reminder) -> datetime | None:
        """Mark a fired reminder done, or roll it to its next occurrence.

        Returns the next due time for recurring reminders, else ``None``.
        """
        if reminder.recurrence:
            step = {
                "daily": relativedelta(days=1),
                "weekly": relativedelta(weeks=1),
                "monthly": relativedelta(months=1),
                "yearly": relativedelta(years=1),
            }[reminder.recurrence]
            next_due = reminder.due_at + step
            # Skip occurrences already in the past (e.g. after downtime).
            now = datetime.now()
            while next_due <= now:
                next_due += step
            self._conn.execute(
                "UPDATE reminders SET due_at=? WHERE id=?",
                (_iso(next_due), reminder.id),
            )
            self._conn.commit()
            return next_due
        self._conn.execute(
            "UPDATE reminders SET status='done' WHERE id=?", (reminder.id,)
        )
        self._conn.commit()
        return None

    # -- conversation history --------------------------------------------

    def append_message(self, role: str, text: str) -> None:
        self._conn.execute(
            "INSERT INTO history(role, text, created_at) VALUES(?,?,?)",
            (role, text, _iso(datetime.now())),
        )
        self._conn.commit()

    def recent_messages(self, limit: int = 20) -> list[tuple[str, str]]:
        rows = self._conn.execute(
            "SELECT role, text FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [(r["role"], r["text"]) for r in reversed(rows)]
