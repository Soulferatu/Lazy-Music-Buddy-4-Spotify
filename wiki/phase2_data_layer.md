# Phase 2 — Data Layer

**Status:** Implemented
**Branch:** `arch-refactor/phase-1-config-models` (bundled with Phase 1)
**Related:** [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md)

## Overview

Phase 2 moves the band list out of Python source code and gives it a repository interface that supports multi-year lookup from day one. Same behavior, cleaner data ownership.

## What Changed

### 2A — JSON data file

**File:** `wacken_playlist/data/lineups/wacken_2026.json`

The Wacken 2026 lineup now lives as data, not code:

```json
{
  "year": 2026,
  "source_urls": [...],
  "notes": { "dedup_decisions": [...] },
  "bands": ["5th Avenue", "9mm Headshot", ...]
}
```

Updating the lineup is now a data edit with no Python change. Stage 7 (historical years) just needs more JSON files.

### 2B — Near-duplicate audit

Five near-duplicate or non-band entries were resolved. Each decision is recorded in the JSON's `notes.dedup_decisions` field for traceability.

| Removed | Kept | Reason |
|---|---|---|
| `Ten56` | `Ten56.` | Trailing period matches official band styling on Spotify |
| `Troops Of Doom` | `The Troops Of Doom` | Definite article matches official band name |
| `Skylineband` | `Skyline` | Treated as the same act |
| `5th Avenue Hamburg` | `5th Avenue` | Treated as the same act |
| `Maschine's Late Night Show` | *(removed entirely)* | Stage event, not a band — would cause duplicate matching |

The existing exact-duplicate test passed previously because all variants differed exactly. A new normalized-name test (`test_no_normalized_duplicates`) now catches casing, punctuation, and definite-article variants.

### 2C — LineupRepository

**File:** `wacken_playlist/lineup.py`

Replaces the module-level `WACKEN_2026_BANDS` / `WACKEN_2026_SOURCE_URLS` globals with a class:

```python
class LineupRepository:
    def get_bands(self, year: int) -> list[Band]: ...
    def get_band_names(self, year: int) -> list[str]: ...
    def get_available_years(self) -> list[int]: ...
    def get_source_urls(self, year: int) -> list[str]: ...
    def is_valid_band(self, name: str, year: int) -> bool: ...
```

Reads from `data/lineups/wacken_{year}.json`. Caches per-year loads. Raises `LineupNotFoundError` for unknown years.

### App wiring

`create_app()` now attaches a repository instance to the app:

```python
app.lineup = LineupRepository()
```

Routes access it via `current_app.lineup`. The blueprint no longer imports anything from `lineup.py`.

### Tests

- `tests/unit/test_lineup.py` — new, covers `get_bands`, `is_valid_band`, year handling, source URLs, and the normalized-duplicate invariant.
- `tests/test_app.py` — exact-duplicate test moved into the unit test file; module no longer imports the old globals.

## Why This Matters

1. **Data, not code.** Lineup edits no longer require a Python diff.
2. **Multi-year ready.** The interface contract is stable for Stage 7 — adding 2025 means dropping a JSON file.
3. **Service-ready.** `PlaylistBuilder` (Phase 4) can depend on `LineupRepository` without touching disk during unit tests.
4. **Cleaner duplicate guarantee.** Normalized invariant catches the class of mistakes that exact-match could not.

## No Breaking Changes

- All previous integration tests pass unchanged.
- Routes render the same template variables.
- Band list rendered in the UI is the deduped set (179 entries down from 184).

## What's Next

- **Phase 3** — i18n centralization (extract `MESSAGES` to JSON, share with `app.js`).
- **Phase 4** — Service layer (`SpotifyClient`, `PlaylistBuilder`) consuming `LineupRepository` and the Phase 1 models.
