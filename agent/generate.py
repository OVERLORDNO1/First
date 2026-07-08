"""
generate.py — the BRAIN.

Picks today's pillar + template, then asks the LLM to write a full story-driven
video script package and per-platform captions. Saves them to content/<date>/.

This runs fine on its own (no video needed) so you can test the writing first.
"""
import json
import os
import random
import sys
from datetime import date
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent

PILLARS = ["The Reframe", "The Small Shift", "The Hard Truth", "The Origin Story", "The Nervous System"]
TEMPLATES = ["A", "B", "C", "D", "E"]


def read(*parts) -> str:
    return (ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def build_context() -> str:
    """Feed the agent its brand + strategy so every script is on-voice."""
    return "\n\n".join([
        "# BRAND\n" + read("brand", "brand.md"),
        "# STRATEGY\n" + read("strategy", "content-strategy.md"),
        "# STORY TEMPLATES\n" + read("strategy", "story-templates.md"),
    ])


def ask(client, model, system, user) -> str:
    msg = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


def extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found in model output:\n" + text)
    return json.loads(text[start:end + 1])


def main():
    cfg = json.loads(read("agent", "config.json")) if ROOT.joinpath("agent", "config.json").exists() \
        else json.loads(read("agent", "config.example.json"))
    api_key = os.environ.get(cfg["llm"]["api_key_env"])
    if not api_key:
        sys.exit(f"Missing {cfg['llm']['api_key_env']} in environment.")

    client = anthropic.Anthropic(api_key=api_key)
    model = cfg["llm"]["model"]
    context = build_context()

    pillar = random.choice(PILLARS)
    template = random.choice(TEMPLATES)

    print(f"Writing today's video → pillar: {pillar} | template: {template}")

    script_pkg = extract_json(ask(
        client, model,
        system=read("prompts", "script-writer.md") + "\n\n# REFERENCE MATERIAL\n" + context,
        user=f"Write today's video. Use pillar '{pillar}' and template '{template}'. Output only the JSON.",
    ))

    captions = extract_json(ask(
        client, model,
        system=read("prompts", "caption-writer.md"),
        user="Write captions for this script package:\n\n" + json.dumps(script_pkg, indent=2),
    ))

    outdir = ROOT / "content" / date.today().isoformat()
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "script.json").write_text(json.dumps(script_pkg, indent=2), encoding="utf-8")
    (outdir / "captions.json").write_text(json.dumps(captions, indent=2), encoding="utf-8")

    print(f"✅ Saved script + captions to {outdir}")
    print(f"\nHOOK: {script_pkg.get('hook')}")
    return outdir


if __name__ == "__main__":
    main()
