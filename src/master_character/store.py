from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Iterator

from master_character.domain import (
    AgentSpec,
    ApprovalRequest,
    ApprovalStatus,
    CharacterIdentity,
    MasterDirective,
    Mission,
    MissionStatus,
    ModelUsage,
    MutationProposal,
    Task,
    TaskStatus,
)
from master_character.util import utc_now


class Store:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS identity (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS directives (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    directive_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    agent_key TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    active INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(agent_key, version)
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    correlation_id TEXT NOT NULL,
                    mission_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 50,
                    lease_owner TEXT,
                    lease_until TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mutations (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    estimated_cost_usd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correlation_id TEXT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TRIGGER IF NOT EXISTS events_no_update
                BEFORE UPDATE ON events
                BEGIN
                    SELECT RAISE(ABORT, 'events are append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS events_no_delete
                BEFORE DELETE ON events
                BEGIN
                    SELECT RAISE(ABORT, 'events are append-only');
                END;

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, priority, created_at);
                CREATE INDEX IF NOT EXISTS idx_tasks_mission ON tasks(mission_id);
                CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id, id);
                CREATE INDEX IF NOT EXISTS idx_agents_key ON agents(agent_key, version DESC);
                """
            )

    def append_event(self, event_type: str, payload: dict, correlation_id: str | None = None) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT INTO events(correlation_id,event_type,payload,created_at) VALUES(?,?,?,?)",
                (correlation_id, event_type, json.dumps(payload, default=str), utc_now().isoformat()),
            )

    def list_events(self, limit: int = 50) -> list[dict]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT id,correlation_id,event_type,payload,created_at "
                "FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "correlation_id": row["correlation_id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def save_identity(self, identity: CharacterIdentity) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO identity(id,payload,updated_at) VALUES(?,?,?)",
                (identity.id, identity.model_dump_json(), utc_now().isoformat()),
            )

    def get_identity(self) -> CharacterIdentity | None:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM identity LIMIT 1").fetchone()
        return CharacterIdentity.model_validate_json(row["payload"]) if row else None

    def save_directive(self, directive: MasterDirective) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO directives(id,status,priority,payload,created_at) "
                "VALUES(?,?,?,?,?)",
                (
                    directive.id,
                    directive.status.value,
                    directive.priority,
                    directive.model_dump_json(),
                    directive.created_at.isoformat(),
                ),
            )

    def get_active_directive(self) -> MasterDirective | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT payload FROM directives WHERE status=? ORDER BY priority DESC, created_at ASC LIMIT 1",
                ("active",),
            ).fetchone()
        return MasterDirective.model_validate_json(row["payload"]) if row else None

    def save_mission(self, mission: Mission) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO missions(id,directive_id,status,payload,created_at) "
                "VALUES(?,?,?,?,?)",
                (
                    mission.id,
                    mission.directive_id,
                    mission.status.value,
                    mission.model_dump_json(),
                    mission.created_at.isoformat(),
                ),
            )

    def get_mission(self, mission_id: str) -> Mission | None:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM missions WHERE id=?", (mission_id,)).fetchone()
        return Mission.model_validate_json(row["payload"]) if row else None

    def list_missions(self, limit: int = 50) -> list[Mission]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT payload FROM missions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [Mission.model_validate_json(row["payload"]) for row in rows]

    def save_agent(self, agent: AgentSpec) -> None:
        with self.connection() as db:
            if agent.active:
                db.execute("UPDATE agents SET active=0 WHERE agent_key=?", (agent.key,))
            db.execute(
                "INSERT OR REPLACE INTO agents(id,agent_key,version,active,payload,created_at) "
                "VALUES(?,?,?,?,?,?)",
                (
                    agent.id,
                    agent.key,
                    agent.version,
                    1 if agent.active else 0,
                    agent.model_dump_json(),
                    agent.created_at.isoformat(),
                ),
            )

    def get_agent(self, agent_id: str) -> AgentSpec | None:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM agents WHERE id=?", (agent_id,)).fetchone()
        return AgentSpec.model_validate_json(row["payload"]) if row else None

    def get_active_agent(self, key: str) -> AgentSpec | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT payload FROM agents WHERE agent_key=? AND active=1 "
                "ORDER BY version DESC LIMIT 1",
                (key,),
            ).fetchone()
        return AgentSpec.model_validate_json(row["payload"]) if row else None

    def list_agents(self, active_only: bool = True) -> list[AgentSpec]:
        query = "SELECT payload FROM agents"
        params: tuple = ()
        if active_only:
            query += " WHERE active=1"
        query += " ORDER BY agent_key,version DESC"
        with self.connection() as db:
            rows = db.execute(query, params).fetchall()
        return [AgentSpec.model_validate_json(row["payload"]) for row in rows]

    def save_task(self, task: Task, priority: int = 50) -> None:
        task.updated_at = utc_now()
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO tasks(id,correlation_id,mission_id,status,priority,"
                "lease_owner,lease_until,payload,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    task.id,
                    task.correlation_id,
                    task.mission_id,
                    task.status.value,
                    priority,
                    task.lease_owner,
                    task.lease_until.isoformat() if task.lease_until else None,
                    task.model_dump_json(),
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                ),
            )

    def get_task(self, task_id: str) -> Task | None:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM tasks WHERE id=?", (task_id,)).fetchone()
        return Task.model_validate_json(row["payload"]) if row else None

    def list_tasks(self, mission_id: str | None = None, limit: int = 200) -> list[Task]:
        query = "SELECT payload FROM tasks"
        params: list = []
        if mission_id:
            query += " WHERE mission_id=?"
            params.append(mission_id)
        query += " ORDER BY created_at ASC LIMIT ?"
        params.append(limit)
        with self.connection() as db:
            rows = db.execute(query, tuple(params)).fetchall()
        return [Task.model_validate_json(row["payload"]) for row in rows]

    def lease_ready_tasks(self, worker_id: str, limit: int, lease_seconds: int = 120) -> list[Task]:
        now = utc_now()
        lease_until = now + timedelta(seconds=lease_seconds)
        leased: list[Task] = []
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            expired = db.execute(
                "SELECT payload FROM tasks WHERE status=? AND lease_until IS NOT NULL AND lease_until<?",
                (TaskStatus.RUNNING.value, now.isoformat()),
            ).fetchall()
            for row in expired:
                task = Task.model_validate_json(row["payload"])
                task.status = TaskStatus.QUEUED
                task.lease_owner = None
                task.lease_until = None
                task.error = "Previous lease expired; task was requeued."
                db.execute(
                    "UPDATE tasks SET status=?,lease_owner=NULL,lease_until=NULL,payload=?,updated_at=? WHERE id=?",
                    (task.status.value, task.model_dump_json(), now.isoformat(), task.id),
                )

            rows = db.execute(
                "SELECT payload,priority FROM tasks WHERE status=? ORDER BY priority DESC,created_at ASC",
                (TaskStatus.QUEUED.value,),
            ).fetchall()
            completed_ids = {
                row["id"]
                for row in db.execute(
                    "SELECT id FROM tasks WHERE status=?", (TaskStatus.COMPLETED.value,)
                ).fetchall()
            }
            for row in rows:
                if len(leased) >= limit:
                    break
                task = Task.model_validate_json(row["payload"])
                if not set(task.dependency_ids).issubset(completed_ids):
                    continue
                task.status = TaskStatus.RUNNING
                task.lease_owner = worker_id
                task.lease_until = lease_until
                task.attempts += 1
                task.updated_at = now
                updated = db.execute(
                    "UPDATE tasks SET status=?,lease_owner=?,lease_until=?,payload=?,updated_at=? "
                    "WHERE id=? AND status=?",
                    (
                        task.status.value,
                        worker_id,
                        lease_until.isoformat(),
                        task.model_dump_json(),
                        now.isoformat(),
                        task.id,
                        TaskStatus.QUEUED.value,
                    ),
                )
                if updated.rowcount == 1:
                    leased.append(task)
        return leased

    def save_approval(self, approval: ApprovalRequest) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO approvals(id,status,payload,created_at) VALUES(?,?,?,?)",
                (
                    approval.id,
                    approval.status.value,
                    approval.model_dump_json(),
                    approval.created_at.isoformat(),
                ),
            )

    def get_approval(self, approval_id: str) -> ApprovalRequest | None:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM approvals WHERE id=?", (approval_id,)).fetchone()
        return ApprovalRequest.model_validate_json(row["payload"]) if row else None

    def list_approvals(self, pending_only: bool = True) -> list[ApprovalRequest]:
        query = "SELECT payload FROM approvals"
        params: tuple = ()
        if pending_only:
            query += " WHERE status=?"
            params = (ApprovalStatus.PENDING.value,)
        query += " ORDER BY created_at ASC"
        with self.connection() as db:
            rows = db.execute(query, params).fetchall()
        return [ApprovalRequest.model_validate_json(row["payload"]) for row in rows]

    def save_mutation(self, mutation: MutationProposal) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO mutations(id,status,payload,created_at) VALUES(?,?,?,?)",
                (
                    mutation.id,
                    mutation.status.value,
                    mutation.model_dump_json(),
                    mutation.created_at.isoformat(),
                ),
            )

    def add_memory(self, category: str, content: str, metadata: dict | None = None) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT INTO memories(category,content,metadata,created_at) VALUES(?,?,?,?)",
                (category, content, json.dumps(metadata or {}, default=str), utc_now().isoformat()),
            )

    def search_memory(self, query: str, limit: int = 10) -> list[dict]:
        pattern = f"%{query}%"
        with self.connection() as db:
            rows = db.execute(
                "SELECT id,category,content,metadata,created_at FROM memories "
                "WHERE content LIKE ? OR metadata LIKE ? ORDER BY id DESC LIMIT ?",
                (pattern, pattern, limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "category": row["category"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def record_usage(self, usage: ModelUsage) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT INTO usage(provider,model,input_tokens,output_tokens,estimated_cost_usd,created_at) "
                "VALUES(?,?,?,?,?,?)",
                (
                    usage.provider,
                    usage.model,
                    usage.input_tokens,
                    usage.output_tokens,
                    usage.estimated_cost_usd,
                    usage.created_at.isoformat(),
                ),
            )

    def daily_cost(self) -> float:
        today = utc_now().date().isoformat()
        with self.connection() as db:
            row = db.execute(
                "SELECT COALESCE(SUM(estimated_cost_usd),0) AS total FROM usage "
                "WHERE substr(created_at,1,10)=?",
                (today,),
            ).fetchone()
        return float(row["total"])

    def update_mission_from_tasks(self, mission_id: str) -> Mission | None:
        mission = self.get_mission(mission_id)
        if mission is None:
            return None
        tasks = self.list_tasks(mission_id=mission_id)
        if tasks and all(task.status is TaskStatus.COMPLETED for task in tasks):
            mission.status = MissionStatus.COMPLETED
            mission.completed_at = utc_now()
            self.save_mission(mission)
        elif any(task.status is TaskStatus.FAILED and task.attempts >= task.max_attempts for task in tasks):
            mission.status = MissionStatus.FAILED
            mission.completed_at = utc_now()
            self.save_mission(mission)
        elif any(task.status is TaskStatus.WAITING_APPROVAL for task in tasks):
            mission.status = MissionStatus.BLOCKED
            self.save_mission(mission)
        elif tasks:
            mission.status = MissionStatus.RUNNING
            self.save_mission(mission)
        return mission
