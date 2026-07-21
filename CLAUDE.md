import sqlite3

from master_character.core import MasterCharacter


async def test_event_log_rejects_update_and_delete(settings):
    character = MasterCharacter(settings)
    await character.birth()

    with character.store.connection() as db:
        event_id = db.execute("SELECT id FROM events ORDER BY id LIMIT 1").fetchone()["id"]
        try:
            db.execute("UPDATE events SET event_type='tampered' WHERE id=?", (event_id,))
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Event update should have been rejected")
