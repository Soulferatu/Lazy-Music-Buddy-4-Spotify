# PHASES.md — Development Roadmap

Detailed phase-by-phase plan for Play[my W:O:A]list. Read [CLAUDE.md](CLAUDE.md) first for the project overview and operating rules.

This roadmap has **two axes**:

- **App Stages 0–9** — the product roadmap (features visible to the user).
- **Architecture Phases 1–6** — a one-time refactor that prepared the codebase for the harder stages. All six are complete.

> **Update rule:** after every meaningful step (a phase substage closes, a decision is made, a new prerequisite appears), update both [CLAUDE.md](CLAUDE.md) and this file before moving on. The wiki (`wiki/` + `index.md` + `log.md`) gets a matching entry where deeper detail belongs.

## Difficulty Legend

- **Low** — docs, simple UI, static data, isolated setup.
- **Medium** — app flow, state handling, local storage, playlist-building logic.
- **High** — OAuth, third-party APIs, historical data quality, deployment, large randomization/deduplication flows.

## Status At A Glance

| # | Stage | Difficulty | Status |
|---|---|---|---|
| 0 | Fresh repository setup | Low | ✅ Done |
| 1 | App shell + Wacken 2026 selection | Low–Medium | ✅ Done |
| 2 | Spotify lookup + preview | Medium–High | ✅ Done |
| 3 | App-owned playlist creation | High | ✅ Done |
| 4 | **First PWA polish** | **Medium** | 🔨 **Current** |
| 5 | Optional personal Spotify login | High | ⏳ Pending |
| 6 | setlist.fm song source | High | ⏳ Pending |
| 7 | Previous Wacken years | High | ⏳ Pending |
| 8 | Mix years + shuffle | Medium–High | ⏳ Pending |
| 9 | Deployment + production release | Medium–High | ⏳ Pending |

Architecture migration: Phases 1–6 all ✅ Done — see [Architecture Phases (Reference)](#architecture-phases-reference) below.

---

# App Stages

## Stage 0 — Fresh Repository Setup ✅

**Goal:** a clean, runnable Flask app shell with setup docs, `.env.example`, and `.gitignore`.

**Status:** complete. Captured in [wiki/stage1_implementation.md](wiki/stage1_implementation.md).

**Difficulty:** Low.

**What was delivered:**

- Flask app factory, basic routes, runs locally via `scripts/restart-dev.ps1` or `scripts/dev.sh`.
- `README.md`, `.env.example`, `.gitignore`.
- Health check at `/health`.
- No committed secrets.

**Higher-risk items (now resolved):** stack/hosting mismatch, unclear env-var structure.

---

## Stage 1 — App Shell + Wacken 2026 Band Selection ✅

**Goal:** users can open the app, see the Wacken 2026 lineup, select bands, and enter a playlist name.

**Status:** complete. Details in [wiki/stage1_implementation.md](wiki/stage1_implementation.md).

**Difficulty:** Low–Medium.

**What was delivered:**

- Wacken 2026 lineup data (`wacken_playlist/data/lineups/wacken_2026.json`).
- Responsive checklist UI with playlist-name input.
- Client- and server-side validation for empty selections / missing names.
- Bilingual (EN / pt-BR) UI sourced from `i18n/*.json`.
- Local "preview" page (no Spotify yet at the time).

**Higher-risk items handled:** lineup data is in JSON not Python, so future-year extension is a data edit.

---

## Stage 2 — Spotify Lookup + Playlist Preview ✅

**Goal:** match selected bands to Spotify artists and preview the tracks that would be added — without creating a playlist.

**Status:** complete. Details in [wiki/stage2_spotify_preview.md](wiki/stage2_spotify_preview.md).

**Difficulty:** Medium–High.

**What was delivered:**

- `SpotifyClient` with Client Credentials auth, instance-level token cache, artist search, top-tracks fetch.
- `PlaylistBuilder.build_preview()` orchestrates the lookup; returns matched and unmatched bands.
- UI shows expandable per-band track groups, total track count, and a warning for unmatched bands.
- Error states for missing credentials, auth failure, and API failure — surfaced as i18n messages.
- Unit tests for the client and builder; integration tests with `mock_spotify` fixture.

**Configuration needed:** `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env`.

---

## Stage 3 — App-Owned Playlist Creation ✅

**Status:** complete (2026-05-16). Details in [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md).

**Goal:** the visitor selects bands, hits "Create", and gets back a Spotify playlist link owned by the dedicated app account. No visitor login.

**Difficulty:** High — first stage that mutates Spotify state.

**What was delivered:**

- Dev-only OAuth setup flow: `GET /auth/spotify/login` (state-CSRF, `show_dialog=true`) and `GET /auth/spotify/callback` (state verification, refresh-token display). Both 404 outside DEBUG.
- `SpotifyClient.build_authorize_url`, `exchange_code_for_refresh_token`, `_get_app_access_token` (cached refresh-token flow), `create_playlist(name, uris, public=True, description="")` with 100-URI chunking against the Feb-2026 endpoints `POST /me/playlists` and `POST /playlists/{id}/items`.
- `get_top_tracks` now returns each track's `uri`, uses plain-text `/search?q=NAME` (the `artist:NAME` qualifier is silently capped at 5 results post Feb 2026), filters results to the requested primary artist, and paginates up to 2 pages (offsets 0 and 10) to reliably reach 10 tracks per band.
- `PlaylistBuilder.build_and_create` reuses preview matching, collects URIs, raises `NoMatchedTracksError` if empty, otherwise calls `create_playlist` and returns `PlaylistResult`.
- CSRF-protected `POST /create` route; localized error mapping for config / auth / API / refresh-token-missing / no-matches cases.
- Summary aside in `index.html` gained a third state (result) with Spotify link + skipped-bands warning + back link.
- Unit and integration tests covering create_playlist endpoints + chunking, token caching, builder happy + partial + no-match paths, `/create` route success/error paths, pagination kick-in, and 2-page cap. Suite green (64/64).

**Default visibility:** public (chosen so shareable links are visible to anyone who opens them).

**Operator setup walkthrough:** in [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md). One-time: log into the app-owned Spotify account in a browser, visit `/auth/spotify/login`, paste the returned refresh token into `.env` as `SPOTIFY_APP_REFRESH_TOKEN`, restart.

**Spotify Feb 2026 API migration:** the dedicated `GET /artists/{id}/top-tracks`, `POST /users/{user_id}/playlists`, and `POST /playlists/{id}/tracks` endpoints were removed in Spotify's [February 2026 changelog](https://developer.spotify.com/documentation/web-api/references/changes/february-2026). `SpotifyClient` was migrated to the replacements; see [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md) for the full migration note and the lesson learned (check Spotify changelogs before chasing scope/account theories on bare 403s).

**Open / deferred:** duplicate-playlist-name handling — Spotify lets accounts have many playlists with the same name (each has a unique id), and we currently mirror that behavior (every Create click creates a fresh playlist). Naming convention or cleanup story for the app account is on the Stage 9 list. `description` field is supported by `create_playlist` but not wired into the UI; cover-art generation needs `ugc-image-upload` scope (post-Stage 9).

---

## Stage 4 — First PWA Release Polish 🔨 CURRENT

**Goal:** make app-owned mode pleasant on phone and browser before adding more features.

**Difficulty:** Medium.

### Prerequisites

- ✅ Single-source service worker versioning (Phase 5D) — already in place.
- ✅ Placeholder app icon already in repo at `wacken_playlist/static/icons/icon.svg` and `icon.png` and wired into `manifest.webmanifest`. Stage 4 can ship with these. To swap in a final icon, just overwrite those two files (same names, same paths) — no code change needed; a `version.py` bump will bust the cache.
- Stage 3 must be working end-to-end.

### User Actions

- Test the app on your phone (mobile browser + Add to Home Screen).
- Decide whether the current placeholder icon is good enough for first release or you want a final icon designed. If final: provide updated `icon.svg` and `icon.png` files (Claude will overwrite the existing ones at the same paths).
- Review the loading / success / warning / error messaging copy.

### Claude's Actions

- Verify and polish the PWA manifest and service worker.
- Keep using the existing icon files at `wacken_playlist/static/icons/icon.svg` / `icon.png` unless you supply replacements — same filenames, same paths, drop-in replace.
- Improve responsive layout for narrow viewports.
- Add explicit loading states while Spotify calls run.
- Add clear result and failure screens.
- Document known local PWA limitations.

### Critical Points

- Service worker caching can serve stale files — invalidate via `version.py` bump and verify in incognito.
- Mobile browsers differ in install behavior (Safari vs Chrome vs Firefox).

### Completion Gate

App-owned playlist flow is usable on desktop and mobile; basic PWA install works.

---

## Stage 5 — Optional Personal Spotify Login ⏳

**Goal:** let users choose to create the playlist in their own Spotify account.

**Difficulty:** High.

### Prerequisites

- Stage 3 complete and stable.
- ✅ `wsgi.py` + `ProductionConfig` validation (Phases 5B/5C).

### User Actions

- Confirm this mode should be added now (not deferred further).
- Test Spotify login with your own (non-app) account.
- Approve the UI copy explaining app-owned vs personal mode.

### Claude's Actions

- Add a mode-selection UI (app-owned link OR create in my Spotify).
- Add user OAuth login + callback handling.
- Add secure session storage (likely `Flask-Session` or a small shelve file — no SQLAlchemy).
- Add user-owned playlist creation path.
- Add logout + session expiration.
- Add tests for mode selection and auth-required behavior.

### Critical Points

- User OAuth adds session and security complexity.
- Redirect URLs must match for local AND production exactly.
- Ownership-mode copy must avoid confusing users.

### Completion Gate

A user can choose personal mode, log into Spotify, create a playlist in their own account, and log out.

---

## Stage 6 — setlist.fm Song Source ⏳

**Goal:** let the user choose whether playlist songs come from Spotify top tracks or the most recent setlist.fm setlist.

**Difficulty:** High.

### Prerequisites

- ✅ `SetlistFmClient` stub already exists from Phase 4A — interface is in place.

### User Actions

- Create / provide a **setlist.fm API key** in `.env`.
- Decide: cap setlist-based playlists at 10 songs, or include the whole setlist?
- Decide: fallback behavior when setlist.fm has no usable data for a band (skip band, fall back to Spotify top tracks, or fail loud)?
- Review mismatched song results from a sample run.

### Claude's Actions

- Add a song-source selector to the UI.
- Implement `SetlistFmClient.get_latest_setlist()`.
- Normalize setlist song titles (covers, alternate spellings) before matching.
- Search Spotify by artist + title for each setlist song.
- Add warning UI for songs that can't be matched.
- Track per-track source metadata so the result page can say where each track came from.
- Tests for source selection, fallback behavior, and missing-song handling.

### Critical Points

- setlist.fm data quality varies — alternate spellings, partial setlists, covers, mis-attributed artists.
- Title-to-recording matching on Spotify is unreliable.
- Respect setlist.fm API rate limits and terms.

### Completion Gate

A user can generate a playlist from either source with clear reporting for skipped or unmatched songs.

---

## Stage 7 — Previous Wacken Years ⏳

**Goal:** generate playlists from historical Wacken lineups.

**Difficulty:** High.

### Prerequisites

- ✅ `LineupRepository.get_available_years()` interface already supports multi-year from Phase 2C.

### User Actions

- Confirm the **first range of years** to support (e.g. last 5 festivals?).
- Confirm **preferred data sources** — official Wacken first, then public sources if needed.
- Review and approve historical lineup data quality for the first imported years.
- Decide storage: more JSON files in `data/lineups/`, cached locally, or SQLite?

### Claude's Actions

- Research available historical lineup sources.
- Extend the lineup data model with `year`, `band name`, `source URL`, optional stage/day metadata.
- Build an import or curation process per year.
- Add a year selector to the UI.
- Reuse existing playlist creation and song-source selection.
- Document source attribution.

### Critical Points

- Historical lineup data is often incomplete or inconsistent across public sources.
- Automated scraping can break or violate ToS — prefer manual curation when feasible.
- More bands = more Spotify matching errors and more API volume.

### Completion Gate

A user can select one previous Wacken year, choose bands, and create a playlist via existing ownership modes.

---

## Stage 8 — Mix Years + Shuffle ⏳

**Goal:** combine bands across years; ultimately generate a 50-song shuffled mix.

Split into 4 substages because cross-year state and randomization are fragile.

### Stage 8A — Multi-Year Selection — Medium

**User actions:** confirm year-selection UI (checkboxes / multi-select / range); decide whether duplicate-band appearances across years merge or stay separate.

**Claude actions:** multi-year controls, combined lineup display, per-band year labels, duplicate handling rules.

**Gate:** user can select multiple years and see a clean combined band list.

### Stage 8B — Manual Cross-Year Selection — Medium

**User actions:** test selecting bands from different years; confirm playlist ordering (by year, band name, selection order, or randomized).

**Claude actions:** persist selected bands while changing years; selected-bands summary; remove/edit actions; preserve state across refresh where reasonable.

**Gate:** user can build a cross-year band selection manually and create a playlist from it.

### Stage 8C — Shuffle Playlist Generator — High

Goal: pick 10 bands across selected years, pick 5 of each band's top 10 Spotify tracks, dedupe, shuffle → 50-song mix.

**User actions:** confirm whether the 10 bands are app-random or manually picked; whether all 10 must come from different years; whether shuffle avoids repeated artists, repeated songs, or both; whether final order is reshuffled before adding to Spotify.

**Claude actions:** shuffle config panel; selection rules; per-band top-10 fetch; random 5-of-10 pick; dedupe; final order shuffle; preview + reshuffle action; create playlist after confirmation; tests for boundaries, dedup, final size.

**Critical points:** random selection without constraints produces poor results; dedupe can drop the playlist below 50; large multi-band lookups can hit Spotify rate limits; shuffle bugs are easy to miss without tests.

**Gate:** user can generate, preview, reshuffle, and create a 50-song mixed-year playlist or see a clear warning when there aren't enough eligible tracks.

### Stage 8D — Review, Save, Reuse Mixes — Medium–High

**User actions:** decide whether mixes should be saved locally, tied to Spotify login, or exportable; whether saved mixes need editing.

**Claude actions:** saved-mix storage (if wanted); preview history; recreate/update; export/import.

**Gate:** user can save or reuse a mix, or the feature is intentionally deferred.

---

## Stage 9 — Deployment + Production Release ⏳

**Goal:** the app runs reliably on a hosted URL, installable from phone and browser.

**Difficulty:** Medium–High.

### Prerequisites

- ✅ `wsgi.py` (Phase 5C), `ProductionConfig` validation (Phase 5B), CSRF (5A), single-source SW versioning (5D).

### User Actions

- Choose a hosting provider (Render, Fly.io, Railway, PythonAnywhere, or other Flask-friendly host).
- Add the **production redirect URL** in the Spotify Developer dashboard.
- Provide production environment variables (`SECRET_KEY`, Spotify creds, refresh token, setlist.fm key) securely — not via Git.
- Test install behavior on your phone from the hosted URL.
- Test Spotify flows end-to-end from production.
- Review final mobile UI.

### Claude's Actions

- Configure production settings + deployment docs.
- Verify PWA installability from the hosted origin.
- Responsive/mobile polish pass.
- Loading / success / warning / error states consistent.
- Logging for API failures.
- Basic security headers.
- Release checklist.

### Critical Points

- Production Spotify redirect URL must match dashboard config exactly.
- Service worker caching can serve stale assets in production — bump `version.py` deliberately.
- Production secrets handled only via host's secret store.

### Completion Gate

The app is hosted, installable on a phone, and creates Spotify playlists from the production URL using the enabled ownership modes.

---

# Architecture Phases (Reference)

A one-time refactor that prepared the codebase for Stages 2–9. **All six phases are complete.** Full plan in [ARCH_MIGRATION_PLAN.md](ARCH_MIGRATION_PLAN.md). Per-phase detail in `wiki/phaseN_*.md`.

| # | Phase | Purpose | What unlocked it | Status |
|---|---|---|---|---|
| 1 | Config + Models | Typed `Config` classes + dataclasses (`Band`, `PlaylistRequest`, …) | Vocabulary for every later phase | ✅ [details](wiki/phase1_config_models.md) |
| 2 | Data Layer | Band list moved to JSON; `LineupRepository` with year-aware interface; near-duplicate audit | Stage 7 historical years drop in as more JSON files | ✅ [details](wiki/phase2_data_layer.md) |
| 3 | i18n Centralization | Single source of truth `i18n/*.json` injected to template + JS | One edit adds/updates any UI string | ✅ [details](wiki/phase3_i18n.md) |
| 4 | Service Layer Scaffolding | `services/spotify.py`, `services/playlist.py`, `services/setlistfm.py` stub; thin `routes.py` | Stage 2 (done) and Stages 3, 6, 8 have homes | ✅ [details](wiki/phase4_services.md) |
| 5 | Security + Platform Hardening | CSRF, `SECRET_KEY` enforcement, `wsgi.py`, single-source SW versioning | Required before Stage 3 (real Spotify writes) and Stage 9 (deploy) | ✅ [details](wiki/phase5_security_platform.md) |
| 6 | Test Architecture | `conftest.py` + `tests/unit/` and `tests/integration/` split | Unit tests for services without a Flask app | ✅ [details](wiki/phase6_test_architecture.md) |

## Phase → Stage Unlock Map

| App Stage | Needs |
|---|---|
| Stage 2 — Spotify lookup | Phase 4 service layer ✅ |
| Stage 3 — Playlist creation | Phase 5A CSRF + 5B `SECRET_KEY` ✅ |
| Stage 4 — PWA polish | Phase 5D SW versioning ✅ |
| Stage 5 — User OAuth | Phase 5C `wsgi.py` + 5B validation ✅ |
| Stage 6 — setlist.fm | `services/setlistfm.py` stub from 4A ✅ |
| Stage 7 — Historical years | `LineupRepository.get_available_years()` from 2C ✅ |
| Stage 8 — Shuffle | `PlaylistBuilder` from 4A ✅ |
| Stage 9 — Deployment | `wsgi.py` + `ProductionConfig` validation ✅ |

---

# Explicit Non-Goals

To avoid overengineering at this app size, the following are intentionally **out of scope** unless a stage forces them:

- No ORM — Stage 5 sessions will use `Flask-Session` or shelve, not SQLAlchemy.
- No Blueprint split — `routes.py` is small enough; auth Blueprint considered only when OAuth lands.
- No frontend framework — vanilla JS throughout.
- No API versioning — no external API consumers.
- No Docker — deferred to Stage 9 only if the chosen host requires it.
- No async tasks / message queue — Spotify calls stay synchronous unless rate limiting forces it in Stage 9.

---

# Possible Future Enhancements (post-Stage 9)

User login independent of Spotify · favorite bands list · playlist cover image generation · Wacken stage/day schedule planning · time-conflict detection · CSV/JSON export · support other festivals · shareable playlist recipes · admin cleanup for old app-owned playlists.
