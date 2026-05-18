# Library Refactor — As-Built Tracker

Tracks the in-flight normalization of `data/lineups/wacken_2026.json` into a thin lineup pointer file plus per-source `data/library/*.json` files. Full plan and rationale live in [LIBRARY_REFACTOR_PLAN.md](../LIBRARY_REFACTOR_PLAN.md); this page records decisions, progress, and the as-built state as each phase lands.

## Why this refactor

The current `wacken_2026.json` fuses three concerns:

1. Lineup membership (which bands play 2026).
2. Artist identity (canonical name, Spotify ID, aliases, overrides).
3. Spotify track cache (resolved URIs, `resolved_at`).

Stage 6 (setlist.fm) and the End-Goal commitments to historical years and cross-year mixes require splitting these. Lineups become thin pointer lists; per-source data lives in `library/*.json` keyed by Spotify artist ID.

## Decisions Locked Before Starting

| Decision | Choice | Reason |
|---|---|---|
| Band order in thin lineup file | Alphabetical by canonical name | Cleaner diffs as bands are added/removed; current order has no semantic meaning. |
| Bands with no Spotify ID | Parallel `unresolved_names: [...]` list in lineup file | Clear separation between resolvable pointers and editorial unresolved names. |
| Phase pacing | Folded into 4 PRs (1+2, 3, 4, 5+6) | Plan-suggested compromise between safety and ceremony. |
| Setlist.fm data | Schema slot only; populated in Stage 6 | Out of scope for this refactor. |
| MusicBrainz IDs | `mbid` field reserved, stays `null` | Stage 6 sub-task. |

## Target Layout

```
wacken_playlist/data/
  lineups/
    wacken_2026.json          # thin: { year, source_urls, notes, bands: [ids], unresolved_names: [strings] }
  library/
    artists.json              # canonical artist registry (replaces artist_overrides.json)
    spotify_tracks.json       # per-artist Spotify track cache
    unresolved.json           # replaces unresolved_bands.json
    setlists.json             # RESERVED — Stage 6
```

Schemas: see [LIBRARY_REFACTOR_PLAN.md](../LIBRARY_REFACTOR_PLAN.md#target-architecture).

## Phase Progress

| Phase | Scope | Status |
|---|---|---|
| 1+2 | Build `library/*.json` from current data + `LibraryRepository` (parallel read path; nothing consumes it yet) | ✅ Done 2026-05-18 |
| 3 | Dual-path `LineupRepository` behind `USE_THIN_LINEUPS` flag (default off) | ⏳ Pending |
| 4 | Flip flag on; replace `wacken_2026.json` with thin form; archive original to `raw/wacken_2026.fat.json` | ⏳ Pending |
| 5+6 | Resolver writes to `library/`; delete dual-path code, overrides file, and `unresolved_bands.json` | ⏳ Pending |

## As-Built Notes

_To be filled in after each phase ships._

### Phase 1+2 — 2026-05-18

**Build script:** [scripts/build_library.py](../scripts/build_library.py) — re-runnable, idempotent, supports `--check` for drift detection in CI.

**Generated files (in `wacken_playlist/data/library/`):**
- `artists.json` — 169 artists. 14 carry `override_source: "manual_2026-05-17"` (mirroring `artist_overrides.json`). 4 carry `aliases` pulled from `notes.dedup_decisions` (5th Avenue, Skyline, The Troops Of Doom, Ten56.).
- `spotify_tracks.json` — 169 entries, 1,485 total tracks at build time. 5 entries flagged `permanently_unresolved: true` with their `note` (Ballroom DJ Team, Blood Fire Death, Cowgirls From Hell, Wacken Firefighters, Heavysaurus).
- `unresolved.json` — `entries: []`. Every band in current `unresolved_bands.json` has a Spotify ID, so the truly-Spotify-less list is empty. Schema reserved for future years.
- `setlists.json` — `artists: {}`. Reserved for Stage 6.

**Where the `permanently_unresolved` flag lives:** decided to put it on the per-artist entry inside `spotify_tracks.json` (not in `artists.json`). It qualifies track availability, not artist identity. Resolver will check the same shape in Phase 5+6.

**New module:** [wacken_playlist/library.py](../wacken_playlist/library.py) — `LibraryRepository` with `get_artist`, `has_artist`, `get_tracks`, `get_track_count`, `is_permanently_unresolved`, `iter_artist_ids`, `unresolved_names`. Reads with lazy single-file caching. Wired into `create_app` as `app.library`; not consumed yet.

**New model:** `ArtistRecord` in [wacken_playlist/models.py](../wacken_playlist/models.py).

**Tests:** [tests/unit/test_library_parity.py](../tests/unit/test_library_parity.py) (8 assertions: every band present, track lists match, override flag mirrors overrides file, `permanently_unresolved` migrated correctly, aliases pulled from dedup, unresolved entries truly have no Spotify ID, setlists empty, build script idempotent via subprocess). [tests/unit/test_library_repository.py](../tests/unit/test_library_repository.py) (11 tests including a real-data smoke test). All 19 pass.

**Data correction bundled with this phase:** 9mm Headshot — Spotify ID corrected from `2Sm4rGKWBnOQhdqDy4JJh0` (wrong artist, 3 stray tracks) to `0hYxXnnFEBBK8JDab4lIEM` (the actual band, German rock act named "9MM" on Spotify). The override file had already pointed to the correct ID; the resolver retry had been blocked by the prior shadow ban. Tracks fetched via the `/v1/artists/{id}/albums` → `/v1/albums/{id}/tracks` path (the search-based `_collect_tracks_for_artist` failed because Spotify's search for "9mm Headshot" returns nothing tagged to this artist). 10 tracks now resolved. Total goes 1,485 → 1,492 tracks (was 3 stray; now 10 real).

**Open follow-up:** the broader `/v1/artists/{id}/albums` fallback is still not wired into `resolve_lineup.py` (CLAUDE.md flags this as "deferred" — it's what would unblock Minotaurus, Sacred Steel, and other name-collision casualties). Handled here only as a one-off for 9mm Headshot.

### Phase 3
_pending_

### Phase 4
_pending_

### Phase 5+6
_pending_

## Guardrails

- Tests stay green at every phase boundary.
- No behavior change visible to the user — playlists generated before and after the cutover must match.
- Spotify artist ID is the canonical join key. Never key a library by band name.
- Migration is additive: old format stays readable until the Phase 4 cutover.

## Related

- [LIBRARY_REFACTOR_PLAN.md](../LIBRARY_REFACTOR_PLAN.md) — full plan with schemas, file-touch table, and risks.
- [wiki/band_track_resolution.md](band_track_resolution.md) — current as-built resolver; will be rewritten in Phase 5+6.
- [wiki/track_topup_plan.md](track_topup_plan.md) — most recent data state the refactor migrates from.
- [PHASES.md](../PHASES.md) — Stage 6 (setlist.fm) is the consumer this refactor unblocks.
