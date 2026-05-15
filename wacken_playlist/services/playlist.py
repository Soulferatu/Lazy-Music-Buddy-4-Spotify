"""Playlist orchestration service.

Wraps the data layer (LineupRepository) and external clients (SpotifyClient,
SetlistFmClient) so route handlers stay thin. Current implementations cover
the local-preview flow (Stage 1). Stage 2 wires real Spotify lookup into
build_preview; Stage 3 wires real playlist creation into build_and_create.
"""
from __future__ import annotations

from ..models import PlaylistPreview, PlaylistRequest, PlaylistResult
from .spotify import SpotifyClient


class PlaylistBuilder:
    def __init__(
        self,
        spotify: SpotifyClient,
        tracks_per_band: int = SpotifyClient.DEFAULT_TOP_TRACKS_PER_ARTIST,
    ):
        self._spotify = spotify
        self._tracks_per_band = tracks_per_band

    def build_preview(self, request: PlaylistRequest) -> PlaylistPreview:
        """Build a local preview without calling Spotify (Stage 1 behavior)."""
        return PlaylistPreview(
            playlist_name=request.playlist_name,
            bands=list(request.bands),
            track_count=len(request.bands) * self._tracks_per_band,
        )

    def build_and_create(self, request: PlaylistRequest) -> PlaylistResult:
        raise NotImplementedError("Spotify playlist creation lands in Stage 3.")
