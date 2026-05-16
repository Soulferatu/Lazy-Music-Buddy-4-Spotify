"""Spotify Web API client.

Implements Stage 2 (Client Credentials auth, artist search, top tracks).
Stage 3 will add playlist creation under the app-owned account.
"""
from __future__ import annotations

import base64
import logging
import time
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

APP_OAUTH_SCOPES = "playlist-modify-public playlist-modify-private"


class SpotifyConfigError(Exception):
    """Raised when Spotify credentials are missing or invalid."""


class SpotifyAuthError(Exception):
    """Raised when authentication with Spotify fails."""


class SpotifyAPIError(Exception):
    """Raised when a Spotify API call fails."""


class SpotifyClient:
    DEFAULT_TOP_TRACKS_PER_ARTIST = 10
    _AUTH_URL = "https://accounts.spotify.com/api/token"
    _API_BASE = "https://api.spotify.com/v1"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "",
        app_refresh_token: str = "",
        timeout: float = 10.0,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.app_refresh_token = app_refresh_token
        self._timeout = timeout
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._app_token: str | None = None
        self._app_token_expires_at: float = 0.0

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_client_credentials_token(self) -> str:
        """Return a cached Client Credentials token, fetching if expired."""
        if not self.is_configured:
            raise SpotifyConfigError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"
            )

        now = time.time()
        if self._token and now < self._token_expires_at:
            return self._token

        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}"}
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(
                self._AUTH_URL, headers=headers, data=data, timeout=self._timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise SpotifyAuthError(f"Failed to authenticate with Spotify: {e}")

        try:
            payload = response.json()
            token = payload["access_token"]
            expires_in = payload.get("expires_in", 3600)
        except (KeyError, ValueError) as e:
            raise SpotifyAuthError(f"Invalid token response from Spotify: {e}")

        self._token = token
        self._token_expires_at = now + expires_in - 60
        return token

    def search_artist(self, name: str) -> dict | None:
        """Return the best matching artist (exact-name preferred), or None."""
        token = self.get_client_credentials_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": name, "type": "artist", "limit": 5}

        try:
            response = requests.get(
                f"{self._API_BASE}/search",
                headers=headers,
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise SpotifyAPIError(f"Failed to search for artist '{name}': {e}")

        try:
            artists = response.json().get("artists", {}).get("items", [])
        except ValueError as e:
            raise SpotifyAPIError(f"Invalid search response for artist '{name}': {e}")

        if not artists:
            return None

        target = name.strip().lower()
        for artist in artists:
            if artist.get("name", "").strip().lower() == target:
                return artist

        return max(artists, key=lambda a: a.get("popularity", 0))

    MAX_TOP_TRACKS_PAGES = 5
    _SEARCH_PAGE_SIZE = 10

    def get_top_tracks(self, artist_name: str, market: str = "US") -> list[dict]:
        """Return up to 10 top tracks for an artist.

        Uses a two-strategy approach to maximise reliable matches:

        1. `artist:"NAME"` qualifier first — highly targeted; Spotify caps
           this at ~5 results regardless of `limit`, but all results are
           reliably by the right artist. Essential for bands with generic
           names (e.g. "The Other", "Allt") where a plain-text query
           returns mostly unrelated tracks.

        2. Plain `q=NAME` search for up to MAX_TOP_TRACKS_PAGES pages —
           returns more items but needs client-side primary-artist
           filtering to discard covers and unrelated hits.

        Results are deduplicated by URI across both strategies.

        `market` is accepted for forward compatibility but unused —
        /search is market-agnostic.
        """
        token = self.get_client_credentials_token()
        headers = {"Authorization": f"Bearer {token}"}
        target = artist_name.strip().lower()
        tracks: list[dict] = []
        seen_uris: set[str] = set()

        queries: list[tuple[str, int]] = [
            (f'artist:"{artist_name}"', 0),
        ] + [
            (artist_name, page * self._SEARCH_PAGE_SIZE)
            for page in range(self.MAX_TOP_TRACKS_PAGES)
        ]

        for query, offset in queries:
            if len(tracks) >= self.DEFAULT_TOP_TRACKS_PER_ARTIST:
                break

            params = {
                "q": query,
                "type": "track",
                "limit": self._SEARCH_PAGE_SIZE,
                "offset": offset,
            }

            try:
                response = requests.get(
                    f"{self._API_BASE}/search",
                    headers=headers,
                    params=params,
                    timeout=self._timeout,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                raise SpotifyAPIError(
                    f"Failed to fetch tracks for artist '{artist_name}': {e}"
                )

            try:
                items = response.json().get("tracks", {}).get("items", [])
            except ValueError as e:
                raise SpotifyAPIError(
                    f"Invalid search response for artist '{artist_name}': {e}"
                )

            page_matches = 0
            for track in items:
                artists = track.get("artists") or []
                if not artists:
                    continue
                primary = artists[0].get("name", "")
                if primary.strip().lower() != target:
                    continue
                uri = track.get("uri", "")
                dedup_key = uri if uri else f"{track.get('name', '').lower()}|{primary.lower()}"
                if dedup_key in seen_uris:
                    continue
                seen_uris.add(dedup_key)
                tracks.append({
                    "name": track.get("name", ""),
                    "artist": primary,
                    "uri": uri,
                })
                page_matches += 1
                if len(tracks) >= self.DEFAULT_TOP_TRACKS_PER_ARTIST:
                    break

            logger.info(
                "Spotify /search?q=%s offset=%d returned %d items; "
                "%d matched primary artist (total matches so far: %d)",
                query,
                offset,
                len(items),
                page_matches,
                len(tracks),
            )

        return tracks

    def build_authorize_url(self, state: str) -> str:
        """Return the Spotify Authorization Code URL for the app-owned account.

        The caller is responsible for generating and verifying `state`.
        """
        if not self.client_id:
            raise SpotifyConfigError("SPOTIFY_CLIENT_ID must be set")
        if not self.redirect_uri:
            raise SpotifyConfigError("SPOTIFY_REDIRECT_URI must be set")

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": APP_OAUTH_SCOPES,
            "state": state,
            "show_dialog": "true",
        }
        return f"https://accounts.spotify.com/authorize?{urlencode(params)}"

    def exchange_code_for_refresh_token(self, code: str) -> dict:
        """Exchange an authorization code for tokens. Returns the raw payload.

        The refresh_token field is the value to persist as
        SPOTIFY_APP_REFRESH_TOKEN.
        """
        if not self.is_configured:
            raise SpotifyConfigError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"
            )
        if not self.redirect_uri:
            raise SpotifyConfigError("SPOTIFY_REDIRECT_URI must be set")

        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        try:
            response = requests.post(
                self._AUTH_URL, headers=headers, data=data, timeout=self._timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise SpotifyAuthError(f"Failed to exchange code with Spotify: {e}")

        try:
            payload = response.json()
        except ValueError as e:
            raise SpotifyAuthError(f"Invalid token response from Spotify: {e}")

        if "refresh_token" not in payload:
            raise SpotifyAuthError(
                "Spotify did not return a refresh_token. Ensure the OAuth flow "
                "is initiated fresh (revoke the app under Spotify account "
                "settings → Apps if needed) and that show_dialog=true is set."
            )
        return payload

    def _get_app_access_token(self) -> str:
        """Return a cached app-owned access token, refreshing if needed."""
        if not self.is_configured:
            raise SpotifyConfigError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"
            )
        if not self.app_refresh_token:
            raise SpotifyConfigError(
                "SPOTIFY_APP_REFRESH_TOKEN is not set. Run the one-time OAuth "
                "flow at /auth/spotify/login to capture it."
            )

        now = time.time()
        if self._app_token and now < self._app_token_expires_at:
            return self._app_token

        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}"}
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.app_refresh_token,
        }

        try:
            response = requests.post(
                self._AUTH_URL, headers=headers, data=data, timeout=self._timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise SpotifyAuthError(
                f"Failed to refresh app-owned access token: {e}"
            )

        try:
            payload = response.json()
            token = payload["access_token"]
            expires_in = payload.get("expires_in", 3600)
        except (KeyError, ValueError) as e:
            raise SpotifyAuthError(
                f"Invalid refresh response from Spotify: {e}"
            )

        logger.info(
            "Spotify app token refreshed. Granted scopes: %s",
            payload.get("scope", "<no scope field>"),
        )
        self._app_token = token
        self._app_token_expires_at = now + expires_in - 60
        return token

    def create_playlist(
        self,
        name: str,
        track_uris: list[str],
        public: bool = True,
        description: str = "",
    ) -> str:
        """Create a playlist in the app-owned account and add the tracks.

        Returns the public Spotify URL of the new playlist. Uses the
        post-February-2026 Web API endpoints: POST /me/playlists for
        creation and POST /playlists/{id}/items for adding tracks. The
        older /users/{user_id}/playlists and /playlists/{id}/tracks
        endpoints were removed by Spotify in February 2026.
        """
        token = self._get_app_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        body = {"name": name, "public": public}
        if description:
            body["description"] = description

        create_url = f"{self._API_BASE}/me/playlists"
        try:
            response = requests.post(
                create_url,
                headers=headers,
                json=body,
                timeout=self._timeout,
            )
            if response.status_code >= 400:
                logger.warning(
                    "Spotify create_playlist failed status=%s body=%s",
                    response.status_code,
                    response.text,
                )
                raise SpotifyAPIError(
                    f"Failed to create playlist '{name}': "
                    f"HTTP {response.status_code} — {response.text}"
                )
            payload = response.json()
        except requests.RequestException as e:
            raise SpotifyAPIError(f"Failed to create playlist '{name}': {e}")
        except ValueError as e:
            raise SpotifyAPIError(f"Invalid create-playlist response: {e}")

        playlist_id = payload.get("id")
        spotify_url = (
            payload.get("external_urls", {}).get("spotify")
            or (f"https://open.spotify.com/playlist/{playlist_id}" if playlist_id else "")
        )
        if not playlist_id:
            raise SpotifyAPIError("Spotify did not return a playlist id.")

        # Spotify caps add-items at 100 URIs per request.
        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i : i + 100]
            try:
                add_response = requests.post(
                    f"{self._API_BASE}/playlists/{playlist_id}/items",
                    headers=headers,
                    json={"uris": chunk},
                    timeout=self._timeout,
                )
            except requests.RequestException as e:
                raise SpotifyAPIError(
                    f"Failed to add tracks to playlist '{name}': {e}"
                )
            if add_response.status_code >= 400:
                raise SpotifyAPIError(
                    f"Failed to add tracks to playlist '{name}': "
                    f"HTTP {add_response.status_code} — {add_response.text}"
                )

        return spotify_url
