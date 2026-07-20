# Personal AI Assistant — Build Plan

A cloud-hosted personal assistant agent you can reach from any browser (including a locked-down work laptop), that reminds you about dates, handles your email/calendar through Composio, and remembers things about you.

---

## 1. The core idea

Your laptop is just a window. The agent itself runs 24/7 on a small cloud server:

```
┌─────────────────────────── Cloud (always on) ───────────────────────────┐
│                                                                         │
│  Telegram Bot / Web Chat  ──►  Agent service (Claude Agent SDK)         │
│                                      │                                  │
│                    ┌─────────────────┼──────────────────┐               │
│                    ▼                 ▼                  ▼               │
│              Composio MCP      Scheduler (cron)    SQLite memory        │
│           (Gmail, Calendar,   (reminders, morning  (facts, prefs,       │
│            Notion, etc.)       digest, follow-ups)  reminder queue)     │
└─────────────────────────────────────────────────────────────────────────┘
```

You talk to it from Chrome (Telegram Web or a small web UI). It also talks to
you *first* — pinging you when a reminder fires or when an important email
lands.

---

## 2. Stack recommendation

| Piece | Choice | Why |
|---|---|---|
| Brain | **Claude API** via **Claude Agent SDK** (Python or TS) | Agentic loop, tool use, and MCP support are built in — you don't hand-roll the loop |
| Email / Calendar / apps | **Composio** (MCP or SDK) | Managed OAuth for Gmail, Google Calendar, Notion, 300+ apps. Free tier is enough to start |
| Chat interface | **Telegram bot** | Zero frontend code; works on web.telegram.org (Chrome at work), phone, desktop. Push notifications for free |
| Reminders | **APScheduler / node-cron** + SQLite table | The agent inserts reminder rows; the scheduler fires them and messages you on Telegram |
| Memory | **SQLite** (+ a `memory.md` the agent can edit) | Simple, durable, no extra service |
| Hosting | See §3 | ~$0–6/month |

### Why Telegram first, web UI later
A custom web chat needs hosting, auth, and UI work before you can even test the
agent. A Telegram bot is ~30 lines of glue, is already secured (allowlist your
own Telegram user ID), and works everywhere Chrome works. Add a fancy web UI in
Phase 4 if you still want one.

### Alternatives considered
- **n8n (self-hosted or cloud)** — good low-code option: AI Agent node + Gmail/Calendar nodes + cron triggers. Faster to click together, less flexible when you want real agent behavior. Fine fallback if you'd rather not code.
- **Just Claude.ai + connectors** — cheapest (you already pay for Claude; Gmail/Calendar connectors + scheduled tasks exist), but it's not *your* agent and you can't customize its behavior, memory, or proactive pings the way you want.

---

## 3. Where to host it

| Option | Cost | Notes |
|---|---|---|
| **Railway / Render / Fly.io** | ~$5/mo (Render has a free tier that sleeps) | Easiest: `git push` to deploy, secrets UI, logs. **Recommended to start** |
| **Hetzner VPS (CX22)** | ~€4/mo | Cheapest reliable always-on box; you manage it yourself (Docker) |
| **Oracle Cloud Always Free** | $0 | Free ARM VM forever; signup is finicky but genuinely free |

Start on Railway/Render for speed. If costs bug you later, move the Docker
container to Hetzner or Oracle — the app won't care.

**Work-laptop rule:** never expose an unauthenticated web endpoint. With
Telegram there's nothing to expose at all (the bot polls outward). If you add a
web UI later, put it behind **Cloudflare Tunnel + Cloudflare Access** (Google
login) — works in any browser, no VPN client to install on the work machine.

---

## 4. Phases

### Phase 1 — Walking skeleton (a weekend)
1. Create the repo scaffold (Python: `claude-agent-sdk`, `python-telegram-bot`, `composio`).
2. Telegram bot: forward your messages to the agent, reply with its answer. Allowlist your Telegram user ID.
3. Connect Composio: authorize Gmail + Google Calendar once via its OAuth flow.
4. System prompt: who you are, timezone, how it should behave.
5. Deploy to Railway/Render with secrets: `ANTHROPIC_API_KEY`, `COMPOSIO_API_KEY`, `TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_USER_ID`.

**Done when:** from Chrome at work you can ask "what's on my calendar tomorrow?" and "summarize my unread emails" and get real answers.

### Phase 2 — Reminders & memory
1. SQLite: `reminders(id, due_at, text, recurring, done)` and `facts(key, value)`.
2. Give the agent tools: `add_reminder`, `list_reminders`, `remember`, `recall`.
3. APScheduler loop: every minute, fire due reminders as Telegram messages.
4. Recurring dates (birthdays, renewals) with lead-time warnings ("Sara's birthday in 3 days").

**Done when:** "remind me about mom's birthday June 3 every year" survives a redeploy and pings you on time.

### Phase 3 — Proactive email handling
1. Morning digest (cron 7:30am): unread email summary + today's calendar + due reminders, as one Telegram message.
2. Composio Gmail trigger (new email) → agent triages: important → ping you with a summary + suggested reply; noise → ignore/label.
3. Draft-don't-send rule: the agent writes drafts; **you** hit send (at least until you trust it).

**Done when:** you stop opening Gmail first thing in the morning.

### Phase 4 — Nice-to-haves
- Web chat UI behind Cloudflare Access (if Telegram isn't enough).
- Voice notes in → transcription → agent.
- More Composio apps: Notion, Todoist, Slack, WhatsApp.
- Weekly review: "here's what you asked me to track this week."

---

## 5. Costs (monthly)

| Item | Cost |
|---|---|
| Hosting | $0–6 |
| Claude API (personal-assistant usage, Sonnet-class model) | ~$3–15 pay-as-you-go |
| Composio | Free tier |
| Telegram | Free |
| **Total** | **~$5–20/mo** |

Tip: use a Sonnet-class model for routine triage and only escalate to a bigger
model for hard tasks — that keeps API cost near the bottom of that range.

## 6. Security checklist

- [ ] Telegram handler rejects any user ID that isn't yours.
- [ ] All keys live in the host's secrets manager, never in git.
- [ ] Composio scopes: start read-only for Gmail; add send/modify later.
- [ ] Agent drafts emails but doesn't send without confirmation (Phase 3 rule).
- [ ] No public HTTP port unless it's behind Cloudflare Access.
- [ ] Don't wire it to work email/accounts from the work laptop — personal accounts only.

## 7. What you need before Phase 1

1. **Anthropic API key** — console.anthropic.com (separate from your Claude subscription).
2. **Composio account** — composio.dev, connect Gmail + Google Calendar.
3. **Telegram bot token** — message @BotFather, `/newbot`.
4. **Railway or Render account** — sign in with GitHub, point it at this repo.
