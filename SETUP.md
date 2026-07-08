# 📱 Setup Guide (phone-friendly, no coding needed)

You'll set up 4 free/cheap accounts, paste their keys into GitHub once, and then the
agent runs itself. Total time: ~30–40 minutes. Total cost: **under $20/month**.

Do these in order. You can do all of it from your iPhone.

---

## Step 1 — The scheduler (this is what posts to every platform)
This is the one piece that connects TikTok + Instagram + YouTube + Facebook.

**Pick ONE:**
- **Postiz** (open-source, cheapest) → sign up at postiz.com, or self-host for free.
- **Blotato** (~$9/mo, easiest) → blotato.com. Built for exactly this.

Inside the dashboard: **connect your TikTok, Instagram, YouTube, and Facebook accounts**
(tap "add channel" for each and log in). Then find **Settings → API / Public API** and copy your **API key**.

> ⚠️ Instagram & TikTok require a **Business/Creator** account to auto-post. In each app:
> Settings → switch to Professional/Business account (free). Do this first.

---

## Step 2 — Voiceover (ElevenLabs)
- Sign up at elevenlabs.io (free tier works to start).
- Pick a **calm, warm voice** you like → copy its **Voice ID**.
- Profile → **API key** → copy it.

---

## Step 3 — B-roll (Pexels — free forever)
- Sign up at pexels.com → **Image & Video API** → copy your **API key**.

---

## Step 4 — The writer (Anthropic)
- Get an API key at console.anthropic.com → **API keys**.
- Add ~$5 credit. (Scripts cost pennies each.)

---

## Step 5 — Paste the keys into GitHub (one time)
On the GitHub app or website, open this repo →
**Settings → Secrets and variables → Actions → New repository secret.**
Add these four (names must match exactly):

| Secret name | Paste the key from |
|---|---|
| `ANTHROPIC_API_KEY` | Step 4 |
| `ELEVENLABS_API_KEY` | Step 2 |
| `PEXELS_API_KEY` | Step 3 |
| `POSTIZ_API_KEY` | Step 1 |

Also edit **`agent/config.example.json`** → copy it to **`agent/config.json`**, and fill in
your `voice_id` (Step 2) and scheduler `base_url` (Step 1). *(config.json is gitignored — safe.)*

---

## Step 6 — Test it (no posting yet)
In the GitHub app: **Actions → Story Engine → Run workflow → set "dry_run" = true → Run.**
It writes a script + captions and saves them (download the artifact to read them). No video, no posting.
Love the writing? Move on.

## Step 7 — Go live
Run the workflow again with **dry_run = false**. It builds the video and posts everywhere.
After that, the schedule in `.github/workflows/story-engine.yml` runs it automatically ~4×/week.
You do nothing. 🎉

---

## Changing things later (just ask the agent)
- New page name / voice → edit `brand/brand.md`.
- Post more/less often → edit the `cron` lines in the workflow.
- Different vibe → edit `strategy/story-templates.md`.
- Just tell Claude: *"change the posting schedule to daily at 6pm"* and it'll do it.
