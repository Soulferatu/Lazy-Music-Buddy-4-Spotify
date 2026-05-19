# Library Refactor — As-Built Tracker

Tracks the in-flight normalization of `data/lineups/wacken_2026.json` into a thin lineup pointer file plus per-source `data/library/*.json` files. Full plan and rationale live in [LIBRARY_REFACTOR_PLAN.md](../LIBRARY_REFACTOR_PLAN.md); this page records decisions, progress, and the as-built state as each phase lands.

## ⏸ Resume Here — Phase 4 Next

**Where we paused:** Phase 3 done. `wacken_2026.thin.json` exists, `LineupRepository` reads both shapes, `USE_THIN_LINEUPS` flag added (default `False` everywhere). Runtime still uses the fat file. Tests stay at the same baseline (9 pre-existing failures unchanged; 10 new passing tests).

**Next session — Phase 4 task list (the cutover):**
1. Set `USE_THIN_LINEUPS = True` on `DevelopmentConfig` and `ProductionConfig` (keep `TestingConfig` controlled per-test).
2. Manual smoke test against a Flask dev run with the flag on: preview a playlist, create one, compare track URIs against a baseline taken pre-flip. Document the comparison in the as-built notes.
3. Move the current fat `wacken_playlist/data/lineups/wacken_2026.json` to `raw/wacken_2026.fat.json` (audit copy, out of the read path).
4. Promote `wacken_2026.thin.json` to `wacken_2026.json`. Update `scripts/build_library.py` so its output filename matches the promoted name (it stops writing a separate `.thin.json` from this point).
5. Update `LineupRepository._path_for` to drop the `.thin.json` suffix when `use_thin` is True — both modes read `wacken_YYYY.json`; the shape determines which path runs.
6. Update `scripts/resolve_lineup.py` minimally so it does **not** break on the thin shape. The full resolver rewrite is Phase 5+6, but if Phase 4 leaves only a thin file in place, the resolver needs at least a "refuse to run / clear error" branch until then. Decide between (a) gating the resolver on the fat file being present, (b) reading the fat file from `raw/` for now, (c) accepting the thin shape and writing to `data/library/spotify_tracks.json` (which is Phase 5's job anyway).
7. Tests: full suite green except the same pre-existing 9. Cover both code paths in `tests/unit/test_lineup.py` after the rename.
8. Bump `wacken_playlist/version.py` (cache-bust SW + static assets).
9. CLAUDE.md, PHASES.md, wiki/library_refactor.md, wiki/band_track_resolution.md all reflect the cutover.

**Open question for Phase 4:** the resolver-during-cutover handling above (Phase 4 task 6). Worth a small decision before code touches.

**Don't touch in Phase 4:**
- The resolver rewrite proper (Phase 5+6).
- `artist_overrides.json` and `unresolved_bands.json` (delete in Phase 5+6 once resolver writes to library directly).
- The pre-existing 9 failing tests.
- The permanently-unresolved UX (badge + warning copy). Separate follow-up PR after Phase 4 — see the "Tracked Follow-Up" section below for the locked schema and UI sketch.

**Commands to remind yourself of state:**
- `py scripts/build_library.py --check` — confirms library + thin lineup in sync with the fat source.
- `py -m pytest` — 84 pass, 9 pre-existing fail.
- `git log --oneline -5` — Phase 3 commit on top.

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
| 3 | Dual-path `LineupRepository` behind `USE_THIN_LINEUPS` flag (default off) | ✅ Done 2026-05-19 |
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

### Phase 3 — 2026-05-19

**Thin lineup file:** [wacken_playlist/data/lineups/wacken_2026.thin.json](../wacken_playlist/data/lineups/wacken_2026.thin.json) — produced by [scripts/build_library.py](../scripts/build_library.py) (extended in this phase to emit a 5th output). Shape:
- `year`, `source_urls` carried over verbatim.
- `notes.withdrawals` / `notes.non_band_entries` migrated from the fat file's `notes.dedup_decisions` entries where `kept` is null (alias entries with `kept != null` continue to live in `library/artists.json`). Classification rule: reason text containing "withdrew" / "withdrawal" → withdrawals; everything else → non_band_entries. Today: 1 each (Nita Strauss withdrew; Maschine's Late Night Show is a stage event).
- `bands` is a list of 169 Spotify artist IDs, sorted alphabetically by canonical name (case-insensitive — same order as `artists.json` and `spotify_tracks.json` so the three files diff cleanly together).
- `unresolved_names: []` — reserved per the locked schema; empty today since every band has a Spotify ID.

**Config flag:** `USE_THIN_LINEUPS` added to the base `Config` class in [wacken_playlist/config.py](../wacken_playlist/config.py), default `False`. Inherited by Development, Testing, Production unchanged. Phase 4 flips Dev + Prod.

**Dual-path `LineupRepository`:** [wacken_playlist/lineup.py](../wacken_playlist/lineup.py) now accepts `library: LibraryRepository | None` and `use_thin: bool` in its constructor. When `use_thin=True`:
- `_path_for(year)` returns `wacken_YYYY.thin.json`.
- `get_bands(year)` joins each Spotify ID against `LibraryRepository.get_artist` + `get_tracks` + `get_track_count` to hydrate the `Band` dataclass.
- `get_band_names(year)` reads names off the library too.
- `is_valid_band` delegates to `get_band_names` (works for both shapes).
- `get_available_years` filters by file suffix so fat and thin files in the same dir don't bleed across modes.
- Missing library at read time raises a clear `RuntimeError("LineupRepository is in thin mode but no LibraryRepository was supplied")`.

**Wiring:** [wacken_playlist/__init__.py](../wacken_playlist/__init__.py) builds `app.library` first, then passes it (plus the config flag) to `LineupRepository`. With the default flag off, this is a no-op for runtime behavior; the fat-path branch still serves all reads.

**Tests:** [tests/unit/test_lineup_thin.py](../tests/unit/test_lineup_thin.py) — 10 new tests. Asserts the thin-mode repo returns the same set of bands, same per-band Band data (name, year, tracks, track_count), alphabetical ordering, source URLs preserved, `is_valid_band` works for known + unknown names, thin mode raises without a library, unknown years still raise `LineupNotFoundError`, and the editorial notes section carries both withdrawals and non-band entries. Existing fat-path tests in [tests/unit/test_lineup.py](../tests/unit/test_lineup.py) remain green untouched.

**Suite state:** 84 pass / 9 pre-existing fail (was 74 / 9 before Phase 3). No new regressions.

**Decision notes for Phase 4 (the cutover):** see top-of-page **Resume Here** section. The non-trivial open question is how `scripts/resolve_lineup.py` behaves between the rename (Phase 4) and the resolver rewrite (Phase 5+6), since it currently writes to the fat lineup file.

### Phase 4
_pending_

### Phase 5+6
_pending_

## Tracked Follow-Up (post-refactor)

### Permanently-unresolved UX (separate PR after Phase 4)

Today the app has 5 bands flagged `permanently_unresolved: true` in `library/spotify_tracks.json`. They slip through the UI silently — users can tick them in the checklist and the preview shows them with 0 or 2 tracks, but the existing "unmatched bands" warning only fires when there's no Spotify artist match at all.

| Band | Tracks | Category |
|---|---|---|
| Ballroom DJ Team | 0 | Wacken house act |
| Blood Fire Death | 0 | Tribute act |
| Cowgirls From Hell | 2 | Tribute act |
| Wacken Firefighters | 0 | Wacken-local |
| Heavysaurus | 2 | Real band, thin Spotify catalog (only 2 unique songs ever) |

**Planned UX (locked decisions for the follow-up PR):**
- Bands stay selectable but get a visual marker on the checklist tile (badge / icon).
- If selected, the preview surfaces a clear warning per band — different copy depending on category.
- Two reason categories in the data model: `wacken_local_or_tribute` (the first 4 bands) vs `thin_catalog` (Heavysaurus and any future case). UI shows different copy for each.

**Schema sketch (subject to revision when the PR lands):**

```json
"6uyCfgv8FWIc2mifriVXqw": {
  "tracks": [...],
  "track_count": 2,
  "resolved_at": "...",
  "permanently_unresolved": true,
  "unresolved_reason": "thin_catalog",
  "note": "Only 2 unique songs across 6 release URIs"
}
```

**Where the work lives:** [scripts/build_library.py](../scripts/build_library.py) (read a new `unresolved_reason` from `unresolved_bands.json` or inline rule), `spotify_tracks.json` (new field), `wacken_playlist/models.py` (new `Band` fields?), `routes.py` / `templates/index.html` / `static/css/styles.css` (checklist badge + warning), `i18n/{en,pt-BR}.json` (copy for both reason types).

**Not part of Phase 3 or 4.** Phase 3's contract is "no user-visible behavior change". Phase 4 is the cutover (still no UX change). This is a Phase-4-follow-up commit on its own.

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
