from master_character.core import MasterCharacter


async def test_birth_creates_identity_and_lineage(settings):
    character = MasterCharacter(settings)
    identity = await character.birth()

    assert identity.name == "Master Character"
    keys = {agent.key for agent in character.store.list_agents()}
    assert {"trainer", "researcher", "evaluator", "mission_architect", "operator"}.issubset(keys)
    assert any(event["event_type"] == "master_character_booted" for event in character.store.list_events())
