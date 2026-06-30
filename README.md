---
title: Jarvis
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: gradio
app_file: app.py
pinned: false
---

# Jarvis

A simple personal AI assistant with a real brain — a tiny, personal version of
Tony Stark's Jarvis. It runs on the Claude API, streams its replies, and keeps a
long-term memory file so it slowly learns about you.

It comes in two flavours that share the same brain and memory:

- **`jarvis.py`** — a terminal chat (run it in a console).
- **`app.py`** — a **web interface** you open in a browser. This is the one you
  deploy to a free host so you can use Jarvis **now and from home, on any device.**

## Use it now (free, from your phone or any browser)

The web version is built to run on a **free Hugging Face Space**:

1. Create a free account at <https://huggingface.co>.
2. Click **New → Space**. Choose **SDK: Gradio**, give it a name.
3. Upload these files (or connect this GitHub repo): `app.py`, `jarvis.py`,
   `requirements.txt`, `memory.md`, and this `README.md`.
4. In the Space, go to **Settings → Secrets** and add a secret named
   `ANTHROPIC_API_KEY` with your Anthropic key.
5. The Space builds itself and gives you a public URL. Open it on your phone or
   laptop — that's your Jarvis, reachable anywhere.

The little YAML block at the very top of this file is what tells Hugging Face to
run it as a Gradio app — leave it there.

> Other free options that work the same way: **Render**, **Railway**, or
> **Streamlit Community Cloud**. Hugging Face Spaces is the easiest because the
> chat UI and the public URL come for free.

## Use it at home

Exactly the same code runs on your own machine or a Raspberry Pi:

```bash
pip install -r requirements.txt

# Either export your key:
export ANTHROPIC_API_KEY=sk-ant-...
# ...or copy .env.example to .env and put your key there (loaded automatically):
cp .env.example .env

python app.py      # web UI at http://localhost:7860
# or
python jarvis.py   # terminal chat
```

### Terminal commands

In the terminal version (`jarvis.py`), a few slash-commands are available:

| Command    | What it does                                  |
| ---------- | --------------------------------------------- |
| `/help`    | List commands                                 |
| `/memory`  | Show everything Jarvis remembers about you    |
| `/forget`  | Forget the most recent thing it learned       |
| `/clear`   | Clear the current conversation (keeps memory) |
| `exit`     | Quit                                          |

## How the memory works

`memory.md` holds durable facts about you. Jarvis loads it into its prompt every
turn, so it always "knows" what's there. When it learns something lasting (your
name, a preference, a project) it calls its `remember` tool and appends a dated
line to `memory.md`. You can also edit the file by hand.

> Note: on a free cloud Space the filesystem resets on rebuilds, so long-term
> memory survives a session but not a redeploy. For permanent memory, run it at
> home, or point `JARVIS_MEMORY` at a synced location (e.g. your Obsidian vault).

## Configuration

| Variable            | Default            | What it does                              |
| ------------------- | ------------------ | ----------------------------------------- |
| `ANTHROPIC_API_KEY` | —                  | Your Anthropic API key (required)         |
| `JARVIS_MODEL`      | `claude-opus-4-8`  | Model. `claude-sonnet-4-6` / `claude-haiku-4-5` for cheaper/faster. |
| `JARVIS_MEMORY`     | `memory.md`        | Path to the long-term memory file.        |

## How this relates to OpenJarvis

[OpenJarvis](https://github.com/open-jarvis/OpenJarvis) is a separate, larger
project that runs **local models on your own hardware** (via Ollama). It's a
great **private, at-home** option for later — install it on your PC or Pi and run
its `jarvis` command. But it needs real local compute, so it can't be hosted on a
free cloud space for "use it now from anywhere."

This project takes the other route: the heavy thinking runs on Anthropic's
servers, so the app itself is tiny and **fits free hosting with a built-in chat
UI** — which is exactly what gets you a Jarvis you can use now *and* at home.

## Where this is going

- **Obsidian** — point `JARVIS_MEMORY` at a note in your vault for richer memory.
- **Raspberry Pi** — single app, light footprint; drop to a smaller model to keep
  an always-on assistant cheap.
- **Voice** — wrap speech-to-text / text-to-speech around the chat loop.
