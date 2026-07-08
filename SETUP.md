# 📱 Setup Guide — the FREE path (semi-auto, ~$0/month)

The agent writes the story, records the voiceover, pulls cinematic footage, and builds a
finished vertical video **with captions burned in**. Then it hands you a **post-pack** — the
video plus copy-paste captions for each platform. You post it in ~2 minutes from your phone.

No scheduler fees. No platform app-review pain. Total cost: **basically $0** (free tiers).

You'll set up **3 free accounts**, paste **3 keys** into GitHub once, and you're done.
All of this works from your iPhone.

---

## Step 1 — The writer (Anthropic)
- Get an API key at **console.anthropic.com → API keys**.
- Add ~$5 credit. Each script costs about **a penny**, so $5 lasts months.
- Copy the key.

## Step 2 — The voiceover (ElevenLabs — free tier)
- Sign up at **elevenlabs.io**.
- Pick a **calm, warm voice** → copy its **Voice ID**.
- Profile → **API key** → copy it.

## Step 3 — The footage (Pexels — free forever)
- Sign up at **pexels.com** → **Image & Video API** → copy your **API key**.

---

## Step 4 — Paste the keys into GitHub (one time)
On the GitHub app or website: open this repo →
**Settings → Secrets and variables → Actions → New repository secret.**
Add these three (names must match exactly):

| Secret name | From |
|---|---|
| `ANTHROPIC_API_KEY` | Step 1 |
| `ELEVENLABS_API_KEY` | Step 2 |
| `PEXELS_API_KEY` | Step 3 |

Then copy **`agent/config.example.json`** to **`agent/config.json`** and fill in your
`voice_id` (Step 2). Leave the scheduler as `"provider": "manual"`. *(config.json is gitignored — safe.)*

---

## Step 5 — Make your first video
In the GitHub app: **Actions → Story Engine → Run workflow.**
When it finishes (~2–3 min), tap the run → **download the "content" artifact**. Inside you'll find:
- `final.mp4` — your finished video
- `POST_PACK.txt` — the caption for each platform, ready to paste

## Step 6 — Post it (the 2-minute routine)
Save `final.mp4` to your phone, then for each app:
**TikTok → Instagram Reels → YouTube Shorts → Facebook** — upload the video, paste that
platform's caption from `POST_PACK.txt`, post. Done.

> 💡 Want to post to all four in fewer taps? Connect them once in a **free** app like
> **Buffer** or **Metricool** (free tiers) and upload there instead of app-by-app.

## Step 7 — Let it run on autopilot (the *creating* part)
The schedule in `.github/workflows/story-engine.yml` already makes a fresh video ~4×/week
automatically. You just grab each one and post it. Zero writing, zero editing on your side.

---

## Upgrading to fully-automatic later
When the page is growing and you're ready to remove the manual step, switch the scheduler
`provider` to `postiz` (self-host ~$5/mo) or `blotato` ($29/mo) — the posting code is already
there. Just tell Claude *"set me up for full auto-posting"* and it'll walk you through it.

## Changing things (just ask Claude on your phone)
- New page name / voice → `brand/brand.md`
- Post more/less often → the `cron` lines in the workflow
- Different story vibe → `strategy/story-templates.md`
- Or literally say: *"make the videos funnier"* / *"post daily at 6pm"* and it's done.
