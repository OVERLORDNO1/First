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


def _secs(t: str) -> tuple[float, float]:
    """'13-21s' -> (13.0, 21.0). Tolerant of stray spaces / the trailing 's'."""
    a, b = t.replace("s", "").split("-")
    return float(a), float(b)


def _esc(text: str) -> str:
    """Escape a caption for ffmpeg drawtext."""
    return text.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"’").replace("%", r"\%")


def caption_filters(beats) -> str:
    """One drawtext per beat — big bold captions, timed to each beat, fading in."""
    parts = []
    for beat in beats:
        start, end = _secs(beat["t"])
        txt = _esc(beat.get("onscreen_text", "").upper())
        if not txt:
            continue
        parts.append(
            "drawtext=text='{t}'"
            ":fontcolor=white:fontsize=76:font=sans:borderw=2:bordercolor=black@0.6"
            ":box=1:boxcolor=black@0.28:boxborderw=26"
            ":x=(w-text_w)/2:y=h*0.62"
            ":enable='between(t,{s},{e})'".format(t=txt, s=start, e=end)
        )
    return ",".join(parts)


def assemble(clips, voiceover: Path, beats, out: Path, music: Path | None = None):
    """
    ffmpeg: concat clips -> scale/crop to 1080x1920 -> burn timed captions
    -> mix voiceover (loud) with optional background music (quiet).
    """
    listfile = out.parent / "clips.txt"
    listfile.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")

    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30"
    caps = caption_filters(beats)
    if caps:
        vf += "," + caps

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
           "-i", str(voiceover)]

    if music and music.exists():
        # duck the music under the voice, then mix
        cmd += ["-stream_loop", "-1", "-i", str(music),
                "-filter_complex",
                f"[0:v]{vf}[v];"
                "[2:a]volume=0.18[bg];"
                "[1:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-vf", vf, "-map", "0:v:0", "-map", "1:a:0"]

    cmd += ["-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)]
    subprocess.run(cmd, check=True)
    print(f"✅ final video (captions{' + music' if music and music.exists() else ''}) → {out}")


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

    # Optional: drop any royalty-free track at assets/music.mp3 and it'll be mixed in quietly.
    music = ROOT / "assets" / "music.mp3"
    assemble(clips, d / "voice.mp3", script["beats"], d / "final.mp4",
             music if music.exists() else None)


if __name__ == "__main__":
    from datetime import date
    main(sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat())
