# Agent Visual Engine

First visual proof asset: a single premium SaaS hero component, rendered at `/preview`.

## Purpose

This project exists to answer one question before any platform is built:

> Can AI-generated front-end output look genuinely premium?

It contains exactly one real UI component — `PremiumSaaSHero` (animated) and
`PremiumSaaSHeroStatic` (no Framer Motion) — and a `/preview` route for visual
review. No landing page, no dashboard, no MCP, no database.

## Stack

- Next.js (App Router) + TypeScript
- Tailwind CSS v3
- Framer Motion (animated hero only)
- Geist via `next/font` (the `geist` package)
- Biome for lint/format

## Install

```bash
pnpm install
```

## Run locally

```bash
pnpm dev
```

Then open:

```txt
http://localhost:3000/preview
```

`/preview` renders the hero full-bleed on a near-black background for
screenshots, screen recording, and mobile/desktop QA (test at 375px).

## Verify

```bash
pnpm build
pnpm biome check .
```

## Integrity note

Integrity note: this first component contains no network calls, no secrets, no
shell execution, and no hidden tracking.
