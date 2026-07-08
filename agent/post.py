"""
post.py — pushes the finished video + captions to ALL platforms via one scheduler call.

Default provider: Postiz (open-source, self-hostable free, has a clean API).
Swap `post_postiz` for `post_blotato` if you go with Blotato instead — same idea.

Both work the same way: you connect TikTok / Instagram / YouTube / Facebook ONCE inside
the scheduler's dashboard (from your phone), and after that this script just hands it the
video + caption and it fans out to every platform.
"""
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


def load(date_str: str):
    d = ROOT / "content" / date_str
    cfg_path = ROOT / "agent" / "config.json"
    if not cfg_path.exists():
        cfg_path = ROOT / "agent" / "config.example.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    captions = json.loads((d / "captions.json").read_text(encoding="utf-8"))
    return cfg, captions, d / "final.mp4"


def post_postiz(cfg, captions, video: Path):
    base = cfg["scheduler"]["base_url"].rstrip("/")
    key = os.environ[cfg["scheduler"]["api_key_env"]]
    headers = {"Authorization": key}

    # 1) upload the video file to Postiz
    with open(video, "rb") as f:
        up = requests.post(f"{base}/api/public/v1/upload",
                           headers=headers, files={"file": f}, timeout=300)
    up.raise_for_status()
    media_id = up.json().get("id")

    # 2) create one post targeting all connected channels, with per-platform captions
    payload = {
        "type": "now",
        "media": [media_id],
        "posts": [
            {"platform": "tiktok",    "content": captions["tiktok"]["caption"] + "\n" + " ".join(captions["tiktok"]["hashtags"])},
            {"platform": "instagram", "content": captions["instagram"]["caption"] + "\n" + " ".join(captions["instagram"]["hashtags"])},
            {"platform": "youtube",   "content": captions["youtube"]["title"] + "\n" + captions["youtube"]["description"]},
            {"platform": "facebook",  "content": captions["facebook"]["caption"]},
        ],
    }
    r = requests.post(f"{base}/api/public/v1/posts", headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    print("🚀 posted to all connected platforms:", r.json().get("id", "ok"))


def deliver_manual(captions, video: Path):
    """
    FREE semi-auto mode. No posting — just build a clean, copy-paste 'post-pack'
    next to the video so you can post it yourself in ~2 minutes from your phone.
    """
    out = video.parent / "POST_PACK.txt"
    L = ["🎬  YOUR VIDEO IS READY — post it in a couple of taps.",
         f"Video file: {video.name}", "", "=" * 46, ""]

    L += ["📱 TIKTOK",
          captions["tiktok"]["caption"],
          " ".join(captions["tiktok"]["hashtags"]), "", "-" * 46, ""]
    L += ["📸 INSTAGRAM REELS",
          captions["instagram"]["caption"],
          " ".join(captions["instagram"]["hashtags"]), "", "-" * 46, ""]
    L += ["▶️ YOUTUBE SHORTS",
          "Title: " + captions["youtube"]["title"],
          captions["youtube"]["description"],
          " ".join(captions["youtube"]["hashtags"]), "", "-" * 46, ""]
    L += ["👥 FACEBOOK",
          captions["facebook"]["caption"], "", "=" * 46]

    out.write_text("\n".join(L), encoding="utf-8")
    print(f"✅ post-pack ready → {out}")
    print("   Open POST_PACK.txt, then upload the video to each app with the caption.")


def main(date_str: str):
    cfg, captions, video = load(date_str)
    if not video.exists():
        sys.exit(f"No video at {video} — run build_video.py first.")
    provider = cfg["scheduler"]["provider"]
    if provider == "manual":
        deliver_manual(captions, video)
    elif provider == "postiz":
        post_postiz(cfg, captions, video)
    else:
        sys.exit(f"Add a post_{provider}() function for provider '{provider}'.")


if __name__ == "__main__":
    from datetime import date
    main(sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat())
