# Stage 2 — Spotify Lookup and Playlist Preview

**Status:** Implemented
**Original branch:** `stage2/spotify-preview` (commit `a45f8b3`)
**Ported into:** `arch-refactor/phase-1-config-models` after Phase 6

## What Stage 2 Delivers

Users selecting bands and pressing Preview now get a real Spotify-backed result:

- Each selected band is searched on Spotify (Client Credentials flow — no user login).
- Exact-name matches win; otherwise the highest-popularity candidate is used.
- Up to 10 top tracks per matched artist are fetched.
- The preview shows expandable per-band track groups, total track count, and a warning list of bands that couldn't be matched.

No playlist is created — that lands in Stage 3.

## Architecture

```
routes.preview ──► PlaylistBuilder.build_preview(PlaylistRequest)
                     │
                     ├─► SpotifyClient.search_artist(name)
                     └─► SpotifyClient.get_top_tracks(artist_name)
                     │
                     └─► PlaylistPreview(track_count, matched=[MatchedBand], unmatched=[str])
```

Key files:

| File | Role |
|---|---|
| `wacken_playlist/services/spotify.py` | `SpotifyClient` — auth, search, top tracks; instance-level token cache |
| `wacken_playlist/services/playlist.py` | `PlaylistBuilder.build_preview` iterates bands, collects matched/unmatched |
| `wacken_playlist/models.py` | `MatchedBand`, `PlaylistPreview` (now carries `matched`, `unmatched`) |
| `wacken_playlist/routes.py` | Catches `SpotifyConfig/Auth/APIError` and surfaces i18n error messages |
| `wacken_playlist/templates/index.html` | Track-group `<details>` and unmatched-warning markup |
| `wacken_playlist/i18n/*.json` | New keys: `preview_tracks_matched`, `unmatched_warning`, three `spotify_*_error` keys |
| `wacken_playlist/static/css/styles.css` | `.track-groups`, `.track-group-header`, `.notice-warning` rules |

## Reconciliation Note

Stage 2 originally shipped on a feature branch with a procedural `wacken_playlist/spotify.py` (module-level functions, global `_token_cache`) and routes that called it directly. Meanwhile the architecture refactor on a parallel branch created the `services/` layer with `SpotifyClient` as a class.

The port (May 2026) keeps the Stage 2 behavior verbatim and moves the logic into the class:

- Module-level `get_access_token` / `search_artist` / `get_top_tracks` → `SpotifyClient` methods.
- Module-level `_token_cache` dict → `self._token` / `self._token_expires_at` instance state.
- `lookup_bands(bands)` (env-reading orchestrator) → `PlaylistBuilder.build_preview(PlaylistRequest)` using the injected client.
- Exception classes (`SpotifyConfigError`, `SpotifyAuthError`, `SpotifyAPIError`) preserved and re-exported via `wacken_playlist.services`.

## Configuration

`.env` needs the Client Credentials pair:

```
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
```

`SPOTIFY_REDIRECT_URI` and `SPOTIFY_APP_REFRESH_TOKEN` are still placeholders — Stage 3 wires them.

When credentials are missing, the preview surfaces `Spotify credentials are not configured.` in the active language; the form remains usable.

## Tests

- `tests/unit/test_spotify_client.py` — token caching, refresh, exact-match preference, popularity fallback, empty results, auth failure.
- `tests/unit/test_playlist_builder.py` — matched/unmatched accounting, zero-band path, all-unmatched path, `build_and_create` still raises.
- `tests/integration/test_routes.py` — full request/response with mocked Spotify: matched tracks render, unmatched warning renders, three error states render the correct i18n message.

`tests/conftest.py` now ships a `mock_spotify` fixture that the `app` fixture installs onto `app.spotify` and a fresh `app.playlist_builder` — so every integration test gets deterministic Spotify behavior without network access.

## What's Next

Stage 3 — app-owned playlist creation. Prerequisites already in place from the architecture migration:

- CSRF (Phase 5A) and `SECRET_KEY` enforcement (Phase 5B) for the new `POST /create` form.
- `wsgi.py` production entry (Phase 5C).
- `PlaylistBuilder.build_and_create(request) -> PlaylistResult` interface (already declared, raises `NotImplementedError`).
