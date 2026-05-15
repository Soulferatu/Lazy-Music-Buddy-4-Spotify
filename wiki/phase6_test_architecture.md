# Phase 6 — Test Architecture

**Status:** Implemented
**Related:** [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md)

## Overview

Phase 6 finishes the architecture migration. It establishes a clear unit-vs-integration split, shared fixtures, model coverage, and cross-platform dev scripts so contributors on macOS or Linux can run the app without rewriting commands.

## What Changed

### 6A — `tests/conftest.py`

Shared fixtures replace ad-hoc per-file helpers:

- `app` — `create_app(TestingConfig)`
- `client` — Flask test client
- `mock_spotify` — a `MagicMock(spec=SpotifyClient)` preloaded with sensible artist / top-track / playlist return values

Any test in `tests/` can request these by parameter name.

### 6B — `unit/` vs `integration/` split

Final layout:

```
tests/
  conftest.py
  unit/
    test_i18n.py
    test_lineup.py
    test_models.py            # new — frozen dataclass invariants, defaults, hashability
    test_playlist_builder.py
    test_security.py
  integration/
    test_routes.py            # moved from tests/test_app.py — now uses the client fixture
```

Unit tests import zero Flask app and make no HTTP calls. Integration tests go through `client.get/post`. `test_security.py` straddles both — it's unit-level configuration plumbing and lives under `unit/` for now.

### 6C — Cross-platform dev script + README

- `scripts/dev.sh` mirrors `scripts/restart-dev.ps1`: best-effort kill of the previous dev server, then `python3 -m flask ... --debug run`. Accepts an optional port arg (`./scripts/dev.sh 1338`).
- `README.md` now documents Windows and macOS/Linux setup side-by-side, points to per-folder pytest invocations, and includes the `gunicorn wsgi:application` production command.

## Tests

Full suite: **35/35 passing** (5 integration + 30 unit).

## What's Next — Architecture Migration Complete

Phases 1–6 are done. The codebase is now ready for app-stage work:

| Stage | Now unblocked by |
|---|---|
| Stage 2 (Spotify lookup) | Phase 4 `SpotifyClient` + `PlaylistBuilder` |
| Stage 3 (Playlist creation) | Phase 5A CSRF + Phase 5B `SECRET_KEY` |
| Stage 4 (PWA polish) | Phase 5D version single-source |
| Stage 5 (User OAuth) | Phase 5B/5C |
| Stage 7 (Historical years) | Phase 2C `LineupRepository.get_available_years()` |
| Stage 9 (Deployment) | Phase 5C `wsgi.py` |

Next product step is **Stage 2 — Spotify lookup and playlist preview**.
