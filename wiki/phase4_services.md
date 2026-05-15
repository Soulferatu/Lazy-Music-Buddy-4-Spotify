# Phase 4 — Service Layer Scaffolding

**Status:** Implemented
**Related:** [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md)

## Overview

Phase 4 introduces the `services/` package and pushes orchestration out of `routes.py`. The route handler now does HTTP glue only — parse form, validate, hand to `PlaylistBuilder`, render. When Stage 2 lands real Spotify lookup, it slots into `SpotifyClient` without touching the route.

## What Changed

### 4A — `services/` package

Three modules, all plain classes with constructor injection — no Flask globals inside.

**`services/spotify.py`** — `SpotifyClient`

Real implementations land in Stage 2 (auth, artist search, top tracks) and Stage 3 (playlist creation). For now the methods raise `NotImplementedError` and `is_configured` reports whether credentials are present.

```python
class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri="", app_refresh_token=""): ...
    @property
    def is_configured(self) -> bool: ...
    def get_client_credentials_token(self) -> str: ...        # Stage 2
    def search_artist(self, name) -> dict | None: ...          # Stage 2
    def get_top_tracks(self, artist_id, market="US") -> list:  # Stage 2
    def create_playlist(self, name, track_uris) -> str: ...    # Stage 3
```

**`services/playlist.py`** — `PlaylistBuilder`

Orchestrates a `PlaylistRequest` into a `PlaylistPreview` (today) or `PlaylistResult` (Stage 3). Current `build_preview` does no network I/O — it just multiplies band count by `tracks_per_band`, matching the Stage 1 local preview behavior. The interface is the contract Stage 2 will fill in.

**`services/setlistfm.py`** — `SetlistFmClient`

Stub for Stage 6. Interface defined, body raises `NotImplementedError`.

### 4B — Service wiring in `create_app`

Services are instantiated once at startup and attached to the app:

```python
app.lineup = LineupRepository()
app.spotify = SpotifyClient(...config...)
app.setlistfm = SetlistFmClient(api_key=...)
app.playlist_builder = PlaylistBuilder(app.spotify)
```

Routes reach them via `current_app.playlist_builder`, `current_app.lineup`, etc. No module-level singletons, no import-time side effects.

### 4C — Thinned routes

The `/preview` handler is now glue:

1. Parse form.
2. Validate (band list + name) — produces i18n errors.
3. Build a `PlaylistRequest` from validated input.
4. Call `current_app.playlist_builder.build_preview(request)`.
5. Render.

No business logic in the route. The preview view dict is built from the returned `PlaylistPreview` — the template contract is unchanged, so the existing integration tests pass without edits.

## Tests

New: `tests/unit/test_playlist_builder.py`

- Track count is `len(bands) * tracks_per_band`.
- Empty selection returns an empty preview.
- `build_preview` does **not** call any `SpotifyClient` method (asserted with a `MagicMock(spec=SpotifyClient)`).
- `build_and_create` raises `NotImplementedError` until Stage 3.

Full suite: **22/22 passing.**

## No Breaking Changes

- Integration tests unchanged.
- Initial render unchanged in both languages.
- Preview output unchanged for users.

## What's Next

- **Phase 5** — Security and platform hardening (CSRF, `SECRET_KEY` enforcement, `wsgi.py`, service worker versioning).
- **Stage 2** can now begin: fill in `SpotifyClient.search_artist` / `get_top_tracks` and have `PlaylistBuilder.build_preview` call them.
