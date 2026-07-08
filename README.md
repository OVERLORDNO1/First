# 🎬 Story Engine — Autonomous Motivational Content Agent

An AI agent that writes **story-driven, cinematic motivational videos** and posts them
automatically to **TikTok, Instagram Reels, YouTube Shorts, and Facebook** — for under **$20/month**.

Built to run from your **iPhone** (Claude app) and on autopilot (free GitHub Actions cron).

---

## What it does, end to end

```
1. WRITES a story   →  hook → build-up → turning point → payoff → call-to-action
2. NARRATES it      →  emotional AI voiceover
3. BUILDS the video →  cinematic stock B-roll + captions + music (faceless, high quality)
4. WRITES captions  →  tuned per platform (TikTok / IG / YT / FB) + hashtags
5. POSTS everywhere →  one push fans out to all platforms via a scheduler
```

You approve nothing day-to-day once it's live — but you *can* review anything from your phone.

---

## The cheap architecture (why it stays under $20)

| Layer | Tool | Cost |
|---|---|---|
| Brain (scripts, story arcs, captions) | This repo + an LLM | pennies |
| Automation engine (the scheduler/cron) | **GitHub Actions** | **free** |
| Voiceover | ElevenLabs free tier / OpenAI TTS | ~$0–5/mo |
| Cinematic B-roll | **Pexels** stock (free API) | **free** |
| Video assembly | **ffmpeg** (runs in the free Action) | **free** |
| Post to all platforms | **Postiz** (open-source) or **Blotato** | free–~$9/mo |

**Total: ~$5–19/month.**

---

## 📱 Start here

New to this? Open **[SETUP.md](SETUP.md)** — it's written for a phone, step by step, no coding assumed.

## Folder map

| Folder | What's inside |
|---|---|
| `brand/` | Who the page is — name, voice, look, values |
| `strategy/` | Content pillars, story frameworks, posting schedule |
| `prompts/` | The exact instructions the AI uses to write each piece |
| `agent/` | The runnable pipeline (script → voice → video → post) |
| `.github/workflows/` | The free autopilot (GitHub Actions cron) |
| `content/` | Where generated scripts & videos land |
