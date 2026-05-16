# Stage 3 — App-Owned Playlist Creation

Stage 3 delivers the first end-to-end "create a real Spotify playlist" flow.
A visitor selects bands, previews, hits **Create Spotify playlist**, and
receives a link to a playlist owned by the dedicated app-owned account. No
visitor login is required.

## What Was Built

### One-Time OAuth Setup Flow (dev-only)

Two routes, both gated on `app.config["DEBUG"]` (return 404 in production):

- `GET /auth/spotify/login` — generates a CSRF `state`, stores it in the
  Flask session, and redirects to Spotify's `/authorize` endpoint with the
  scopes `playlist-modify-public playlist-modify-private` and
  `show_dialog=true` (forces a fresh consent so a `refresh_token` is always
  returned).
- `GET /auth/spotify/callback` — verifies `state`, exchanges the auth code
  for tokens, and renders the `refresh_token` in plain text so the operator
  can paste it into `.env` as `SPOTIFY_APP_REFRESH_TOKEN`.

This flow is run **once**, while logged into the app-owned Spotify account.

### `SpotifyClient` Extensions

- `build_authorize_url(state)` — assembles the Authorization Code URL.
- `exchange_code_for_refresh_token(code)` — exchanges the auth code for the
  full token payload; raises `SpotifyAuthError` if `refresh_token` is
  missing.
- `_get_app_access_token()` — refresh-token flow, cached in-memory until
  60 s before expiry.
- `create_playlist(name, track_uris, public=True, description="")` — calls
  `POST /me/playlists`, then `POST /playlists/{id}/items` in 100-URI
  chunks (Spotify's API cap). Returns the public Spotify URL.
- `get_top_tracks` now includes `uri` in each track dict so the result can
  be fed straight into `create_playlist`.

### `PlaylistBuilder.build_and_create`

1. Calls `build_preview(request)` to resolve bands → artists → tracks.
2. Collects every track URI from matched bands.
3. Raises `NoMatchedTracksError` if nothing resolved.
4. Calls `SpotifyClient.create_playlist`.
5. Returns a `PlaylistResult` with the URL, track count, and the list of
   skipped (unmatched) bands.

Default visibility is **public** — the chosen behavior so the shareable
Spotify link is visible to anyone who opens it, not just the app account.

### `POST /create` Route

CSRF-protected (Flask-WTF `CSRFProtect` is global). Re-validates the form
inputs (same rules as `/preview`), runs `build_and_create`, and renders
either the success result panel or a localized error.

Error mapping:

| Exception | i18n key |
| --- | --- |
| `SpotifyConfigError` containing `REFRESH_TOKEN` | `spotify_refresh_token_missing` |
| Other `SpotifyConfigError` | `spotify_config_error` |
| `SpotifyAuthError` | `spotify_auth_error` |
| `SpotifyAPIError` | `spotify_api_error` |
| `NoMatchedTracksError` | `create_no_tracks_error` |

### UI

The summary aside in `index.html` gained a third state — **result** —
showing the playlist name, track count, an "Open in Spotify" link, a
skipped-bands warning when applicable, and a link back to start over. The
preview state gained a hidden form posting the playlist name and band
selection to `/create`.

### Tests

- Unit tests for `create_playlist` cover refresh-token caching, `/me`
  caching, payload shape, and the 100-URI chunking.
- Unit tests for `build_and_create` cover the happy path, partial matches,
  and the `NoMatchedTracksError` path.
- Integration tests for `POST /create` cover the success path, skipped
  bands, no-match error, validation errors, auth-error mapping, and the
  refresh-token-missing message.

All 60 existing + new tests pass.

## Operator Setup Walkthrough

1. Confirm Spotify Developer dashboard has the redirect URI
   `http://127.0.0.1:1337/auth/spotify/callback` registered exactly.
2. Set `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and
   `SPOTIFY_REDIRECT_URI` in `.env`.
3. Open Spotify in a browser, **log in as the app-owned account** (use an
   incognito window to avoid mixing with a personal account).
4. Run `scripts/restart-dev.ps1`.
5. Visit `http://127.0.0.1:1337/auth/spotify/login` → approve.
6. Copy the refresh token displayed on the callback page into `.env` as
   `SPOTIFY_APP_REFRESH_TOKEN=...`.
7. Restart the dev server. The Create button on the preview now works.

## Spotify Web API February 2026 Migration

When this stage was first implemented, `create_playlist` used the
historical endpoints `POST /users/{user_id}/playlists` and
`POST /playlists/{id}/tracks`. These returned `HTTP 403 {"error":
{"status": 403, "message": "Forbidden"}}` with no useful headers or
body detail.

The cause was not scopes, user-management allowlists, app age, or
account state — Spotify **removed both endpoints in their
[February 2026 changelog](https://developer.spotify.com/documentation/web-api/references/changes/february-2026)**.
The replacements (also in force as of the
[March 2026 changelog](https://developer.spotify.com/documentation/web-api/references/changes/march-2026),
which did not revert these) are:

| Old (removed Feb 2026) | New |
| --- | --- |
| `POST /users/{user_id}/playlists` | `POST /me/playlists` |
| `POST /playlists/{id}/tracks` | `POST /playlists/{id}/items` |

`POST /me/playlists` creates the playlist for the authenticated user
only, so the previous `/me` lookup that resolved the user id is no
longer needed and was removed from `SpotifyClient`.

**Lesson:** when a Spotify endpoint returns a bare 403 "Forbidden"
with no detail and all the obvious causes (scopes, allowlist, redirect
URI, account state) check out, the very first thing to inspect is the
[Spotify Web API changelogs](https://developer.spotify.com/documentation/web-api/references/changes/)
for endpoint removals or renames.

**Diagnostics retained:** `SpotifyClient` still logs at INFO level the
granted scopes on token refresh, and at WARNING the response status +
body on any non-2xx playlist response. Useful if a future changelog
moves endpoints again.

## Open Items / Future Work

- Production playlist naming convention or cleanup story (deferred — the
  app-owned account will accumulate playlists over time).
- Setting `description` on the playlist (supported by `create_playlist`
  but not yet wired up).
- Generating cover art (needs the `ugc-image-upload` scope — post-Stage 9).
