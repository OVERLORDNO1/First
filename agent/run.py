"""
run.py — the full autopilot: write → build → post, in one command.

Used by the GitHub Actions cron. You can also run it by hand from your phone
(via the Claude app / a terminal app) any time you want a fresh video.

Flags:
  --dry-run   write the script + captions only (no video, no posting) — great for testing.
"""
import sys
from datetime import date

import generate
import build_video
import post


def main():
    dry = "--dry-run" in sys.argv
    today = date.today().isoformat()

    generate.main()                 # 1. write the story + captions
    if dry:
        print("Dry run — stopping before video/posting.")
        return

    build_video.main(today)         # 2. voiceover + b-roll + assemble
    post.main(today)                # 3. fan out to all platforms


if __name__ == "__main__":
    main()
