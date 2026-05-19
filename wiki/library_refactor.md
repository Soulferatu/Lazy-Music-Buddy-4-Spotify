# Library Refactor — As-Built Tracker

Tracks the in-flight normalization of `data/lineups/wacken_2026.json` into a thin lineup pointer file plus per-source `data/library/*.json` files. Full plan and rationale live in [LIBRARY_REFACTOR_PLAN.md](../LIBRARY_REFACTOR_PLAN.md); this page records decisions, progress, and the as-built state as each phase lands.

## ✅ Refactor Complete

All four phases landed. The next session can move on to Stage 6 (setlist.fm integration); the refactor's `setlists.json` slot is ready to consume.

Quick state pointers:
- Resolver: [scripts/resolve_lineup.py](../scripts/resolve_lineup.py) — canonical writer for `library/spotify_tracks.json`. See [wiki/band_track_resolution.md](band_track_resolution.md) for the full as-built.
- Lineup format: thin pointer list in `data/lineups/wacken_YYYY.json`. Single read path through `LineupRepository`.
- Library files: `data/library/{artists,spotify_tracks,unresolved,setlists}.json`.

Original Phase 5+6 task list (now done) preserved below for history.

## ⏸ Original Phase 5+6 Plan (completed 2026-05-19)

**Where we paused:** Phase 4 (cutover) done. `wacken_2026.json` now holds the thin pointer list in production; the historic fat snapshot lives at `raw/wacken_2026.fat.json` for audit. `USE_THIN_LINEUPS=True` in Dev + Prod. `LineupRepository` auto-creates a sibling `LibraryRepository` when none is supplied. Resolver script refuses to run with a clear error pointing at this page. Tests stay at the same 84 pass / 9 pre-existing fail baseline. Version bumped to `0.5.8a`.

**Next session — Phase 5+6 task list (resolver rewrite + dual-path removal):**

1. Rewrite `scripts/resolve_lineup.py` so the lineup file is read-only:
   - Read which Spotify IDs to resolve from `wacken_playlist/data/lineups/wacken_2026.json` (the thin pointer list) + `wacken_playlist/data/library/artists.json` for canonical names + overrides metadata.
   - Write tracks to `wacken_playlist/data/library/spotify_tracks.json`. Update `track_count`, `resolved_at`, preserve `permanently_unresolved`.
   - Write unresolvable bands (truly Spotify-less, no artist ID at all) to `wacken_playlist/data/library/unresolved.json`.
   - Preserve flags: `--retry-unresolved`, `--retry-low-count`, `--below-threshold-only`, `--test`, `--resume-from-band`. They now scope over library entries.
   - Remove the Phase 4 guard once the new write target is in place.
2. Delete the resolver's reads of `artist_overrides.json` and `unresolved_bands.json` — replace with reads against `library/artists.json` (the `override_source` field signals overrides) and `library/spotify_tracks.json` (`permanently_unresolved`).
3. Delete `wacken_playlist/data/lineups/artist_overrides.json` and `wacken_playlist/data/lineups/unresolved_bands.json` once nothing reads them.
4. Remove dual-path code in `LineupRepository`: drop the `isinstance(item, dict)` branch in `get_bands` / `get_band_names`, drop the `use_thin` constructor arg, drop the `USE_THIN_LINEUPS` flag in `config.py`, drop the now-unused fat-shape paths.
5. Delete `raw/wacken_2026.fat.json` once parity tests are retired. Parity tests in `tests/unit/test_library_parity.py` were retained through Phase 4 as a guardrail against silent drift; the resolver rewrite supersedes them — replace with focused resolver tests.
6. Update [wiki/band_track_resolution.md](band_track_resolution.md) to reflect the library-only write target.
7. Bump `wacken_playlist/version.py` (probably the v0.6.0 we reserved — confirm with user before bumping major).
8. Run the resolver end-to-end once against the live data so `library/spotify_tracks.json` is regenerated through the new path. Probe Spotify first (per memory rule) since the band data is the actual user-facing dataset.
9. CLAUDE.md, PHASES.md, wiki updates.

**Open questions for Phase 5+6:**
- After the resolver rewrite, does the parity test still have a purpose? Probably no — it compares library against the (now-archived) fat snapshot. Delete and replace with a resolver smoke test asserting the rewritten resolver produces a stable library shape.
- The permanently-unresolved UX (tracked follow-up below) — does it ride along in the same PR as Phase 5+6, or stay separate? Recommend separate, after Phase 5+6 commits.

**Don't touch in Phase 5+6:**
- Stage 6 (setlist.fm) integration. Phase 5+6 closes the refactor; Stage 6 starts after.
- The permanently-unresolved UX (badge + warning copy) — its own follow-up PR; see "Tracked Follow-Up" section below.
- The pre-existing 9 failing tests on this branch.

**Commands to remind yourself of state:**
- `py scripts/build_library.py --check` — library + lineup in sync with the archived fat snapshot.
- `py -m pytest` — 84 pass, 9 pre-existing fail.
- `git log --oneline -5` — Phase 4 commit on top.

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
| 4 | Flip flag on; replace `wacken_2026.json` with thin form; archive original to `raw/wacken_2026.fat.json` | ✅ Done 2026-05-19 |
| 5+6 | Resolver writes to `library/`; delete dual-path code, overrides file, and `unresolved_bands.json` | ✅ Done 2026-05-19 |

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

### Phase 4 — 2026-05-19

**Cutover summary:** the thin pointer file is now the canonical lineup format. The fat snapshot moved to `raw/wacken_2026.fat.json` for audit; nothing in the running app reads it. `USE_THIN_LINEUPS=True` on Development + Production configs (TestingConfig inherits the base `False` so individual tests stay explicit).

**File moves:**
- `wacken_playlist/data/lineups/wacken_2026.json` (fat, 169 dicts with embedded tracks) → `raw/wacken_2026.fat.json`.
- `wacken_playlist/data/lineups/wacken_2026.thin.json` → `wacken_playlist/data/lineups/wacken_2026.json` (thin, 169 alphabetical Spotify IDs).

**Code:**
- [scripts/build_library.py](../scripts/build_library.py) now reads `raw/wacken_2026.fat.json` (the archived source of truth) and writes `wacken_playlist/data/lineups/wacken_2026.json` (thin) plus the four library files. Idempotent. `--check` mode unchanged.
- [wacken_playlist/lineup.py](../wacken_playlist/lineup.py): `_path_for` simplified to always return `wacken_YYYY.json`. `__init__` auto-creates a sibling `LibraryRepository(data_dir=self._data_dir.parent / "library")` when none is supplied, so test fixtures and ad-hoc construction (`LineupRepository()`) keep working without manual wiring. The dual-path `isinstance(item, str)` vs `isinstance(item, dict)` branch survives — Phase 5+6 removes it. `get_available_years` simplified (no thin/fat suffix filter).
- [wacken_playlist/config.py](../wacken_playlist/config.py): `USE_THIN_LINEUPS = True` set on Development + Production.
- [wacken_playlist/__init__.py](../wacken_playlist/__init__.py): no changes (already wires `app.library` first then passes it to `LineupRepository`).
- [scripts/resolve_lineup.py](../scripts/resolve_lineup.py) gains a Phase 4 guard at script entry: if the lineup file is in thin shape (first `bands[0]` is a string), print a clear error pointing at this wiki page and exit 2 before any read/write that would corrupt it. Removed in Phase 5+6 when the resolver is rewritten to target `library/spotify_tracks.json`.

**Tests:**
- [tests/unit/test_lineup_thin.py](../tests/unit/test_lineup_thin.py): fixtures renamed (`fat_repo` → `default_repo`); the prior "requires explicit library or raises" test replaced with `test_thin_read_with_missing_library_raises_cleanly` which asserts the auto-created `LibraryRepository` fails loudly when no library files exist under tmp_path. Notes-section assertion updated to point at `wacken_2026.json` (the new canonical filename).
- [tests/unit/test_library_parity.py](../tests/unit/test_library_parity.py): redirected to read `raw/wacken_2026.fat.json` as the parity source. Will be retired in Phase 5+6 once the resolver writes straight to library.
- Existing fat-path tests in `tests/unit/test_lineup.py` continue to pass — they were written shape-agnostic, and `LineupRepository()` now reads the thin file through the auto-created library.
- Full suite: 84 pass / 9 pre-existing fail. Same baseline as Phase 3 — no regressions.

**Baseline integrity check (pre-flip vs post-flip):**
```
band count:        169 → 169 ✓
total tracks:      1,492 → 1,492 ✓
sha256 signature:  2d8794c7a9a3679858be0f411c7353ad260e9ac1030bb294f3588c81c4af4f5d → same ✓
```
Signature = sha256 of `json.dumps(sorted bands by spotify_id, each {id, name, [track URIs]})`.

**Version bump:** [wacken_playlist/version.py](../wacken_playlist/version.py) → `0.5.8a` (user-specified — `0.6.0` reserved for Stage 6 launch).

**Smoke test:** confirmed by the user on the local dev server with `USE_THIN_LINEUPS=True`. Band list loads, all 169 bands present, preview shows the expected track counts per band (10 for the majority of headliners), language toggle works.

### Phase 5+6 — 2026-05-19 (v0.5.9)

**Resolver rewrite:** [scripts/resolve_lineup.py](../scripts/resolve_lineup.py) is now the canonical writer for `data/library/spotify_tracks.json`. Reads the thin lineup file + `library/artists.json`; writes only `library/spotify_tracks.json`. The previous read/write target (the fat `wacken_2026.json` and the separate `artist_overrides.json` + `unresolved_bands.json` audit pair) is gone.

Key behavior changes vs the previous resolver:
- **Pre-flight Spotify probe** built into every batch (`_probe_spotify`). Aborts cleanly with exit 2 if the probe fails — the memory-rule "always probe before a batch retry" is now mechanical.
- **Albums fallback** in `_resolve_one`: when search returns zero tracks tagged to the artist ID, walks `/v1/artists/{id}/albums` (album + single groups) and pulls tracks from each album. This handles the project-name ≠ Spotify-name case (9mm Headshot → "9MM" on Spotify, ID `0hYxXnnFEBBK8JDab4lIEM`).
- **Safety guard**: `_resolve_ids` refuses to overwrite a nonzero entry with zero. A transient 429 / 502 / timeout late in the batch can no longer destroy good track data.
- **No more name-keyed overrides file.** Hand-curated bands keep their Spotify ID directly in the lineup + an `override_source` marker in `library/artists.json` for documentation. The resolver does not branch on overrides — it joins lineup IDs against `artists.json` for the canonical name and runs the same search path for every band.

**Dual-path removal:** [wacken_playlist/lineup.py](../wacken_playlist/lineup.py) simplified. The `use_thin` constructor arg, the `_path_for` shape switch, and the `isinstance(item, dict)` fat branch are gone. `LineupRepository.get_bands` joins lineup IDs through `LibraryRepository` unconditionally. `USE_THIN_LINEUPS` flag deleted from `wacken_playlist/config.py` (no longer in Config / Development / Production).

**Files deleted:**
- `wacken_playlist/data/lineups/artist_overrides.json` (the overrides data moved to `library/artists.json`'s `override_source` field during Phase 1+2; nothing read this file anymore).
- `wacken_playlist/data/lineups/unresolved_bands.json` (`permanently_unresolved` flag moved to `spotify_tracks.json` entries during Phase 1+2; this file was no longer read).
- `scripts/build_library.py` (one-way migration aid; obsolete now that the resolver is the canonical writer for `library/spotify_tracks.json` and the lineup file is hand-curated).
- `raw/wacken_2026.fat.json` (parity tests retired; nothing else read it).

**Tests:**
- Retired: [tests/unit/test_library_parity.py](../tests/unit/test_library_parity.py) — its job was to assert the library mirrored the fat snapshot during the migration. Both inputs are gone now.
- Added: [tests/unit/test_library_consistency.py](../tests/unit/test_library_consistency.py) — 7 tests asserting internal consistency of the library files (every lineup ID has an artists.json + spotify_tracks.json entry; no orphans in either direction; tracks-entry shape is well-formed; setlists empty; unresolved entries don't shadow library artists).
- Rewrote: [tests/unit/test_lineup_thin.py](../tests/unit/test_lineup_thin.py) — fixture renamed (`thin_repo` → `explicit_repo` since "thin" is no longer a mode), `use_thin=True` arg removed, all 10 tests pass.
- Suite: **83 pass / 9 pre-existing fail** (was 84 / 9 — net -1 from retiring 8 parity tests, adding 7 consistency tests).

**Live run during cutover (the lesson):** ran the rewritten resolver end-to-end against all 169 artists. The smoke test (`--test`, first 10 bands) was clean — 9mm Headshot resolved via the albums fallback. The full run made it to band 160 cleanly, then hit a Spotify 429 / 502 wall around band 161; without the safety guard in place yet, ~450 tracks across 53 bands were written as zero. Rolled back from the safeguard backup, added the safety guard, and skipped re-running to avoid further rate-limit pressure. The 9 real improvements observed before the rate-limit (Craft, E.N.D., Focus, Force, Krogi, Mantar, Maschine, Mr. Hurley Und Die Pulveraffen, Nergal) were not preserved; user can run `--retry-unresolved` whenever Spotify is calm to recover them. Library left at 1,492 tracks — the pre-Phase-5+6 baseline.

**Version:** [wacken_playlist/version.py](../wacken_playlist/version.py) → `0.5.9` (refactor complete; `0.6.0` still reserved for Stage 6 launch).

## Tracked Follow-Up (post-refactor)

### ✅ Permanently-unresolved UX (landed 2026-05-19, v0.5.9b)

Shipped as a follow-up commit after the Phase 5+6 refactor. The 5 affected bands now carry a per-reason classification (`wacken_local_or_tribute` for festival house acts and tribute bands, `thin_catalog` for real artists with very small Spotify catalogs) which drives both a checklist badge and a reason-specific preview warning.

**Data:** `wacken_playlist/data/library/spotify_tracks.json` gains `unresolved_reason: "wacken_local_or_tribute" | "thin_catalog"` next to the existing `permanently_unresolved: true` + `note` fields. 4 bands flagged `wacken_local_or_tribute` (Ballroom DJ Team, Blood Fire Death, Cowgirls From Hell, Wacken Firefighters); 1 flagged `thin_catalog` (Heavysaurus).

**Read path:** `LibraryRepository.unresolved_reason(spotify_id) → Optional[str]`. `LineupRepository._band_from_library` plumbs both `permanently_unresolved` and `unresolved_reason` onto the `Band` dataclass.

**UI:**
- Checklist tile: `.band-badge` chip next to the band name. Blood-red for local/tribute, ember-glow for thin catalog. Tile remains selectable.
- Preview: new `.notice-info` block beneath the existing matched-track count, with reason-specific copy per band. The legacy yellow "Could not find on Spotify" warning now filters out bands already in this new notice so the same band never appears twice — it stays as a catch-all for genuinely-unmatched bands (no Spotify ID at all).
- i18n: 5 new keys in `en.json` + `pt-BR.json` (`band_badge_local_or_tribute`, `band_badge_thin_catalog`, `limited_presence_heading`, `limited_presence_{local_or_tribute,thin_catalog}_explanation`).

**Polish:** band-option padding bumped from `11px 14px` to `12px 15px` (~3% larger tiles).

**Tests:** [tests/unit/test_unresolved_reason.py](../tests/unit/test_unresolved_reason.py) — 6 tests covering schema consistency (every flag has a reason; reasons only set when flagged), LibraryRepository + LineupRepository return paths, and the i18n keys exist in both languages. Suite: 89 pass / 9 pre-existing fail.

### Original Permanently-unresolved UX plan (kept for history)

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
