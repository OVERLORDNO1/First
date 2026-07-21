from master_character.core import MasterCharacter
from master_character.domain import MissionStatus, TaskStatus


async def test_command_creates_agents_and_completes_mission(settings):
    character = MasterCharacter(settings)
    directive, mission, tasks = await character.command(
        "Build a working internal research engine",
        success_criteria=["A tested implementation exists"],
        constraints=["No spending"],
    )

    assert directive.statement.startswith("Build")
    assert mission.status is MissionStatus.RUNNING
    assert len(tasks) == 3
    assert character.store.get_active_agent("mission_builder") is not None

    processed = await character.run_until_idle(max_steps=20)
    assert processed
    stored = character.store.list_tasks(mission_id=mission.id)
    assert all(task.status is TaskStatus.COMPLETED for task in stored)
    assert character.store.get_mission(mission.id).status is MissionStatus.COMPLETED
