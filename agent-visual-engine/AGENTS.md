# AGENTS.md

## Scope

This repository builds exactly one proof asset and then stops:

- `src/components/heroes/PremiumSaaSHero.tsx` — animated + static hero
- `src/app/preview/page.tsx` — full-bleed preview route

## Hard rules

Do **not** add, before human visual review approves the first hero:

- a landing page, dashboard, or component gallery
- a second component or shared UI abstraction library
- MCP (local or remote), API routes, database, auth, billing
- external images, remote assets, icon packages, or emoji
- network calls, `fetch`, analytics, iframes, localStorage, or secrets

## Component contract

- Every prop in `PremiumSaaSHeroProps` must visibly affect the output.
- `PremiumSaaSHeroStatic` must contain zero references to Framer Motion.
- The product mockup zone is built only from `div`s and Tailwind.
- Must be perfect at 375px with no horizontal overflow.

## Stop condition

Once `/preview` renders and `pnpm build` + `pnpm biome check .` pass, stop.
Human visual review comes next.
