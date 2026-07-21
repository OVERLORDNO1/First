from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from master_character.config import Settings
from master_character.core import MasterCharacter


class CommandRequest(BaseModel):
    statement: str
    success_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    priority: int = 100


class ApprovalResolution(BaseModel):
    approve: bool
    note: str = ""


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    character = MasterCharacter(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await character.birth()
        yield

    app = FastAPI(title="Master Character", version="2.0.0", lifespan=lifespan)

    @app.get("/", response_class=HTMLResponse)
    async def root() -> str:
        return """
        <!doctype html><html><body style="font-family:system-ui;max-width:900px;margin:40px auto">
        <h1>Master Character v2</h1>
        <p>Main body online. Use the JSON API or CLI to issue commands and resolve approvals.</p>
        <pre>POST /api/command\nPOST /api/step\nGET /api/state\nGET /api/approvals</pre>
        </body></html>
        """

    @app.post("/api/birth")
    async def birth():
        return (await character.birth()).model_dump(mode="json")

    @app.post("/api/command")
    async def command(request: CommandRequest):
        directive, mission, tasks = await character.command(
            request.statement,
            request.success_criteria,
            request.constraints,
            request.priority,
        )
        return {
            "directive": directive.model_dump(mode="json"),
            "mission": mission.model_dump(mode="json"),
            "tasks": [task.model_dump(mode="json") for task in tasks],
        }

    @app.post("/api/step")
    async def step(max_tasks: int | None = None):
        tasks = await character.step(max_tasks=max_tasks)
        return [task.model_dump(mode="json") for task in tasks]

    @app.get("/api/state")
    async def state():
        return character.snapshot().model_dump(mode="json")

    @app.get("/api/approvals")
    async def approvals():
        return [item.model_dump(mode="json") for item in character.store.list_approvals()]

    @app.post("/api/approvals/{approval_id}")
    async def resolve(approval_id: str, request: ApprovalResolution):
        try:
            approval = character.resolve_approval(approval_id, request.approve, request.note)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Approval not found") from exc
        return approval.model_dump(mode="json")

    return app
