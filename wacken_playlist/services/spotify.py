"""Spotify Web API client.

Currently a scaffold — Stage 2 fills in real implementations against
the Spotify Web API. Methods are defined here so route handlers and
PlaylistBuilder can depend on a stable interface today.
"""
from __future__ import annotations


class SpotifyClient:
    DEFAULT_TOP_TRACKS_PER_ARTIST = 10

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "",
        app_refresh_token: str = "",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.app_refresh_token = app_refresh_token

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_client_credentials_token(self) -> str:
        raise NotImplementedError("Spotify auth lands in Stage 2.")

    def search_artist(self, name: str) -> dict | None:
        raise NotImplementedError("Spotify artist search lands in Stage 2.")

    def get_top_tracks(self, artist_id: str, market: str = "US") -> list[dict]:
        raise NotImplementedError("Spotify top tracks lands in Stage 2.")

    def create_playlist(self, name: str, track_uris: list[str]) -> str:
        raise NotImplementedError("Playlist creation lands in Stage 3.")
