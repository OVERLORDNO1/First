# J.A.R.V.I.S.

*Just A Rather Very Intelligent System* — a personal AI assistant that lives in the cloud, remembers everything you tell it, reminds you before things happen, and grows new capabilities through plugins. Powered by Claude.

```
You › remind me about mom's birthday, June 3rd, every year
╭──────────────────────────── JARVIS ────────────────────────────╮
│ Done, sir. I'll remind you every June 3rd — and I've made a    │
│ note of the date itself, in case it comes up sooner.           │
╰────────────────────────────────────────────────────────────────╯
```

## What it does

- **Conversational assistant with a character** — a composed, dry-witted digital
  butler. The persona is fully configurable (name, honorific, extra directives).
- **Persistent memory** — facts, notes, and full conversation history survive
  restarts (SQLite). Tell it something once; it remembers next week.
- **Reminders that actually fire** — one-off and recurring (daily / weekly /
  monthly / yearly), delivered by a background scheduler even mid-conversation.
  Missed occurrences during downtime roll forward correctly.
- **Optional daily briefing** — at a time you choose, JARVIS composes a morning
  briefing and pushes it to you.
- **Plugin architecture, two ways:**
  - **Local skills** — drop in a Python class with a JSON schema; it becomes a
    tool the model can call.
  - **Remote MCP servers** — add Composio (Gmail, Calendar, 300+ apps) or any
    MCP server to `mcp_servers.json`; the tools attach via the Claude API's MCP
    connector with **zero code changes**.
- **Multiple interfaces** — a polished terminal chat today, a Telegram bot for
  access from any phone or browser, and a clean seam for adding more.

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  Interfaces          jarvis/interfaces/                            │
│    CLI (rich)  ·  Telegram (long-poll)  ·  <your channel here>     │
├────────────────────────────────────────────────────────────────────┤
│  Agent core          jarvis/agent.py                               │
│    Claude tool loop · adaptive thinking · prompt caching           │
│    per-turn <context> envelope (time, upcoming reminders)          │
├──────────────────┬──────────────────────┬──────────────────────────┤
│  Skills (local)  │  MCP servers (remote)│  Scheduler               │
│  registry.py     │  mcp_servers.json →  │  scheduler.py            │
│  skills/*        │  Claude MCP connector│  reminders · briefing    │
├──────────────────┴──────────────────────┴──────────────────────────┤
│  Memory              jarvis/memory.py  (SQLite)                    │
│    facts · notes · reminders · conversation history                │
└────────────────────────────────────────────────────────────────────┘
```

Design decisions worth knowing:

- **Prompt caching done right.** The persona/system prompt is byte-stable with a
  `cache_control` breakpoint; all dynamic state (current time, due reminders)
  travels in a per-turn envelope at the *end* of the prompt, so the cached
  prefix is never invalidated.
- **The loop handles the hard stop reasons** — `tool_use`, `pause_turn`
  (server-side tool continuation), and `refusal` — and tool failures are
  reported back to the model with `is_error` instead of crashing the session.
- **History trimming is turn-aligned** so a `tool_use`/`tool_result` pair is
  never severed (which would 400 the API).

## Quickstart

Requires Python 3.10+ and an Anthropic API key ([console.anthropic.com](https://console.anthropic.com)).

```bash
git clone <this repo> && cd First
python -m venv .venv && source .venv/bin/activate
pip install -e .

cp .env.example .env        # then put your ANTHROPIC_API_KEY in it
jarvis                      # terminal chat
```

### Telegram (access from anywhere)

1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.
2. Get your numeric user ID (message [@userinfobot](https://t.me/userinfobot)).
3. In `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC...
   TELEGRAM_ALLOWED_USER_ID=123456789
   ```
4. ```bash
   pip install -e '.[telegram]'
   jarvis --telegram
   ```

Only your user ID is answered — everyone else is silently ignored. The bot uses
long polling (outbound only), so the host needs **no open ports**.

### Docker

```bash
docker build -t jarvis .
docker run --env-file .env -v jarvis-data:/data jarvis --telegram
```

Deploy the same image to Railway / Render / Fly.io / any VPS for 24/7 uptime.

## Configuration

Everything is set via environment variables or `.env` (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | required |
| `JARVIS_MODEL` | `claude-opus-4-8` | Claude model ID |
| `JARVIS_EFFORT` | `high` | `low` \| `medium` \| `high` \| `xhigh` \| `max` |
| `JARVIS_ASSISTANT_NAME` | `JARVIS` | the assistant's name |
| `JARVIS_USER_NAME` | `Boss` | how it thinks of you |
| `JARVIS_HONORIFIC` | `sir` | how it addresses you |
| `JARVIS_EXTRA_PERSONA` | — | extra system-prompt directives |
| `JARVIS_DB_PATH` | `jarvis.db` | SQLite location |
| `JARVIS_BRIEFING_TIME` | *(off)* | `HH:MM` for the daily briefing |
| `JARVIS_MCP_CONFIG_PATH` | `mcp_servers.json` | MCP plugin config |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ALLOWED_USER_ID` | — | Telegram interface |

## Extending JARVIS

### Add a local skill

```python
# jarvis/skills/weather.py
from jarvis.skills.base import Skill, SkillContext

class GetWeather(Skill):
    name = "get_weather"
    description = "Get the current weather. Call when the user asks about weather."
    input_schema = {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    }

    def run(self, ctx: SkillContext, **kwargs) -> str:
        return f"22°C and clear in {kwargs['city']}"  # call a real API here
```

Register it in `jarvis/skills/__init__.py` (`BUILTIN_SKILLS`) and it's live.

### Add remote tools (Composio, Gmail, Calendar, …)

Create `mcp_servers.json` (see `mcp_servers.example.json`):

```json
[
  {
    "name": "composio",
    "url": "https://<your-composio-mcp-endpoint>",
    "authorization_token": "<token if required>"
  }
]
```

Restart JARVIS. The Claude API's MCP connector attaches the server's tools
directly — no local glue code. Composio handles the Gmail/Calendar OAuth on
its side; see [composio.dev](https://composio.dev) for creating an MCP endpoint.

## Development

```bash
pip install -e '.[dev]'
pytest
```

The test suite covers the memory store, skill dispatch, the scheduler
(including recurrence-past-downtime), and the full agent loop against a
scripted fake client — no API key or network needed.

## Security notes

- Keys live in `.env` / host secrets — never in git (`.gitignore` covers it).
- The Telegram interface answers **only** the allowlisted user ID.
- JARVIS is instructed to confirm before hard-to-reverse or outward-facing
  actions; keep that rule when adding skills with side effects.
- Connect personal accounts only — keep work email/accounts out of it.

## Roadmap

- [ ] Composio preset config + guided OAuth setup
- [ ] Voice notes in (transcription → agent)
- [ ] Web chat UI behind Cloudflare Access
- [ ] Proactive email triage (morning digest, draft-don't-send)
- [ ] Semantic memory search (embeddings) once facts outgrow substring search
