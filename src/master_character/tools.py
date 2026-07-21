from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from master_character.store import Store

ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler


class ToolRegistry:
    def __init__(self, workspace: Path, store: Store, allowed: list[str]):
        self.workspace = workspace.resolve()
        self.store = store
        self.allowed = set(allowed)
        self.tools: dict[str, Tool] = {}
        self._register_builtins()

    def _safe_path(self, raw: str) -> Path:
        path = (self.workspace / raw).resolve()
        if path != self.workspace and self.workspace not in path.parents:
            raise PermissionError("Path escapes the controlled workspace.")
        return path

    def _register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def _register_builtins(self) -> None:
        async def workspace_list(args: dict[str, Any]) -> Any:
            path = self._safe_path(args.get("path", "."))
            if not path.exists():
                return []
            if path.is_file():
                return [str(path.relative_to(self.workspace))]
            return [
                str(item.relative_to(self.workspace))
                for item in sorted(path.rglob("*"))
                if item.is_file()
            ][:1000]

        async def workspace_read(args: dict[str, Any]) -> Any:
            path = self._safe_path(args["path"])
            if not path.is_file():
                raise FileNotFoundError(args["path"])
            return path.read_text(encoding="utf-8")[:250_000]

        async def workspace_write(args: dict[str, Any]) -> Any:
            path = self._safe_path(args["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args["content"], encoding="utf-8")
            return {"path": str(path.relative_to(self.workspace)), "bytes": path.stat().st_size}

        async def memory_search(args: dict[str, Any]) -> Any:
            return self.store.search_memory(args["query"], int(args.get("limit", 10)))

        async def system_state(args: dict[str, Any]) -> Any:
            identity = self.store.get_identity()
            directive = self.store.get_active_directive()
            return {
                "identity": identity.model_dump(mode="json") if identity else None,
                "active_directive": directive.model_dump(mode="json") if directive else None,
                "agents": [agent.model_dump(mode="json") for agent in self.store.list_agents()],
                "missions": [mission.model_dump(mode="json") for mission in self.store.list_missions(20)],
                "pending_approvals": len(self.store.list_approvals()),
                "daily_cost_usd": self.store.daily_cost(),
            }

        self._register(Tool(
            "workspace_list",
            "List files in the controlled mission workspace.",
            {"type": "object", "properties": {"path": {"type": "string", "default": "."}}, "additionalProperties": False},
            workspace_list,
        ))
        self._register(Tool(
            "workspace_read",
            "Read a UTF-8 file inside the controlled workspace.",
            {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False},
            workspace_read,
        ))
        self._register(Tool(
            "workspace_write",
            "Write a UTF-8 artifact inside the controlled workspace. Cannot modify source or secrets.",
            {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
                "additionalProperties": False,
            },
            workspace_write,
        ))
        self._register(Tool(
            "memory_search",
            "Search persistent internal memory for previous goals, decisions, findings, and outcomes.",
            {
                "type": "object",
                "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}},
                "required": ["query"],
                "additionalProperties": False,
            },
            memory_search,
        ))
        self._register(Tool(
            "system_state",
            "Return a compact current-state snapshot.",
            {"type": "object", "properties": {}, "additionalProperties": False},
            system_state,
        ))

    def definitions(self) -> list[dict[str, Any]]:
        return [
            {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema}
            for name, tool in sorted(self.tools.items())
            if name in self.allowed
        ]

    async def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self.allowed:
            return {"ok": False, "error": f"Tool not allowed for this agent: {name}"}
        tool = self.tools.get(name)
        if not tool:
            return {"ok": False, "error": f"Unknown tool: {name}"}
        try:
            return {"ok": True, "result": await tool.handler(arguments)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
