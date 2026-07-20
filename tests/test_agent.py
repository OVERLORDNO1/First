"""Agent-loop tests against a scripted fake Anthropic client — no network."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from jarvis.agent import Jarvis
from jarvis.memory import Store


def text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def tool_block(name: str, tool_input: dict, block_id: str = "toolu_1") -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", name=name, input=tool_input, id=block_id)


def response(stop_reason: str, *blocks) -> SimpleNamespace:
    return SimpleNamespace(stop_reason=stop_reason, content=list(blocks))


class FakeClient:
    """Yields scripted responses and records every request payload."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests: list[dict] = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        # Snapshot: the agent mutates its messages list after the call returns.
        kwargs["messages"] = list(kwargs["messages"])
        self.requests.append(kwargs)
        return self._responses.pop(0)


@pytest.fixture()
def make_jarvis(settings):
    def factory(responses):
        store = Store(settings.db_path)
        client = FakeClient(responses)
        return Jarvis(settings, store, client=client), client, store

    return factory


def test_plain_reply(make_jarvis):
    jarvis, client, _ = make_jarvis(
        [response("end_turn", text_block("Good evening, sir."))]
    )
    assert jarvis.converse("hello") == "Good evening, sir."
    req = client.requests[0]
    # system prompt is cached, thinking adaptive, tools exposed
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert req["thinking"] == {"type": "adaptive"}
    assert any(t["name"] == "add_reminder" for t in req["tools"])
    # context envelope rides along with the user text
    assert "<context>" in req["messages"][-1]["content"]


def test_tool_loop_executes_skill_and_feeds_result_back(make_jarvis):
    due = (datetime.now() + timedelta(days=1)).replace(microsecond=0)
    jarvis, client, store = make_jarvis(
        [
            response(
                "tool_use",
                text_block("One moment."),
                tool_block("add_reminder", {"text": "Dentist", "due_at": due.isoformat()}),
            ),
            response("end_turn", text_block("Done, sir. Reminder set.")),
        ]
    )
    reply = jarvis.converse("remind me about the dentist tomorrow")
    assert reply == "Done, sir. Reminder set."
    # the skill really ran
    assert store.pending_reminders()[0].text == "Dentist"
    # tool result was sent back with the matching id
    tool_results = client.requests[1]["messages"][-1]["content"]
    assert tool_results[0]["type"] == "tool_result"
    assert tool_results[0]["tool_use_id"] == "toolu_1"
    assert "Reminder #1" in tool_results[0]["content"]


def test_tool_error_reported_with_is_error(make_jarvis):
    jarvis, client, _ = make_jarvis(
        [
            response(
                "tool_use",
                tool_block("add_reminder", {"text": "x", "due_at": "garbage"}),
            ),
            response("end_turn", text_block("Apologies — that time made no sense.")),
        ]
    )
    jarvis.converse("remind me at garbage o'clock")
    tool_results = client.requests[1]["messages"][-1]["content"]
    assert tool_results[0]["is_error"] is True


def test_refusal_handled(make_jarvis):
    jarvis, _, _ = make_jarvis([response("refusal")])
    assert "decline" in jarvis.converse("do the bad thing")


def test_pause_turn_resumes(make_jarvis):
    jarvis, client, _ = make_jarvis(
        [
            response("pause_turn", text_block("working...")),
            response("end_turn", text_block("Finished.")),
        ]
    )
    assert jarvis.converse("long task") == "Finished."
    assert len(client.requests) == 2


def test_history_persists_across_restart(settings):
    store = Store(settings.db_path)
    jarvis = Jarvis(
        settings, store, client=FakeClient([response("end_turn", text_block("Noted."))])
    )
    jarvis.converse("my name is Hesam")
    # simulate restart: fresh agent over the same store
    jarvis2 = Jarvis(
        settings, store, client=FakeClient([response("end_turn", text_block("Hesam."))])
    )
    roles = [(m["role"], m["content"]) for m in jarvis2.messages]
    assert ("user", "my name is Hesam") in roles
    assert ("assistant", "Noted.") in roles


def test_mcp_servers_route_through_beta(settings, tmp_path):
    settings.mcp_config_path.write_text(
        '[{"name": "composio", "url": "https://mcp.composio.dev/x"}]'
    )
    store = Store(settings.db_path)

    beta_requests: list[dict] = []

    def beta_create(**kwargs):
        beta_requests.append(kwargs)
        return response("end_turn", text_block("Via MCP."))

    client = SimpleNamespace(
        messages=SimpleNamespace(create=None),  # must not be used
        beta=SimpleNamespace(messages=SimpleNamespace(create=beta_create)),
    )
    jarvis = Jarvis(settings, store, client=client)
    assert jarvis.converse("check my email") == "Via MCP."
    req = beta_requests[0]
    assert req["betas"] == ["mcp-client-2025-11-20"]
    assert req["mcp_servers"][0]["name"] == "composio"
    assert {"type": "mcp_toolset", "mcp_server_name": "composio"} in req["tools"]
