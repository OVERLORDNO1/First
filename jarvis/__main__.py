"""Entry point: ``jarvis`` (or ``python -m jarvis``)."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from .agent import Jarvis
from .config import Settings
from .memory import Store
from .registry import SkillRegistry


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="J.A.R.V.I.S. — your personal AI assistant.",
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="run the Telegram bot interface instead of the terminal chat",
    )
    parser.add_argument("--verbose", action="store_true", help="debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    load_dotenv()  # make ANTHROPIC_API_KEY et al. from .env visible to the SDK

    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get(
        "ANTHROPIC_AUTH_TOKEN"
    ):
        sys.exit(
            "ANTHROPIC_API_KEY is not set. Export it or put it in a .env file:\n"
            "  ANTHROPIC_API_KEY=sk-ant-..."
        )

    settings = Settings()
    store = Store(settings.db_path)
    jarvis = Jarvis(settings, store, SkillRegistry())

    try:
        if args.telegram:
            from .interfaces.telegram import run_telegram

            run_telegram(jarvis)
        else:
            from .interfaces.cli import run_cli

            run_cli(jarvis)
    finally:
        store.close()


if __name__ == "__main__":
    main()
