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

**Stage 6 — setlist.fm Song Source** (next up, not started).

- Stages 0–5 complete (2026-05-16). Stage 5: Vercel deployment live with full PWA support.
- **Hotfix (2026-05-17, v0.5.4)**: Pre-resolution system deployed to fix 17-hour Spotify rate-limit shadow ban. All 169 bands now have tracks resolved offline at build time. Zero Spotify search calls per user session. Track removal UX improved (yellow X, toggle un-exclude).
- **Band resolution improvement (2026-05-17, v0.5.5)**: Rewrote offline resolution system to use artist ID-based filtering instead of name matching. Two-strategy search (artist-qualifier + plain text) with URI deduplication. Resolved 24 of 42 unresolved bands, reducing count to 18 (57% improvement). Remaining 18 include genuinely low-availability artists (e.g., Mantar 4 tracks, niche local bands).
- **Artist-ID overrides + permanent-unresolved flag (2026-05-17, in progress)**: Added `wacken_playlist/data/lineups/artist_overrides.json` (manual band-name → Spotify-artist-ID map) for bands where Spotify's search picks the wrong top hit (generic names like "Phantom", "Focus", "The Haunted"). Resolver now consults overrides before `search_artist`. Also added `permanently_unresolved: true` flag on `unresolved_bands.json` entries (4 Wacken-local / tribute acts) so `--retry-unresolved` skips them. **14 overrides staged for verification** (incl. E.N.D., Force, Novelization, Maschine added after the initial 10); re-run still blocked by an active Spotify shadow ban as of 2026-05-18 — retry pending once rate limit clears.
- **Track top-up (2026-05-18, Steps 1–5 effectively done, v0.5.8)**: [Ten_song_fix.md](Ten_song_fix.md) plan executed. Resolver hardening:
  - Added `--retry-low-count N` flag to [scripts/resolve_lineup.py](scripts/resolve_lineup.py); honors `permanently_unresolved` flag from `unresolved_bands.json`; idempotent (keeps prior data on no improvement).
  - Bumped `MAX_PAGES_ARTIST` 3 → 5 after a diagnostic on **The Limit** showed pages 3–4 of the `artist:"NAME"` qualifier returned tracks the resolver was missing.
  - Added **case-insensitive title dedup** in `_collect_tracks_for_artist` because Spotify often returns multiple URIs for the same song (single / album / compilation / remaster). A global sweep across `wacken_2026.json` found 40 bands with release-variant duplicates inflating their counts (e.g. Evil Jared 7→4, Arroganz/Alien Ant Farm/Goodnight Greatness 10→7).
  - Followed dedup with re-fetch sweeps on the 9/8/7/6 buckets so the resolver could find genuinely-new unique songs that had previously fallen off the end of the 10-URI window.
- **Result:** 136 of 169 bands at the 10-track cap (was 74). Total tracks 1,234 → 1,485 (+251). Below-cap remainder: 5 at 9, 7 at 8, 1 at 6, 2 at 4, 1 at 3, 3 at 2, 1 at 1, 13 at 0 — these are real Spotify ceilings, name-collision casualties (e.g. Minotaurus and Sacred Steel: Spotify's `artist:"NAME"` search now ranks a different artist first, the filter correctly rejects), or already flagged. **Heavysaurus** (`6uyCfgv8FWIc2mifriVXqw`) flagged `permanently_unresolved` — only 2 unique songs across 6 release URIs.
- Handling guide and per-band rationale: [wiki/track_topup_plan.md](wiki/track_topup_plan.md). Handling guide: [wiki/track_topup_plan.md](wiki/track_topup_plan.md).
- Architecture migration (Phases 1–6) complete — service layer, config, models, i18n, security, test split all in place.
- **Library refactor (2026-05-18, in flight — Phase 1+2 done, Phase 3 next)**: see [wiki/library_refactor.md](wiki/library_refactor.md) — has a top-of-page **Resume Here** section with the Phase 3 task list. Splitting `wacken_2026.json` into a thin lineup pointer file plus `data/library/{artists,spotify_tracks,unresolved,setlists}.json`. Folded 4-phase plan (1+2, 3, 4, 5+6) per [LIBRARY_REFACTOR_PLAN.md](LIBRARY_REFACTOR_PLAN.md). Targeted to land before Stage 6 so setlist.fm data uses the new layout from day one.
  - **Phase 1+2 done (commit `35855a2`):** generated `data/library/*.json` (169 artists, 1,492 tracks, 5 permanently_unresolved), built `LibraryRepository`, wired `app.library`. 19 new tests pass. No app behavior change — `LineupRepository` still reads the fat `wacken_2026.json`. Bundled fix: 9mm Headshot artist ID corrected (`2Sm4rGKWBnOQhdqDy4JJh0` → `0hYxXnnFEBBK8JDab4lIEM`), 10 German rock tracks resolved via `/v1/artists/{id}/albums` walk.
  - **Phase 3 next:** dual-path `LineupRepository` behind a `USE_THIN_LINEUPS` config flag (default off). Generate `wacken_2026.thin.json`. No runtime behavior change with the flag off.
- **Known pre-existing test failures on this branch (NOT from the refactor):** 9 tests fail on `dev-search-improvements` since before this work (stale `MAX_PAGES_*` and `create_playlist` call-count assertions, post-v0.5.8). Verified pre-existing on commit `952136c`. To be fixed as a separate follow-up commit after the refactor lands; do not bundle.
- **Next:** complete the library refactor (Phase 3 → 4 → 5+6), then begin Stage 6 (setlist.fm integration). No external-timeline change.
- Optional: Personal Spotify login deferred (app-owned account works for sharing).

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

## Band Track Resolution Strategy

**Offline pre-resolution** (Stage 5, v0.5.4+): all Spotify track lookups happen at build time via `scripts/resolve_lineup.py`, not during user sessions. This eliminates per-session Spotify API calls and rate-limit exposure.

**Artist ID-based filtering** (v0.5.5): the resolution script uses **Spotify artist IDs** (not name strings) to match tracks to bands. This solves ambiguity from:
- Case/capitalization differences (e.g., "Corrosion of Conformity" vs "Corrosion Of Conformity").
- Generic band names (Europe, Focus, Saxon, etc.) that appear multiple times in search results.
- Covers and alternate recordings that share song titles but are by different artists.

**Two-strategy search** (v0.5.5): `scripts/resolve_lineup.py::_collect_tracks_for_artist()` runs both:
1. **artist:"NAME" qualifier** — capped at ~5 results per page post-Feb 2026 Spotify update, but catches official releases.
2. **Plain-text NAME search** — unlimited pagination, catches remixes, live versions, covers (filtered by artist ID to stay on-brand).

Results from both strategies are deduplicated by track URI and filtered to return only tracks where the artist ID matches. Maximum 10 tracks per band.

**Artist-ID overrides** (2026-05-17): `wacken_playlist/data/lineups/artist_overrides.json` maps band names to Spotify artist IDs for cases where `search_artist` picks the wrong artist (generic names like "Phantom", "Focus", "The Haunted"). The resolver consults this map first; if a name is present, it skips `search_artist` and uses the override ID directly. Override IDs are looked up manually on `open.spotify.com/artist/<ID>` and verified before being added.

**Permanently-unresolved bands**: entries in `unresolved_bands.json` with `"permanently_unresolved": true` (and a `"note"` explaining why) are skipped by `--retry-unresolved`. Used for Wacken-local acts (e.g. Wacken Firefighters), house DJs, and tribute bands that have no recorded Spotify presence.

**Retry modes**:
- `py scripts/resolve_lineup.py --retry-unresolved` — re-resolve all non-permanent unresolved bands (uses overrides + skips permanently-unresolved).
- `py scripts/resolve_lineup.py --retry-unresolved --below-threshold-only` — re-resolve only bands with 1-4 tracks; skip those with zero (likely genuinely absent from Spotify).

**Data:** resolved band metadata stored in `wacken_playlist/data/lineups/wacken_2026.json` with embedded track URIs; unresolved outliers in `unresolved_bands.json` for auditing.

**Full as-built reference:** [wiki/band_track_resolution.md](wiki/band_track_resolution.md). The historical proposal that motivated this design lives in [raw/spotify_search_proposal.md](raw/spotify_search_proposal.md) — note that the shipped implementation diverged (kept `get_top_tracks` as a two-strategy method, added `excluded_uris`, added overrides + `permanently_unresolved`).

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
  data/lineups/         wacken_2026.json (with embedded resolved tracks); unresolved_bands.json (for auditing); artist_overrides.json (manual band-name → Spotify-artist-ID map)
  templates/            base.html, index.html
  static/               CSS, JS, service worker, icons
  version.py            Single source of cache-busting version
tests/
  conftest.py
  unit/                 No Flask, no I/O — pure service tests
  integration/          Uses test_client + mocked services
wiki/                   Processed knowledge pages (see Wiki Workflow below)
raw/                    Original source material (prompts, decisions)
scripts/
    resolve_lineup.py   Offline Spotify track pre-resolution with artist ID filtering
    restart-dev.ps1     Windows dev startup
    dev.sh              macOS/Linux dev startup
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
- [wiki/spotify_integration.md](wiki/spotify_integration.md), [wiki/pwa_requirements.md](wiki/pwa_requirements.md), [wiki/stage1_implementation.md](wiki/stage1_implementation.md), [wiki/stage2_spotify_preview.md](wiki/stage2_spotify_preview.md), [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md), [wiki/stage4_pwa_polish.md](wiki/stage4_pwa_polish.md), [wiki/stage5_deployment.md](wiki/stage5_deployment.md), [wiki/band_track_resolution.md](wiki/band_track_resolution.md), [wiki/track_topup_plan.md](wiki/track_topup_plan.md), [wiki/phase1_config_models.md](wiki/phase1_config_models.md) … [wiki/phase6_test_architecture.md](wiki/phase6_test_architecture.md) — deep dives still authoritative for their topics.
