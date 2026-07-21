from fastapi.testclient import TestClient

from master_character.api import create_app


def test_api_birth_and_state(settings):
    with TestClient(create_app(settings)) as client:
        response = client.post("/api/birth")
        assert response.status_code == 200
        assert response.json()["name"] == "Master Character"
        state = client.get("/api/state")
        assert state.status_code == 200
        assert state.json()["identity"]["name"] == "Master Character"
