#!/usr/bin/env python3
"""
Jarvis — a simple personal assistant with a real brain.

Talks to Claude (Opus 4.8 by default), streams replies, remembers the
conversation while it's running, and keeps a long-term memory file on disk
so it slowly learns about you. Point it at your Obsidian vault later and it
gets a much bigger memory for free.

Run:  python jarvis.py
Quit: type 'exit', 'quit', or press Ctrl-D
"""

import os
import sys
import datetime
from pathlib import Path

import anthropic

# --- Configuration -----------------------------------------------------------

# The brain. Opus 4.8 is the most capable. If you move this to a Raspberry Pi
# and want it cheaper/faster, set JARVIS_MODEL=claude-sonnet-4-6 (or
# claude-haiku-4-5) in your environment.
MODEL = os.environ.get("JARVIS_MODEL", "claude-opus-4-8")

# Where Jarvis keeps what it learns about you. One plain Markdown file for now;
# swap this for a folder in your Obsidian vault when you're ready.
MEMORY_FILE = Path(os.environ.get("JARVIS_MEMORY", "memory.md"))

# A running transcript of your chats, so you never lose a conversation.
LOG_FILE = Path("jarvis_log.md")

MAX_TOKENS = 4096


def build_system_prompt(memory_text: str) -> str:
    """The personality + everything Jarvis currently knows about you."""
    return f"""You are Jarvis, a personal AI assistant — calm, sharp, and a little
witty, in the spirit of Tony Stark's assistant. You speak naturally and get to
the point. You're helpful first, clever second.

Guidelines:
- Be concise. Answer the question, then stop. Don't pad replies with filler.
- When you don't know something, say so plainly instead of guessing.
- You're a thinking partner: offer a recommendation, not an exhaustive survey.
- You have a long-term memory of the person you assist (below). Use it to be
  personal and relevant. When you learn a durable new fact about them — their
  name, preferences, projects, people, routines — call the `remember` tool so
  you don't forget it next time.
- Only remember things that are genuinely worth keeping. Don't remember
  one-off trivia or the contents of this conversation verbatim.

What you currently know about the person you assist:
---
{memory_text.strip() or "(nothing yet — you're just getting to know them)"}
---
"""


# The one tool Jarvis has: the ability to write to its own long-term memory.
REMEMBER_TOOL = {
    "name": "remember",
    "description": (
        "Save a durable fact about the user to long-term memory so you "
        "recall it in future conversations. Use for lasting things: their "
        "name, preferences, ongoing projects, important people, routines."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "fact": {
                "type": "string",
                "description": "A single, self-contained fact to remember, "
                "written in the third person (e.g. 'Hesam is building a "
                "personal AI assistant called Jarvis').",
            }
        },
        "required": ["fact"],
    },
}


def load_memory() -> str:
    if MEMORY_FILE.exists():
        return MEMORY_FILE.read_text(encoding="utf-8")
    return ""


def append_memory(fact: str) -> None:
    """Append a fact to the memory file as a dated bullet."""
    stamp = datetime.date.today().isoformat()
    line = f"- ({stamp}) {fact.strip()}\n"
    with MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def log(role: str, text: str) -> None:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n**{role}** ({stamp}):\n\n{text}\n")


def stream_turn(client, messages, memory_text):
    """
    Run one assistant turn: stream the reply, handle any `remember` tool calls,
    and loop until Claude is done. Returns the final assistant text.

    `messages` is mutated in place to include the full turn (assistant content
    + any tool results), so the conversation stays coherent.
    """
    final_text_parts = []

    while True:
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=build_system_prompt(memory_text),
            tools=[REMEMBER_TOOL],
            messages=messages,
        ) as stream:
            for event in stream:
                if (
                    event.type == "content_block_delta"
                    and event.delta.type == "text_delta"
                ):
                    sys.stdout.write(event.delta.text)
                    sys.stdout.flush()
            response = stream.get_final_message()

        # Record the assistant's turn (text + any tool_use blocks).
        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:
            if block.type == "text":
                final_text_parts.append(block.text)

        if response.stop_reason != "tool_use":
            print()  # newline after the streamed reply
            break

        # Jarvis wants to remember something. Do it, then feed the result back.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "remember":
                fact = block.input["fact"]
                append_memory(fact)
                memory_text = load_memory()
                print(f"\n  \033[2m· remembered: {fact}\033[0m")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Saved to long-term memory.",
                    }
                )
        messages.append({"role": "user", "content": tool_results})

    return "".join(final_text_parts), memory_text


def main() -> None:
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        print(
            "No API key found. Set your Anthropic key first:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.Anthropic()
    memory_text = load_memory()
    messages = []

    print("\033[1mJarvis\033[0m online. (type 'exit' to quit)\n")

    while True:
        try:
            user_input = input("\033[1myou ›\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "bye"}:
            print("Goodbye.")
            break

        messages.append({"role": "user", "content": user_input})
        log("you", user_input)

        print("\033[1mjarvis ›\033[0m ", end="", flush=True)
        try:
            reply, memory_text = stream_turn(client, messages, memory_text)
        except anthropic.APIError as e:
            print(f"\n[error talking to Claude: {e}]")
            # Drop the failed user turn so the history stays valid.
            messages.pop()
            continue

        log("jarvis", reply)
        print()


if __name__ == "__main__":
    main()
