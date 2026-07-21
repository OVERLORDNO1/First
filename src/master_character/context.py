from __future__ import annotations

import yaml

from master_character.config import Settings
from master_character.store import Store


class ContextBuilder:
    def __init__(self, settings: Settings, store: Store):
        self.settings = settings
        self.store = store

    def charter(self) -> str:
        charter = self.settings.charter_path.read_text(encoding="utf-8")
        rules = yaml.safe_load(self.settings.rules_path.read_text(encoding="utf-8"))
        return charter + "\n\n# IMMUTABLE RULES\n" + yaml.safe_dump(rules, sort_keys=False)

    def snapshot_text(self) -> str:
        identity = self.store.get_identity()
        directive = self.store.get_active_directive()
        missions = self.store.list_missions(limit=10)
        tasks = self.store.list_tasks(limit=30)
        agents = self.store.list_agents()
        approvals = self.store.list_approvals()
        return (
            "# CURRENT STATE\n"
            f"Identity: {identity.model_dump_json(indent=2) if identity else 'none'}\n"
            f"Active directive: {directive.model_dump_json(indent=2) if directive else 'none'}\n"
            f"Missions: {[{'id': m.id, 'title': m.title, 'status': m.status.value} for m in missions]}\n"
            f"Tasks: {[{'id': t.id, 'title': t.title, 'status': t.status.value} for t in tasks]}\n"
            f"Agents: {[{'key': a.key, 'version': a.version, 'role': a.role} for a in agents]}\n"
            f"Pending approvals: {len(approvals)}\n"
            f"Daily cost USD: {self.store.daily_cost():.4f}\n"
        )
