"""
build_video.py — turns a script package into a finished 9:16 video.

Pipeline (all free/cheap, runs in GitHub Actions):
  1. Voiceover  → ElevenLabs (or OpenAI TTS) reads the full script.
  2. B-roll     → downloads cinematic vertical stock clips from Pexels for each beat.
  3. Assemble   → ffmpeg stitches clips to the voiceover length, adds bold captions + music,
                  and crops everything to 1080x1920.

Output: content/<date>/final.mp4

NOTE: This is the piece we test together live the first time (voice + ffmpeg settings
depend on your chosen voice and vibe). Everything is modular so we can swap providers.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


def load_cfg():
    p = ROOT / "agent" / "config.json"
    if not p.exists():
        p = ROOT / "agent" / "config.example.json"
    return json.loads(p.read_text(encoding="utf-8"))


def make_voiceover(cfg, script_text: str, out: Path):
    """ElevenLabs TTS → mp3. Swap this function for OpenAI TTS if you prefer."""
    key = os.environ[cfg["voiceover"]["api_key_env"]]
    voice_id = cfg["voiceover"]["voice_id"]
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={"text": script_text, "model_id": "eleven_multilingual_v2",
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3}},
        timeout=120,
    )
    r.raise_for_status()
    out.write_bytes(r.content)
    print(f"🎙️  voiceover → {out}")


def fetch_broll(cfg, query: str, out: Path):
    """Grab one cinematic vertical clip from Pexels for a beat."""
    key = os.environ[cfg["broll"]["api_key_env"]]
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": key},
        params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 1},
        timeout=60,
    )
    r.raise_for_status()
    vids = r.json().get("videos", [])
    if not vids:
        print(f"⚠️  no clip for '{query}' — trying a fallback term")
        return None
    # pick a mid-resolution vertical file
    files = sorted(vids[0]["video_files"], key=lambda f: f.get("height", 0))
    link = files[-1]["link"]
    out.write_bytes(requests.get(link, timeout=120).content)
    print(f"🎞️  b-roll '{query}' → {out}")
    return out


def assemble(clips, voiceover: Path, out: Path):
    """ffmpeg: concat clips, scale/crop to 1080x1920, lay the voiceover on top."""
    listfile = out.parent / "clips.txt"
    listfile.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(listfile),
        "-i", str(voiceover),
        "-vf", vf,
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ final video → {out}")


def main(date_str: str):
    cfg = load_cfg()
    d = ROOT / "content" / date_str
    script = json.loads((d / "script.json").read_text(encoding="utf-8"))

    make_voiceover(cfg, script["script"], d / "voice.mp3")

    clips = []
    for i, beat in enumerate(script["beats"]):
        clip = fetch_broll(cfg, beat["broll"], d / f"broll_{i}.mp4")
        if clip:
            clips.append(clip)

    if not clips:
        sys.exit("No b-roll downloaded — check PEXELS_API_KEY and search terms.")

    assemble(clips, d / "voice.mp3", d / "final.mp4")
    # Captions overlay + music are added in a second ffmpeg pass — see docs/captions.md


if __name__ == "__main__":
    from datetime import date
    main(sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat())
