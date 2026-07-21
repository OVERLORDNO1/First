from master_character.core import MasterCharacter
from master_character.domain import ApprovalStatus, MutationStatus


async def test_growth_task_stages_mutation_for_approval(settings):
    character = MasterCharacter(settings)
    await character.birth()
    await character.run_until_idle(max_steps=20)

    approvals = character.store.list_approvals()
    assert len(approvals) == 1
    assert approvals[0].action == "promote_mutation"
    assert approvals[0].status is ApprovalStatus.PENDING
