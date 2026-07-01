# Job Application Agent

A Claude Code project that searches for jobs, tailors your CV/cover letter per
posting, fills out applications, and tracks everything in one log.

## Important: where this has to run

This project needs a persistent machine with a real, logged-in browser —
Claude Code sessions triggered from GitHub issues/PRs (like the one that
built this scaffold) run in throwaway cloud containers with no browser, so
they can maintain these files but can't drive LinkedIn. You need either your
own computer, or a persistent virtual machine/dev environment. If you don't
have your own machine free right now, the fastest free option is a **GitHub
Codespace on this repo** — see below.

### Option A: GitHub Codespaces (free, no setup on your own machine)

This repo includes a `.devcontainer/devcontainer.json` at the repo root that
does the setup for you.

1. On github.com, go to this repo, switch to the
   `claude/automated-job-applications-x2yjwa` branch, click **Code → Codespaces
   → Create codespace on branch**.
2. Wait for it to build — it installs Claude Code CLI, Playwright + Chromium,
   registers the Playwright MCP server, and a lightweight virtual desktop
   (noVNC) automatically.
3. Once it's ready, open the **Ports** tab, find port `6080` ("Virtual
   desktop"), click the globe icon to open it in a browser tab, and enter the
   password from `devcontainer.json` (`changeme123` by default — change it
   before you use this for real).
4. Inside that virtual desktop, open a browser and log into linkedin.com
   once, manually, with your real credentials. Playwright MCP's browser
   profile persists on the Codespace's disk after that, so you won't need to
   log in again unless the Codespace is deleted/rebuilt.
5. In the Codespace's terminal (VS Code's integrated terminal, not the
   desktop), run `claude`, `cd job-agent`, and ask it to run the job-apply
   skill.
6. Free tier: personal GitHub accounts get 60 hours/month of 2-core Codespace
   usage (120 core-hours) at no cost, and it auto-stops after ~30 minutes
   idle so you don't burn hours by accident. Fine to start with; if you use
   this daily you may want to move to a paid tier or your own machine later.

Codespaces persist between stop/start, but **deleting or rebuilding the
Codespace wipes the browser profile** — you'd need to log into LinkedIn
again.

### Option B: your own computer

```bash
claude mcp add playwright npx @playwright/mcp@latest
```

Then log into linkedin.com once in the browser Playwright drives, so the
session/cookies persist. Never give this project your LinkedIn password
directly — it should reuse an already-authenticated browser session.

## Why LinkedIn is handled differently than company career pages

LinkedIn's user agreement prohibits third-party automation of activity on
its site, and accounts can be restricted for it. Greenhouse, Lever, Ashby,
Workday and plain company career pages have no equivalent restriction against
you (a job seeker) using a tool to fill out your own application.

So the automation policy in `.claude/skills/job-apply/SKILL.md` is:

- **LinkedIn Easy Apply**: search, match, tailor CV/cover letter, open the
  form, fill every field, attach the CV — then **stop before clicking the
  final Submit button** and hand control back to you.
- **Company ATS pages** (Greenhouse/Lever/Ashby/Workday/direct sites): search,
  match, tailor, fill, and submit automatically, then log it.

This gives you real automation everywhere, with the one click that carries
account risk left in your hands.

## Folder layout

```
job-agent/
  cv/
    master-cv.pdf          <- your source CV (upload/replace this)
    cv.md                  <- plain-text/markdown extraction, easier for Claude to parse
  profile.json              structured facts: contact info, skills, work history, education
  cover-letter-style.md      tone/voice guide so generated letters sound like you
  target-roles.yml           what to search for: titles, locations, seniority, must-haves
  blacklist-companies.yml     companies/recruiters to skip
  application-log.csv         every job touched: status, dates, links, notes
  .claude/skills/job-apply/SKILL.md   the procedure Claude Code follows
```

## Getting started

1. Replace `cv/master-cv.pdf` with your real CV and fill in `cv/cv.md` and
   `profile.json` from it (or ask Claude to do this from the PDF).
2. Edit `target-roles.yml` and `blacklist-companies.yml` for your search.
3. Edit `cover-letter-style.md` if you want a different tone.
4. In Claude Code, on your machine, with Playwright MCP installed, run:

   > Use the job-apply skill to find and apply to matching roles.

5. Review `application-log.csv` regularly, and check for LinkedIn
   applications sitting in `filled_pending_submit` status that need your
   final click.

## Recommended pace

10-20 well-matched, properly tailored applications per day beats mass-applying
to hundreds. The skill defaults to a daily cap you can change in
`target-roles.yml`.
