# Jarvis

A simple personal AI assistant with a real brain — think a tiny, terminal
version of Tony Stark's Jarvis. It runs on the Claude API, streams its replies,
remembers your conversation while it's running, and keeps a long-term memory
file on disk so it slowly learns about you.

## What it does

- **Chats** with you in the terminal, streaming replies token by token.
- **Has a brain** — powered by Claude Opus 4.8 (configurable).
- **Remembers you** — a `memory.md` file holds durable facts about you. Jarvis
  writes to it on its own (via a `remember` tool) and you can edit it by hand.
- **Keeps a log** — every conversation is saved to `jarvis_log.md`.

## Setup

You need an Anthropic API key and Python 3.9+.

```bash
# 1. Install the one dependency
pip install -r requirements.txt

# 2. Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Run it
python jarvis.py
```

Type `exit` (or Ctrl-D) to quit.

## Configuration

Set these environment variables to tweak behaviour:

| Variable            | Default            | What it does                              |
| ------------------- | ------------------ | ----------------------------------------- |
| `ANTHROPIC_API_KEY` | —                  | Your Anthropic API key (required)         |
| `JARVIS_MODEL`      | `claude-opus-4-8`  | The model. Use `claude-sonnet-4-6` or `claude-haiku-4-5` for cheaper/faster. |
| `JARVIS_MEMORY`     | `memory.md`        | Path to the long-term memory file.        |

## How the memory works

Jarvis loads `memory.md` into its system prompt at the start of every reply, so
it always "knows" what's in there. When it learns something durable about you
(your name, a preference, a project), it calls its `remember` tool, which
appends a dated bullet to `memory.md`.

You'll see a quiet `· remembered: ...` note when this happens.

## Where this is going

- **Obsidian** — point `JARVIS_MEMORY` at a notes file in your vault, or extend
  Jarvis to read multiple notes, and it gains a much richer picture of you.
- **Raspberry Pi / always-on** — it's a single Python file with one dependency,
  so it'll happily run on a Pi. Drop `JARVIS_MODEL` to a smaller model to keep
  costs down for an always-on assistant.
- **Voice** — add speech-to-text and text-to-speech around the chat loop to talk
  to it out loud.
