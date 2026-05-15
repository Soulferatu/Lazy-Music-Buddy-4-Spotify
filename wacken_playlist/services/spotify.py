"""Spotify Web API client.

Implements Stage 2 (Client Credentials auth, artist search, top tracks).
Stage 3 will add playlist creation under the app-owned account.
"""
from __future__ import annotations

import base64
import time

import requests


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

    def get_top_tracks(self, artist_name: str, market: str = "US") -> list[dict]:
        """Return up to 10 top tracks for an artist (search-by-artist heuristic).

        `market` is accepted for forward compatibility with the official
        top-tracks endpoint; the current implementation uses /search which is
        market-agnostic but resilient to artists without /top-tracks data.
        """
        token = self.get_client_credentials_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "q": f"artist:{artist_name}",
            "type": "track",
            "limit": self.DEFAULT_TOP_TRACKS_PER_ARTIST,
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

        tracks: list[dict] = []
        for track in items[: self.DEFAULT_TOP_TRACKS_PER_ARTIST]:
            artists = track.get("artists") or []
            primary = artists[0]["name"] if artists else "Unknown"
            tracks.append({"name": track.get("name", ""), "artist": primary})
        return tracks

    def create_playlist(self, name: str, track_uris: list[str]) -> str:
        raise NotImplementedError("Playlist creation lands in Stage 3.")
