# Phase 1 — Config and Models

**Status:** Implemented  
**Branch:** `arch-refactor/phase-1-config-models`  
**Related:** [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md)

## Overview

Phase 1 establishes the foundation for all subsequent architecture work: typed configuration management and reusable data models. No behavior changes — the app works exactly as before, but with a clean vocabulary for services and tests.

## What Changed

### 1A — Config Class

**File:** `wacken_playlist/config.py`

Three config classes replace the ad-hoc `os.environ.get()` pattern:

| Class | Purpose | SECRET_KEY Behavior |
|-------|---------|-------------------|
| `Config` | Base class — reads all environment variables | None (optional) |
| `DevelopmentConfig` | Local development with safe defaults | Falls back to `"dev-only-insecure"` |
| `TestingConfig` | Test fixtures with fixed values | Always `"test-secret"` |
| `ProductionConfig` | Production — no fallbacks, fails if `SECRET_KEY` absent | Must come from `$SECRET_KEY` env var |

**Environment variables supported:**
- `SECRET_KEY` — Flask session signing key
- `SPOTIFY_CLIENT_ID` — Spotify API credentials
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI`
- `SPOTIFY_APP_REFRESH_TOKEN`
- `SETLISTFM_API_KEY` — setlist.fm API key (Stage 6)

### 1B — Models

**File:** `wacken_playlist/models.py`

Four pure Python dataclasses, no Flask dependencies:

```python
@dataclass(frozen=True)
class Band:
    name: str
    year: int
```
Immutable band record. The `year` field supports multi-year playlists (Stage 7).

```python
@dataclass
class PlaylistRequest:
    playlist_name: str
    bands: list[Band]
    language: str = "en"
    song_source: str = "spotify_top"
```
What a user is asking for. Will be used by `PlaylistBuilder` service (Phase 4).

```python
@dataclass
class PlaylistPreview:
    playlist_name: str
    bands: list[Band]
    track_count: int
```
What we show before creation. Returned by `PlaylistBuilder.build_preview()`.

```python
@dataclass
class PlaylistResult:
    playlist_name: str
    spotify_url: str
    track_count: int
    skipped_bands: list[str] = field(default_factory=list)
```
Final result with Spotify link and any bands we couldn't match.

### Updated App Factory

**File:** `wacken_playlist/__init__.py`

```python
def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # ... register blueprints
```

Routes now access config via `current_app.config["SPOTIFY_CLIENT_ID"]` instead of inline `os.environ.get()`.

## Why This Matters

1. **Environment-aware** — Dev, test, and prod configs can have different defaults and validation.
2. **Centralized** — All config lives in one place instead of scattered `os.environ.get()` calls.
3. **Typed** — Type checkers and IDEs understand what config keys exist.
4. **Testable** — Services can be instantiated with a `TestingConfig` and make no real API calls.
5. **Reusable vocabulary** — Models can be imported anywhere without Flask context. Unit tests can build `PlaylistRequest` objects without a running app.

## What's Next

Phase 1 is self-contained and can be merged as-is. Phases 2–6 build on this foundation:

- **Phase 2** (Data Layer) — `LineupRepository` to load bands from JSON data files
- **Phase 3** (i18n) — JSON translation files injected by the server
- **Phase 4** (Services) — `SpotifyClient` and `PlaylistBuilder` classes using these models
- **Phase 5** (Security) — CSRF protection, `SECRET_KEY` enforcement, `wsgi.py`
- **Phase 6** (Tests) — Unit and integration test split using `conftest.py`

See the [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md) for the full dependency graph.

## No Breaking Changes

- Existing routes work unchanged
- Existing tests pass unchanged
- `.env` file is still read the same way
- App behavior is identical to before
