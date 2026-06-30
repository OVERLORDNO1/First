#!/usr/bin/env python3
"""
Jarvis — web interface.

A browser chat UI for the same Jarvis brain as jarvis.py: Claude under the
hood, streaming replies, and the same memory.md long-term memory.

Run it anywhere:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    python app.py            # opens a local web app at http://localhost:7860

Deploy it free (so you can use it from your phone, now and from home):
    Push this repo to a Hugging Face Space (SDK: gradio) and add your
    ANTHROPIC_API_KEY as a Space secret. See README.md.
"""

import os

import gradio as gr
import anthropic

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Reuse the exact same brain + memory as the terminal version.
from jarvis import (
    MODEL,
    MAX_TOKENS,
    REMEMBER_TOOL,
    build_system_prompt,
    load_memory,
    append_memory,
)

client = anthropic.Anthropic() if (
    os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
) else None


def chat(message, history):
    """
    Streaming chat handler for Gradio.

    `history` is a list of {"role", "content"} dicts (type="messages").
    Yields the assistant reply as it streams in.
    """
    if client is None:
        yield (
            "⚠️ No API key configured. Set the `ANTHROPIC_API_KEY` environment "
            "variable (or, on Hugging Face Spaces, add it as a Space secret)."
        )
        return

    memory_text = load_memory()

    # Rebuild the Claude message list from the visible chat history.
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})

    shown = ""  # everything displayed to the user so far this turn

    while True:
        try:
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
                        shown += event.delta.text
                        yield shown
                response = stream.get_final_message()
        except anthropic.APIError as e:
            yield shown + f"\n\n_[error talking to Claude: {e}]_"
            return

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return

        # Handle any `remember` tool calls, then let Claude continue.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "remember":
                fact = block.input["fact"]
                append_memory(fact)
                memory_text = load_memory()
                shown += f"\n\n_· remembered: {fact}_\n\n"
                yield shown
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Saved to long-term memory.",
                    }
                )
        messages.append({"role": "user", "content": tool_results})


demo = gr.ChatInterface(
    fn=chat,
    title="🤖 Jarvis",
    description="Your personal assistant. He remembers what matters about you.",
    examples=[
        "Hey Jarvis, introduce yourself.",
        "Remember that I prefer short answers.",
        "What do you know about me so far?",
    ],
)

if __name__ == "__main__":
    # 0.0.0.0 so it works inside containers / on a Pi / on a Space.
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
