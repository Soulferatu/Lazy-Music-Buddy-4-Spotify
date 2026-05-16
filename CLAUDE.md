# Play[my W:O:A]list — Project Brief for Claude

This file is the single entry point for any Claude session on this repo. It states what the project is, where it stands, and how Claude should operate. For the full roadmap and per-phase detail, see [PHASES.md](PHASES.md).

## End Goal

Build a browser-first Progressive Web App (installable on phone or desktop) that lets a user:

1. Pick Wacken Open Air bands (starting with the 2026 lineup, later extending to historical years and cross-year mixes).
2. Name a playlist.
3. Receive a real Spotify playlist generated from those bands — either created in a dedicated app-owned Spotify account (and shared via link) or, optionally, in the visitor's own Spotify account.
4. Choose between Spotify top tracks or the latest setlist.fm setlist as the song source.
5. Generate shuffle/blended playlists across multiple Wacken years.

The app must be installable as a PWA, work on mobile and desktop, and never commit secrets.

## Current Stage

**Stage 5 — Deployment + Public Release** (next up).

- Stages 0–4 are complete (2026-05-16). Stage 4 delivered: loading states on Preview/Create, mobile auto-scroll to summary, dynamic countdown to July 29 2026, stale copy fixes, Apple PWA meta tags, manifest `scope`, service worker fix, floating action buttons (FAB) with proper fixed positioning, result page buttons in side-by-side layout, extended Spotify artist search pagination (5 pages), version `0.4.0`. Details: [wiki/stage4_pwa_polish.md](wiki/stage4_pwa_polish.md).
- Architecture migration (Phases 1–6) is complete — the service layer, config, models, i18n, security hardening, and test split are all in place.
- Next milestone: deploy to a public hosting provider so others can access and use the app. The app-owned Spotify account creates playlists for users; no visitor authentication required.
- Optional: Personal Spotify login deferred to later (low priority; app-owned account works for sharing).

## Confirmed Product Decisions

| Decision | Choice |
|---|---|
| App name | Play[my W:O:A]list |
| Visual style | A1v3 "Embers" — dark festival dashboard. Near-black base (#141316 / #0a090b / #1a1418) with ember orange (#ff4500) and ember-glow (#ff8a3d) as primary accents, blood red (#8b0000) for depth and "blood splatter" radial gradients in the page background, paper-cream (#f5f1e8) for body text. Gold (#e0b84f / #f5d27a) is used sparingly — only the CTA button, the round W mark, and a few headline highlights. |
| Heading font | Cinzel Decorative Bold |
| Body font | Inter (Inter Tight in hero/UI) |
| Accent font | Special Elite (eyebrows, badges, ticket metadata) |
| Language | Bilingual EN / pt-BR, switchable in UI |
| Layout | Checklist-first, single-page flow |
| First Spotify mode | App-owned mode |
| Local dev | Sufficient through Stage 4 |
| Backend | Flask |
| Frontend | Server-rendered HTML + vanilla JS + responsive CSS |
| App icon | Existing placeholder at `wacken_playlist/static/icons/icon.svg` and `icon.png` — used by the PWA manifest. Replace by overwriting those two files when a final icon is approved; no code change needed. |

Open decisions: final logo/install icon (placeholder in use), whether to add personal Spotify login (Optional Stage).

**Hosting provider (Stage 5):** Vercel confirmed — see [DEPLOYMENT.md](DEPLOYMENT.md) for setup instructions.

## Tech Stack

- **Backend:** Flask (app factory pattern, typed `Config` classes).
- **Frontend:** Jinja2 templates, vanilla JS, responsive CSS, PWA manifest + service worker.
- **APIs:** Spotify Web API (Stage 2+), setlist.fm API (Stage 6+).
- **Data:** JSON files in `wacken_playlist/data/lineups/`; SQLite considered later if auth/session storage needs it.
- **Tests:** `pytest` split into `tests/unit/` and `tests/integration/` with shared `conftest.py`.
- **i18n:** `wacken_playlist/i18n/{en,pt-BR}.json`, injected into templates and exposed to JS via `window.__translations`.
- **Production entry:** `wsgi.py` for Gunicorn.

## Repository Map

```
wacken_playlist/        Flask app package
  __init__.py           create_app factory + service wiring
  config.py             Development / Testing / Production configs
  models.py             Band, PlaylistRequest, PlaylistPreview, MatchedBand, PlaylistResult
  routes.py             Thin HTTP handlers — no business logic
  lineup.py             LineupRepository (reads data/lineups/*.json)
  services/             SpotifyClient, PlaylistBuilder, SetlistFmClient (stub)
  i18n/                 en.json, pt-BR.json
  data/lineups/         wacken_2026.json (more years later)
  templates/            base.html, index.html
  static/               CSS, JS, service worker, icons
  version.py            Single source of cache-busting version
tests/
  conftest.py
  unit/                 No Flask, no I/O — pure service tests
  integration/          Uses test_client + mocked services
wiki/                   Processed knowledge pages (see Wiki Workflow below)
raw/                    Original source material (prompts, decisions)
scripts/                restart-dev.ps1 (Windows), dev.sh (macOS/Linux)
wsgi.py                 Production entry point
```

## Operating Rules for Claude

These are durable instructions. Follow them every session.

1. **Never commit without explicit approval.** The user reviews every change before it is committed. Stage and propose; do not run `git commit` unsolicited.
2. **Update CLAUDE.md and PHASES.md after every meaningful step.** When a phase completes, when the current stage shifts, when a decision is made, or when a new prerequisite appears — reflect it here and in [PHASES.md](PHASES.md) before moving on.
3. **Never commit secrets.** Spotify and setlist.fm credentials live only in `.env` (and production secret stores). The repo carries `.env.example` only.
4. **Respect the wiki architecture** — see Wiki Workflow below. New durable knowledge becomes a `wiki/` page; raw sources go in `raw/`; cross-links go through [index.md](index.md); every ingest is logged in [log.md](log.md).
5. **Ask when uncertain.** The user has minimal dev experience and explicitly wants to be consulted on unclear decisions. Prefer a short clarifying question over guessing.
6. **One source of truth per concern.** Translations in `i18n/*.json` only. Band data in `data/lineups/*.json` only. Cache version in `version.py` only. Do not duplicate.
7. **Tests follow the split.** Pure logic → `tests/unit/`. HTTP-touching → `tests/integration/`. Integration tests mock `SpotifyClient` via the `mock_spotify` fixture.
8. **No premature abstractions.** No DI containers, no ORM, no Blueprint split until a stage actually needs them. See Explicit Non-Goals in [PHASES.md](PHASES.md).

## Wiki Workflow

The project uses an LLM-friendly wiki structure so knowledge stays searchable and auditable across sessions.

- `raw/` — original sources (prompts, decisions, exports). Do not rewrite in place.
- `wiki/` — processed knowledge pages. One topic per page, lowercase filenames with underscores.
- [index.md](index.md) — master index linking every wiki page to its purpose and related pages.
- [log.md](log.md) — chronological record of every ingest or wiki update.
- [wiki_start.md](wiki_start.md) — the full workflow specification.

When adding knowledge:

1. Put original material in `raw/` if there is a durable source.
2. Create or update one focused page in `wiki/`.
3. Link it from `index.md` (including the `Related Pages` column).
4. Log the change in `log.md`.

Search the wiki with ripgrep from the project root, e.g. `rg "OAuth" raw wiki index.md log.md`.

## Historical / Archived Docs

The following remain for reference but are no longer the primary sources of truth — CLAUDE.md and PHASES.md are:

- [Start.MD](Start.MD) — original product brief and stage-by-stage spec.
- [ARCH_MIGRATION_PLAN.md](ARCH_MIGRATION_PLAN.md) — full architecture migration plan with rationale.
- [wiki/project_overview.md](wiki/project_overview.md), [wiki/development_stages.md](wiki/development_stages.md) — earlier roadmap summaries.
- [wiki/spotify_integration.md](wiki/spotify_integration.md), [wiki/pwa_requirements.md](wiki/pwa_requirements.md), [wiki/stage1_implementation.md](wiki/stage1_implementation.md), [wiki/stage2_spotify_preview.md](wiki/stage2_spotify_preview.md), [wiki/phase1_config_models.md](wiki/phase1_config_models.md) … [wiki/phase6_test_architecture.md](wiki/phase6_test_architecture.md) — deep dives still authoritative for their topics.
