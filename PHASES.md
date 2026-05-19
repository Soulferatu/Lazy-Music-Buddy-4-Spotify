# PHASES.md — Development Roadmap

Detailed phase-by-phase plan for Play[my W:O:A]list. Read [CLAUDE.md](CLAUDE.md) first for the project overview and operating rules.

This roadmap has **two axes**:

- **App Stages 0–8** — the product roadmap (features visible to the user). Deployment was promoted from Stage 9 to Stage 5; there is no Stage 9.
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
| 4 | First PWA polish | Medium | ✅ Done |
| 5 | Deployment + public release | Medium–High | ✅ Done |
| 6 | **setlist.fm song source** | **High** | ⏳ **Pending** |
| 7 | Previous Wacken years | High | ⏳ Pending |
| 8 | Mix years + shuffle | Medium–High | ⏳ Pending |

**Optional Stages** (not required for MVP):
| Opt-1 | Personal Spotify login | High | ⏳ Pending |

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

**Open / deferred:** duplicate-playlist-name handling — Spotify lets accounts have many playlists with the same name (each has a unique id), and we currently mirror that behavior (every Create click creates a fresh playlist). Naming convention or cleanup story for the app account is deferred to post-Stage 8 enhancements. `description` field is supported by `create_playlist` but not wired into the UI; cover-art generation needs `ugc-image-upload` scope (post-Stage 8).

---

## Stage 4 — First PWA Release Polish ✅

**Goal:** make app-owned mode pleasant on phone and browser before adding more features.

**Difficulty:** Medium.

**Status:** complete (2026-05-16). Details in [wiki/stage4_pwa_polish.md](wiki/stage4_pwa_polish.md).

**What was delivered:**

- **Loading states** — Preview and Create buttons disable and relabel while Spotify calls run (`preview_loading` / `create_loading` i18n keys; `button:disabled` style).
- **Mobile auto-scroll** — on viewports < 920 px, the page scrolls to the summary panel automatically after Preview/Create so the result is immediately visible without scrolling past 87 band tiles.
- **Dynamic countdown** — JS calculates days until July 29, 2026 (Holy Grounds opening) from `data-target-date`; no longer hardcoded.
- **Stale copy fixed** — `ready_copy` no longer says "Spotify search begins in later stages."
- **Apple PWA meta tags** — `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, `apple-mobile-web-app-title`, `apple-touch-icon` link.
- **Manifest `scope`** — added `"scope": "/"`.
- **Service worker fix** — removed redundant `self.skipWaiting()` from the activate handler (was a no-op but incorrect).
- **Floating action buttons (FAB)** — Preview/Create buttons are now truly fixed-position in bottom-right corner, stay visible while scrolling, with `pointer-events` handling to prevent interference.
- **Mobile FAB sizing** — on screens ≤760px, buttons adjust padding/position (20px margins, 44px min-height) to prevent cutoff on small devices.
- **Result page buttons** — "Open in Spotify" and "Build another playlist" buttons now display side-by-side with flexbox layout, both styled as ghost buttons (outline with gold border), gracefully stack on mobile.
- **Extended Spotify search** — increased pagination from 2 to 5 pages to improve track matching for bands with generic names (The Haunted, Allt, The Other, etc.).
- **Flask network binding** — changed dev server from `--host 127.0.0.1` to `--host 0.0.0.0` to enable mobile phone testing on local network.
- **Version** — `version.py` → `0.4.0` (cache-bust SW and static assets).

### Prerequisites

- ✅ Single-source service worker versioning (Phase 5D) — already in place.
- ✅ Placeholder app icon already in repo at `wacken_playlist/static/icons/icon.svg` and `icon.png` and wired into `manifest.webmanifest`. Stage 4 can ship with these. To swap in a final icon, just overwrite those two files (same names, same paths) — no code change needed; a `version.py` bump will bust the cache.
- Stage 3 must be working end-to-end.

### Completion Gate

App-owned playlist flow is usable on desktop and mobile; basic PWA install works.

---

## Stage 5 — Deployment + Public Release ✅

**Goal:** deploy the app to a public URL so other users can access it, create playlists, and install it as a PWA on their devices.

**Difficulty:** Medium–High.

**Status:** complete (2026-05-16). Vercel chosen as hosting provider. App is live and tested:
- `vercel.json` — Python build config, routing, environment variables.
- `.vercelignore` — exclude tests, docs, git, and cache files from deployment.
- `DEPLOYMENT.md` — complete walkthrough for Vercel setup.
- ✅ Band list loads, language toggle works, preview flow tested, PWA installable on mobile/desktop.

**Post-deployment improvement (2026-05-17, v0.5.5):** improved offline band track resolution:
- **Artist ID-based filtering** — track matching now uses Spotify's unique artist IDs instead of name string matching, eliminating ambiguity from case differences, generic names, and covers.
- **Two-strategy search** — `scripts/resolve_lineup.py` runs both `artist:"NAME"` qualifier search and plain-text search, deduplicating by track URI and filtering by artist ID. Catches official releases and alternate recordings on-brand.
- **Retry modes** — added `--retry-unresolved` and `--below-threshold-only` flags for targeted re-resolution of 42 problematic bands.
- **Results** — 24 of 42 unresolved bands now resolved (20 below-threshold → 5+ tracks, 4 zero-track → 5+ tracks). Remaining 18 are genuinely low-availability or local artists.
- **Version** — bumped to 0.5.5 to cache-bust after lineup data changes.

**Override-system work (2026-05-17, in progress — pending Spotify rate-limit clearance):**
- Added `wacken_playlist/data/lineups/artist_overrides.json` — manual band-name → Spotify-artist-ID map with 14 verified entries (The Haunted, Mantar, Craft, Mr. Hurley Und Die Pulveraffen, The Other, Focus, Trold, Krogi, Phantom, 9mm Headshot, E.N.D., Force, Novelization, Maschine). Resolver consults it before `search_artist` to bypass disambiguation failures on generic names.
- Added `permanently_unresolved: true` flag on `unresolved_bands.json` entries for 4 Wacken-local / tribute acts that have no Spotify presence (Wacken Firefighters, Ballroom DJ Team, Blood Fire Death, Cowgirls From Hell). `--retry-unresolved` now skips them.
- Updated `scripts/resolve_lineup.py`: `_load_overrides()` helper, `resolve_band(override_id=...)` parameter, override-aware `retry_unresolved`.
- **Blocked (still as of 2026-05-18):** first retry hit a fresh Spotify shadow ban (every request 429). Damaged `wacken_2026.json` was restored from HEAD. Retry still pending once the ban clears. Novelization and Maschine each have only 1 song on Spotify — to be marked `permanently_unresolved` **after** the retry captures that single track.
- See [wiki/band_track_resolution.md](wiki/band_track_resolution.md) for the full as-built resolution system.

**Track top-up — Steps 1–5 effectively done (2026-05-18, v0.5.8):** [Ten_song_fix.md](Ten_song_fix.md) executed end-to-end. **136 of 169 bands at 10-track cap** (was 74). Total 1,234 → 1,485 tracks. Resolver changes: `--retry-low-count N` flag (idempotent, honors `permanently_unresolved`); `MAX_PAGES_ARTIST` bumped 3 → 5 after The Limit diagnostic; case-insensitive **title dedup** added to `_collect_tracks_for_artist` (Spotify returns release-variant duplicates that inflate counts). A global dedup sweep across `wacken_2026.json` found 40 bands with title duplicates (e.g. Evil Jared 7→4, Arroganz/Alien Ant Farm/Goodnight Greatness 10→7). Re-fetch sweeps on the now-deduped 9/8/7/6 buckets pushed most up to 10. Remaining below-cap bands are real Spotify ceilings or **name-collision casualties** (e.g. Minotaurus, Sacred Steel — Spotify's `artist:"NAME"` search now ranks a different artist first; the artist-ID filter correctly rejects, so the resolver can't add to existing data via search). **Heavysaurus** flagged `permanently_unresolved` (2 unique songs only). Spot-checks across Steps 1–3 (Judas Priest, Powerwolf, Vended, Animals As Leaders, Running Wild, Savatage) confirmed no artist-ID drift. Handling guide: [wiki/track_topup_plan.md](wiki/track_topup_plan.md).

### Prerequisites

- Stage 4 complete and mobile-friendly.
- ✅ `wsgi.py` (Phase 5C), `ProductionConfig` validation (Phase 5B), CSRF (5A), single-source SW versioning (5D).
- ✅ Spotify app account set up with `SPOTIFY_APP_REFRESH_TOKEN` in `.env`.

### User Actions

- Choose a hosting provider (Render, Fly.io, Railway, PythonAnywhere, or other Flask-friendly host).
- Register a production domain name (or use provider's default domain).
- Add the **production redirect URL** in the Spotify Developer dashboard (e.g., `https://yourdomain.com/auth/spotify/callback`).
- Provide production environment variables securely via host's secret management:
  - `SECRET_KEY` (strong random secret for session/CSRF)
  - `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` (from Spotify Developer)
  - `SPOTIFY_APP_REFRESH_TOKEN` (from Stage 3 setup)
- Test PWA install from the production URL on a phone.
- Test the full flow end-to-end: select bands → preview → create playlist → open in Spotify.
- Monitor for errors and API failures in production logs.

### Claude's Actions

- Configure `ProductionConfig` with all required environment variables.
- Set production-safe defaults (DEBUG=False, TESTING=False, secure cookies, etc.).
- Verify Spotify redirect URL matches exactly in both code and Spotify dashboard.
- Add production deployment documentation (README section or DEPLOYMENT.md).
- Configure HTTPS enforcement if the host supports it.
- Set up security headers (CSP, X-Frame-Options, etc.).
- Implement basic logging for API failures and unexpected errors.
- Create a release checklist and deployment walkthrough.
- Test PWA installability from the production origin.
- Final responsive/mobile UI review.
- Document the provider's deployment steps (git push, environment variables, domain setup).

### Critical Points

- **Spotify redirect URL must match exactly** — local development uses `http://127.0.0.1:1337`, production uses `https://yourdomain.com`. Both must be registered in the Spotify dashboard.
- **Service worker caching** — old versions stay cached even after deployment. Increment `version.py` to force cache busts.
- **Production secrets are never committed** — use the host's secret store (environment variables, secrets manager, or `.env` files outside Git).
- **HTTPS required** — most hosts provide free HTTPS; ensure it's enabled before sharing the URL.
- **Cold starts** — some hosts spin down idle apps; the first request after inactivity may be slow. This is normal.

### Completion Gate

The app is live at a public URL, installable from phone/desktop, and users can create Spotify playlists without any authentication setup on their end. The app account remains private; users just click "Create" and get a shareable Spotify link.

---

## Stage 6 — setlist.fm Song Source ⏳

**Goal:** let the user choose whether playlist songs come from Spotify top tracks or the most recent setlist.fm setlist.

**Difficulty:** High.

**Status:** pending. Not started. Band resolution improvements (v0.5.5) unblocked Stage 6, but implementation has been deferred pending user decision.

**Blocked by (in-flight):** library refactor — see [wiki/library_refactor.md](wiki/library_refactor.md) (top of page has a **Resume Here** section) and [LIBRARY_REFACTOR_PLAN.md](LIBRARY_REFACTOR_PLAN.md). Phases 1+2, 3 and 4 done; Phase 5+6 (resolver rewrite + dual-path removal) next. Stage 6 starts after the refactor lands so setlist.fm data uses `data/library/setlists.json` from day one.

### Prerequisites

- ✅ `SetlistFmClient` stub already exists from Phase 4A — interface is in place.
- ✅ Offline band resolution (v0.5.5) eliminates per-session Spotify rate-limit exposure.
- ⏳ Library refactor (4-phase plan in flight).

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


---

# Architecture Phases (Reference)

A one-time refactor that prepared the codebase for Stages 2–9. **All six phases are complete.** Full plan in [ARCH_MIGRATION_PLAN.md](ARCH_MIGRATION_PLAN.md). Per-phase detail in `wiki/phaseN_*.md`.

| # | Phase | Purpose | What unlocked it | Status |
|---|---|---|---|---|
| 1 | Config + Models | Typed `Config` classes + dataclasses (`Band`, `PlaylistRequest`, …) | Vocabulary for every later phase | ✅ [details](wiki/phase1_config_models.md) |
| 2 | Data Layer | Band list moved to JSON; `LineupRepository` with year-aware interface; near-duplicate audit | Stage 7 historical years drop in as more JSON files | ✅ [details](wiki/phase2_data_layer.md) |
| 3 | i18n Centralization | Single source of truth `i18n/*.json` injected to template + JS | One edit adds/updates any UI string | ✅ [details](wiki/phase3_i18n.md) |
| 4 | Service Layer Scaffolding | `services/spotify.py`, `services/playlist.py`, `services/setlistfm.py` stub; thin `routes.py` | Stage 2 (done) and Stages 3, 6, 8 have homes | ✅ [details](wiki/phase4_services.md) |
| 5 | Security + Platform Hardening | CSRF, `SECRET_KEY` enforcement, `wsgi.py`, single-source SW versioning | Required before Stage 3 (real Spotify writes) and Stage 5 (deploy) | ✅ [details](wiki/phase5_security_platform.md) |
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

---

# Optional Stages

These are not required for the MVP but add power-user functionality and may be implemented after Stage 8.

## Optional Stage — Personal Spotify Login

**Goal:** let users optionally create the playlist in their own Spotify account instead of using the app-owned account.

**Difficulty:** High.

**Why it's optional:** the app-owned account works perfectly for sharing playlists. Personal login adds session/security complexity and is only needed for users who want direct control over their own Spotify accounts. Most users are happy with the generated link.

### Prerequisites

- Stage 5 (Deployment) complete and live.
- All Stages 6–8 features working (optional, but nice to have alongside personal login).

### User Actions

- Test personal login with your own Spotify account (not the app account).
- Review and approve the UI explaining app-owned vs personal mode.
- Verify that personal playlists appear in your own Spotify library.
- Test logout and session expiration.

### Claude's Actions

- Add a **mode-selection UI** before the band selector (app-owned link OR "Create in my Spotify").
- Implement **user OAuth login** (`GET /auth/spotify/login/user`, callback handling, state-CSRF).
- Add **secure session storage** (Flask-Session or shelve; no SQLAlchemy).
- Implement **user-owned playlist creation path** (`POST /create/user`).
- Add **logout + session expiration** (clear cookies, session cleanup).
- Update tests for mode selection and auth-required behavior.
- Document the personal login flow (user sees two options at the start).

### Critical Points

- User OAuth adds session and security complexity — this is why it's optional.
- Redirect URLs must match for local AND production exactly (as with app account).
- UX must be clear: "Create in my Spotify" vs "Create & share via app account".
- Session tokens should not leak to client-side JavaScript.
- Personal playlists bypass the app account; no cleanup needed on the app side.

### Completion Gate

A user can choose personal mode, log into Spotify with their own account, create a playlist in their own library, and log out. Personal playlists work alongside app-owned playlists.

---

# Explicit Non-Goals

To avoid overengineering at this app size, the following are intentionally **out of scope** unless a stage forces them:

- No ORM — Stage 5 sessions will use `Flask-Session` or shelve, not SQLAlchemy.
- No Blueprint split — `routes.py` is small enough; auth Blueprint considered only when OAuth lands.
- No frontend framework — vanilla JS throughout.
- No API versioning — no external API consumers.
- No Docker — Vercel deploy does not require it.
- No async tasks / message queue — Spotify calls stay synchronous (and after v0.5.4 are zero per user session, so rate limiting is no longer a runtime concern).

---

# Possible Future Enhancements (post-Stage 8)

User login independent of Spotify · favorite bands list · playlist cover image generation · Wacken stage/day schedule planning · time-conflict detection · CSV/JSON export · support other festivals · shareable playlist recipes · admin cleanup for old app-owned playlists.
