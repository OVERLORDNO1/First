# Job Application Agent

A Claude Code project that searches for jobs, tailors your CV/cover letter per
posting, fills out applications, and tracks everything in one log.

## Important: where this has to run

This project must run with **Claude Code CLI on your own computer**, logged
into your own browser session, with the Playwright MCP server installed.
Cloud/remote Claude Code sessions (like claude.ai/code containers) have no
browser and no access to your LinkedIn login, so the automation steps below
will not work there — only the research/tailoring steps will.

Setup on your machine:

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
