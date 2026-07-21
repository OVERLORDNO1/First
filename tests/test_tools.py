from master_character.core import MasterCharacter
from master_character.tools import ToolRegistry


async def test_workspace_cannot_escape(settings):
    character = MasterCharacter(settings)
    await character.birth()
    registry = ToolRegistry(settings.workspace, character.store, ["workspace_write"])
    result = await registry.execute("workspace_write", {"path": "../escape.txt", "content": "no"})
    assert result["ok"] is False
    assert not (settings.workspace.parent / "escape.txt").exists()
