# Library Refactor Plan — Play[my W:O:A]list

**Status:** Draft, not started. Authored 2026-05-18.
**Target:** complete before Stage 6 (setlist.fm integration) begins, so setlist data lands in the new structure from day one.
**Owner:** review by user before any code moves.

## Why this refactor exists

Today, [wacken_playlist/data/lineups/wacken_2026.json](wacken_playlist/data/lineups/wacken_2026.json) fuses three concerns into one file:

1. **Lineup membership** — which bands play Wacken 2026.
2. **Artist identity** — canonical name, Spotify artist ID, aliases (currently scattered in `notes.dedup_decisions` and `artist_overrides.json`).
3. **Spotify track data** — resolved tracks per band, with `resolved_at` timestamps.

This was fine for one year and one source. Stage 6 (setlist.fm) and the End-Goal commitments to "historical years" and "cross-year mixes" break it:

- A band returning in 2027 would have its tracks re-resolved and stored twice.
- Setlist.fm data has a different refresh cadence (weekly-ish, tour-driven) than top-tracks (monthly-ish) or lineups (yearly). Mixing all three in one file causes noisy diffs.
- Cross-year shuffle requires deduplication logic at runtime instead of a single shared lookup.
- A song-search "library" reusable by other festivals (Hellfest, Bloodstock) is impossible without splitting.

The fix is normalization: lineups become **thin pointer lists**, and per-source data lives in **dictionary-keyed libraries**.

## Guiding Principles

- **Spotify artist ID is the canonical join key.** Never key a dictionary by band name — that re-introduces the generic-name problem (Phantom, Focus, The Haunted) that `artist_overrides.json` exists to solve.
- **Dict format, not arrays.** Library files use `{spotify_id: {...}}` for O(1) lookup and stable diffs.
- **One concern per file.** Lineup files describe membership only. Library files describe one data source only.
- **Additive migration.** Old `wacken_2026.json` keeps working until a switchover commit. Tests stay green at every step.
- **No behavior change visible to the user** during this refactor. Playlists generated before and after must be identical.
- **Setlist.fm data is out of scope for this plan** — the schema slot is reserved, but populated in Stage 6.

## Target Architecture

```
wacken_playlist/data/
  lineups/
    wacken_2026.json          # thin — see schema below
    wacken_2027.json          # later years drop in alongside
  library/
    artists.json              # canonical artist registry (replaces artist_overrides.json)
    spotify_tracks.json       # per-artist Spotify track cache
    unresolved.json           # replaces unresolved_bands.json
    setlists.json             # RESERVED — schema defined, populated in Stage 6
```

### Schema: `lineups/wacken_YYYY.json`

```json
{
  "year": 2026,
  "source_urls": [...],
  "notes": {
    "withdrawals": [
      { "name": "Nita Strauss", "reason": "Withdrew due to pregnancy" }
    ],
    "non_band_entries": [
      { "name": "Maschine's Late Night Show", "reason": "Stage event, not a band" }
    ]
  },
  "bands": [
    "1biWH85uIGqR8Nj7oKU5J9",
    "2Sm4rGKWBnOQhdqDy4JJh0",
    "..."
  ]
}
```

Notes:
- `bands` is now an array of **Spotify artist IDs** (strings). Order is preserved for now (matches current behavior) but no longer load-bearing — sort happens at read time.
- `notes.dedup_decisions` retires. Dedup info that's structural (aliases, alternate spellings) moves into `library/artists.json`. Dedup info that's editorial (withdrawals, non-band stage events) stays here in dedicated sections.

### Schema: `library/artists.json`

```json
{
  "_meta": {
    "description": "Canonical artist registry. Keyed by Spotify artist ID.",
    "updated_at": "2026-05-18"
  },
  "artists": {
    "1biWH85uIGqR8Nj7oKU5J9": {
      "name": "5th Avenue",
      "aliases": ["5th Avenue Hamburg"],
      "mbid": null,
      "override_source": null,
      "notes": null
    },
    "2WLmgv66Uq4vt2i36vwkAq": {
      "name": "The Haunted",
      "aliases": [],
      "mbid": null,
      "override_source": "manual_2026-05-17",
      "notes": "Search picks wrong artist without override"
    }
  }
}
```

Notes:
- Replaces [artist_overrides.json](wacken_playlist/data/lineups/artist_overrides.json) entirely. An "override" is just an artist whose entry exists *before* the resolver runs.
- `mbid` field is reserved for Stage 6 setlist.fm lookup. Stays `null` during this refactor.
- `aliases` migrates the `notes.dedup_decisions` data from `wacken_2026.json` into something queryable.

### Schema: `library/spotify_tracks.json`

```json
{
  "_meta": {
    "description": "Per-artist Spotify track cache. Keyed by Spotify artist ID.",
    "updated_at": "2026-05-18"
  },
  "artists": {
    "1biWH85uIGqR8Nj7oKU5J9": {
      "tracks": [
        { "uri": "spotify:track:2YCJBTkQlFmj6LcRCsKNfe", "name": "Ocean" },
        ...
      ],
      "track_count": 10,
      "resolved_at": "2026-05-17"
    }
  }
}
```

### Schema: `library/unresolved.json`

```json
{
  "_meta": { "updated_at": "2026-05-18" },
  "entries": [
    {
      "name": "Wacken Firefighters",
      "lineup_years": [2026],
      "permanently_unresolved": true,
      "note": "Wacken-local act, no Spotify presence"
    }
  ]
}
```

Replaces [unresolved_bands.json](wacken_playlist/data/lineups/unresolved_bands.json). Adds `lineup_years` so a band's appearance across years is tracked even when it can't be resolved.

### Schema: `library/setlists.json` (RESERVED)

```json
{
  "_meta": { "description": "RESERVED — populated in Stage 6", "updated_at": null },
  "artists": {}
}
```

Slot exists so Stage 6 doesn't trigger another refactor. Expected per-entry shape (subject to revision in Stage 6):

```json
"<spotify_id>": {
  "mbid": "...",
  "latest_setlist": {
    "setlist_id": "...",
    "event_date": "2025-08-01",
    "venue": "Wacken Open Air",
    "songs": [
      { "name": "Caught In A Mosh", "spotify_uri": "spotify:track:..." }
    ]
  },
  "resolved_at": "..."
}
```

## Phased Migration

Each phase is a standalone PR. Tests stay green at every phase boundary.

### Phase 1 — Build the library files (read-only, no consumers)

**Goal:** generate `library/*.json` from existing data. Nothing reads them yet.

- Write `scripts/build_library.py` — one-shot migration:
  - Reads `wacken_2026.json`, `artist_overrides.json`, `unresolved_bands.json`.
  - Emits `library/artists.json`, `library/spotify_tracks.json`, `library/unresolved.json`, `library/setlists.json` (empty `artists: {}`).
  - Pulls aliases from `notes.dedup_decisions`.
  - Idempotent: re-running produces identical output.
- Commit the generated library files alongside the script.
- **Old files remain unchanged.** App still reads `wacken_2026.json` as before.
- **Test:** add a unit test that loads both old and new sources and asserts every band in `wacken_2026.json` is present in `library/artists.json` with the same track list.

### Phase 2 — Introduce `LibraryRepository`, keep `LineupRepository`

**Goal:** new read path exists in parallel. Old read path unchanged.

- Add [wacken_playlist/library.py](wacken_playlist/library.py) — `LibraryRepository` class with:
  - `get_artist(spotify_id) -> ArtistRecord`
  - `get_tracks(spotify_id) -> list[Track]`
  - `is_permanently_unresolved(spotify_id) -> bool`
- Add models: `ArtistRecord` (name, aliases, mbid, notes) in `models.py`.
- Wire into `create_app` as a sibling service to `LineupRepository`.
- Unit tests for `LibraryRepository` against fixture library files.
- **No route or builder changes yet.**

### Phase 3 — Switch `LineupRepository` to thin format, behind a feature flag

**Goal:** lineup file becomes pointer list. Reads join with library.

- Create `wacken_playlist/data/lineups/wacken_2026.thin.json` (pointer-only format) via the build script.
- Update `LineupRepository.get_bands()` to support **both** shapes:
  - If `bands[0]` is a string ID → join with `LibraryRepository`.
  - If `bands[0]` is a dict → existing path.
- Add a config flag `USE_THIN_LINEUPS` (default `False`).
- Tests cover both code paths.
- **Runtime behavior unchanged with flag off.**

### Phase 4 — Cutover

**Goal:** flip the flag, retire the fat format.

- Set `USE_THIN_LINEUPS = True` in `DevelopmentConfig` and `ProductionConfig`.
- Replace `wacken_2026.json` with the thin version. Old file moves to `raw/wacken_2026.fat.json` for audit.
- Manual smoke test: generate a playlist, compare track URIs against pre-refactor output.
- Run full test suite.

### Phase 5 — Rewrite the resolver

**Goal:** `scripts/resolve_lineup.py` writes to `library/`, not to lineup files.

- Resolver now writes to `library/spotify_tracks.json` and `library/unresolved.json`.
- Lineup files are read-only inputs (it only consults them to know *which* IDs to resolve).
- `--retry-unresolved`, `--retry-low-count`, `--below-threshold-only` flags continue to work, scoped to library entries.
- Update [wiki/band_track_resolution.md](wiki/band_track_resolution.md) to reflect the new write target.
- Delete `artist_overrides.json` (data already migrated into `library/artists.json` in Phase 1).

### Phase 6 — Remove the dual-path code

**Goal:** delete the fat-format branch in `LineupRepository`.

- Remove the `isinstance(item, dict)` branch.
- Remove the `USE_THIN_LINEUPS` flag.
- Delete unused models or fields.
- Update CLAUDE.md, PHASES.md, and the wiki.

## Files Touched (estimate)

| File | Phase | Change |
|---|---|---|
| `scripts/build_library.py` | 1 | New |
| `wacken_playlist/data/library/*.json` | 1 | New (4 files) |
| `tests/unit/test_library_parity.py` | 1 | New |
| `wacken_playlist/library.py` | 2 | New |
| `wacken_playlist/models.py` | 2 | Add `ArtistRecord` |
| `wacken_playlist/__init__.py` | 2 | Wire `LibraryRepository` |
| `tests/unit/test_library_repository.py` | 2 | New |
| `wacken_playlist/lineup.py` | 3, 6 | Dual-path then single-path |
| `wacken_playlist/config.py` | 3, 6 | Add then remove flag |
| `wacken_playlist/data/lineups/wacken_2026.json` | 4 | Replaced with thin format |
| `raw/wacken_2026.fat.json` | 4 | Archived original |
| `scripts/resolve_lineup.py` | 5 | Write target changes |
| `wacken_playlist/data/lineups/artist_overrides.json` | 5 | Deleted |
| `wacken_playlist/data/lineups/unresolved_bands.json` | 5 | Deleted |
| `CLAUDE.md`, `PHASES.md`, `wiki/band_track_resolution.md` | 6 | Reflect new layout |

## Explicit Non-Goals

- **No setlist.fm integration.** Schema slot only. Real data lands in Stage 6.
- **No MusicBrainz ID resolution.** `mbid` field stays `null`. MBID population is a Stage 6 sub-task with its own resolver script.
- **No new festivals.** Architecture supports Hellfest etc., but no non-Wacken lineup is added by this plan.
- **No multi-year UI features.** Cross-year mix UI is Stage 7+. This plan only enables it.
- **No new models package, no DI container, no Blueprint split.** Same restraint as `ARCH_MIGRATION_PLAN.md`.

## Open Questions Before Starting

1. **Order in `bands[]`** — alphabetical, or preserve the current resolution-order? Alphabetical produces cleaner diffs when bands are added or removed. Current order has no semantic meaning.
2. **Unresolved bands in lineup file** — when a Wacken-announced band has no Spotify ID at all (so no key for the library), how is it referenced from `wacken_2026.json`? Options: (a) keep a parallel `unresolved_names: [...]` list in the lineup file, (b) mint synthetic IDs like `unresolved:wacken-firefighters`. Recommend (a) for clarity.
3. **Phase pacing** — six phases is a lot for a side project. Acceptable to fold Phases 1+2 into one PR, and 5+6 into one PR? Reduces to 4 PRs.

## Risks

- **Migration script bug silently drops a band.** Mitigation: Phase 1 parity test asserts band count and track URIs match exactly between old and new sources.
- **Resolver script breakage during Phase 5.** Mitigation: keep `--dry-run` mode, run against a copy of `library/` first.
- **Diff noise on first commit.** The thin-format `wacken_2026.json` will look like a total rewrite in `git blame`. Mitigation: archive the original at `raw/wacken_2026.fat.json` so history is preserved out-of-tree.

## Out of Scope for This Plan (future possibilities)

- Per-festival library partitioning if multiple festivals are added later.
- SQLite migration if the library grows past ~1000 artists.
- A web UI for editing `library/artists.json` aliases and overrides.
