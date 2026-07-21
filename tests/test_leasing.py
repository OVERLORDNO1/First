from master_character.core import MasterCharacter


async def test_task_cannot_be_leased_twice(settings):
    character = MasterCharacter(settings)
    _, mission, _ = await character.command("Build a test artifact")

    first = character.store.lease_ready_tasks("worker-a", 1)
    second = character.store.lease_ready_tasks("worker-b", 1)

    assert len(first) == 1
    assert all(task.id != first[0].id for task in second)
