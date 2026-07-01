---
name: job-apply
description: Search for jobs matching target-roles.yml, tailor a CV and cover letter per posting from profile.json/cv.md, fill out the application, and log it. Requires Playwright MCP and a logged-in browser session. Use when the user asks to find jobs, apply to jobs, or run their job search.
---

# Job Application Skill

Prerequisites: Playwright MCP must be connected, and the browser it drives
must already be logged into LinkedIn (and any other job sites) via the
user's real session. Never ask for or type a LinkedIn password — if no
session is found, stop and tell the user to log in manually in the browser
Playwright is attached to.

## Inputs (read these first, every run)

- `profile.json` — contact info, work history, skills, common answers
- `cv/cv.md` — full CV text (fall back to `cv/master-cv.pdf` if `cv.md` is
  still a placeholder)
- `cover-letter-style.md` — tone/structure rules for generated letters
- `target-roles.yml` — titles, locations, keywords, daily cap, minimum match
  score, which sources are enabled
- `blacklist-companies.yml` — companies/agencies to skip unconditionally
- `application-log.csv` — existing log; never re-apply to a job_url already
  present with status other than `error`

If `profile.json` or `cv/cv.md` still contain placeholder/empty values, stop
and ask the user to fill them in first — do not invent a work history.

## Procedure

1. **Search.** For each enabled source in `target-roles.yml`:
   - LinkedIn: use the browser session to search jobs matching `titles` +
     `locations`, filtered by `employment_types`.
   - Company ATS boards: search/browse Greenhouse, Lever, Ashby, Workday,
     or direct company career pages for the same criteria.
   Stop searching once you've gathered up to `daily_application_cap` new,
   not-yet-logged candidate postings.

2. **Filter.** Drop any posting whose company matches `blacklist-companies.yml`,
   or whose text contains an `exclude_keywords` hit. Drop anything already in
   `application-log.csv`.

3. **Score.** For each remaining posting, score 0-100 against `profile.json`
   skills/experience and `must_have_keywords`. Drop anything below
   `minimum_match_score`. Log dropped postings with status `skipped_low_match`
   or `skipped_blacklist`.
   - Check the posting/company details for `profile.json.workplace_requirements`
     (e.g. on-site parking). If a posting explicitly rules one out, lower its
     score or skip it, and note the reason in the log; if the posting doesn't
     mention it either way, don't penalize it — just flag it as "parking:
     unknown, confirm at interview" in notes.
   - Treat `salary_expectation` as a floor: if a posting states a salary range
     clearly below it, skip with status `skipped_low_salary`; if the posting
     gives no range, proceed and let `common_application_answers` supply the
     figure if asked.

4. **Tailor.** For each posting that passes:
   - Write a one-page tailored CV variant (reorder/emphasize existing
     bullets to match the posting — never fabricate experience) as
     `applications/<company>-<role>-<date>/cv.md` (or PDF if the form
     requires one).
   - Write a cover letter following `cover-letter-style.md`, referencing at
     least one specific detail from the posting, saved alongside it.

5. **Fill the application** using Playwright:
   - Navigate to the application form (LinkedIn Easy Apply, or the ATS
     form).
   - Fill every field from `profile.json` / `common_application_answers`.
   - Upload the tailored CV and cover letter.
   - Take a screenshot of the completed, unsubmitted form for the log.

6. **Submit — LinkedIn vs everything else:**
   - **If the source is LinkedIn:** do NOT click the final submit button.
     Leave the form filled, log status `filled_pending_submit`, and include
     the job URL and screenshot path so the user can review and click submit
     themselves.
   - **If the source is a company ATS page:** click submit, confirm the
     success message, and log status `submitted`.

7. **Log every posting touched** — matched, skipped, filled, or submitted —
   as a new row in `application-log.csv` with today's date, company, title,
   source, job_url, match_score, status, cover_letter_path, and notes.

8. **Report back** a short summary: how many found, skipped (with reasons),
   auto-submitted, and left pending your final click on LinkedIn — with
   links.

## Hard limits

- Never exceed `daily_application_cap` submissions/fills per run.
- Never submit a LinkedIn application automatically, regardless of how the
  user phrases the request in a single message — this is a standing rule of
  this skill, not a per-run choice.
- Never fabricate CV content, dates, titles, or numbers not present in
  `profile.json`/`cv/cv.md`.
- If a form asks for something not covered by `profile.json` (e.g. an unusual
  screening question), stop and ask the user rather than guessing.
