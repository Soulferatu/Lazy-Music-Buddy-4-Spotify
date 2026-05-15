# Phase 3 — i18n Centralization

**Status:** Implemented
**Related:** [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md)

## Overview

Phase 3 eliminates the duplication between server-side `MESSAGES` (Python dict in `routes.py`) and client-side `translations` (JS object in `app.js`). All strings now live in JSON files and have exactly one source of truth.

## What Changed

### 3A — Translation JSON files

**Files:** `wacken_playlist/i18n/en.json`, `wacken_playlist/i18n/pt-BR.json`

Flat key/value maps with `{count}` placeholders for pluralized strings:

```json
{
  "band_count": "{count} bands",
  "preview_tracks": "Spotify will later try to add up to {count} tracks: ..."
}
```

A unit test enforces that every supported language has the same key set, so it's impossible to add a string in EN and forget PT-BR.

### 3B — Server-side loader

**File:** `wacken_playlist/i18n/__init__.py`

```python
SUPPORTED_LANGUAGES = ("en", "pt-BR")

@lru_cache(maxsize=None)
def load_translations(language: str) -> dict[str, str]: ...

@lru_cache(maxsize=1)
def load_all_translations() -> dict[str, dict[str, str]]: ...

def normalize_language(language: str | None) -> str: ...
```

Routes pass two things to Jinja:

- `translations` — the active-language dictionary, used directly in `{{ translations.* }}` for the initial server render (no flash of English content).
- `translations_bundle` — every language, serialized via `| tojson` into `<script>window.__translations = ...</script>` for client-side switching.

Validation errors (`playlist_name_required`, `bands_required`) come from the same JSON files via `load_translations(language)[key]` — the old `MESSAGES` dict in `routes.py` is gone.

### 3C — Slim `app.js`

The hardcoded `translations` object is removed. The client reads `window.__translations` and uses a single `format(template, params)` helper to substitute `{count}` placeholders. Plural handling is unified — no more separate function values per language.

## Where Strings Live Now

| Source | Holds | Consumed by |
|---|---|---|
| `i18n/en.json`, `i18n/pt-BR.json` | All UI strings | Server template + injected client bundle |
| `routes.py` | (none — only keys) | Only references string keys for validation errors |
| `app.js` | (none — only logic) | Reads `window.__translations` |

Adding a new translatable string is now a single edit per language file. No Python change, no JS change.

## No Breaking Changes

- All 18 tests pass (5 integration, 13 unit).
- Initial server render produces correctly-localized HTML for both languages.
- Existing language switch behavior unchanged on the client.

## Scoped Out (Deferred)

- **`base.html` extraction.** The plan's target architecture pulls `<head>` and `<header>` into a `base.html` that `index.html` extends. The Phase 3 work injects the bundle directly into `index.html` because there is still only one page. Base extraction becomes useful when a second template arrives (Stage 3 OAuth pages or Stage 7 multi-year picker) and is deferred to that point.

## What's Next

- **Phase 4** — Service layer (`SpotifyClient`, `PlaylistBuilder`) so route logic stops growing as Spotify lookup lands.
