"""Playlist orchestration service.

Stage 2 behavior: build_preview matches each requested band to a Spotify
artist and fetches up to 10 top tracks, returning a preview with matched
and unmatched bands. Stage 3 will fill in build_and_create.
"""
from __future__ import annotations

from ..models import MatchedBand, PlaylistPreview, PlaylistRequest, PlaylistResult
from .spotify import SpotifyClient


class NoMatchedTracksError(Exception):
    """Raised when build_and_create has zero track URIs to add."""


class PlaylistBuilder:
    def __init__(
        self,
        spotify: SpotifyClient,
        tracks_per_band: int = SpotifyClient.DEFAULT_TOP_TRACKS_PER_ARTIST,
    ):
        self._spotify = spotify
        self._tracks_per_band = tracks_per_band

    def build_preview(self, request: PlaylistRequest) -> PlaylistPreview:
        """Assemble preview from pre-resolved band tracks.

        With the pre-resolution system, every band already has Spotify data embedded.
        We just assemble it into preview format. No runtime Spotify calls.
        """
        matched: list[MatchedBand] = []
        unmatched: list[str] = []

        for band in request.bands:
            # Check if band has pre-resolved tracks
            if band.track_count > 0 and band.spotify_id:
                # Convert Track objects to dict format for compatibility with frontend
                track_dicts = [
                    {"uri": t.uri, "name": t.name, "artist": band.name}
                    for t in band.tracks
                ]
                matched.append(
                    MatchedBand(
                        band=band,
                        artist_id=band.spotify_id,
                        artist_name=band.name,
                        tracks=track_dicts,
                    )
                )
            else:
                # Band has no pre-resolved tracks
                unmatched.append(band.name)

        track_count = sum(len(m.tracks) for m in matched)
        return PlaylistPreview(
            playlist_name=request.playlist_name,
            bands=list(request.bands),
            track_count=track_count,
            matched=matched,
            unmatched=unmatched,
        )

    def build_and_create(
        self, request: PlaylistRequest, public: bool = True
    ) -> PlaylistResult:
        """Build the preview and create the playlist in the app-owned account.

        Raises NoMatchedTracksError if every selected band failed to match
        or all matched bands returned zero tracks with URIs.
        """
        preview = self.build_preview(request)
        excluded = set(request.excluded_uris)
        track_uris = [
            track["uri"]
            for matched in preview.matched
            for track in matched.tracks
            if track.get("uri") and track["uri"] not in excluded
        ]
        if not track_uris:
            raise NoMatchedTracksError(
                "No Spotify tracks were resolved for the selected bands."
            )

        spotify_url = self._spotify.create_playlist(
            request.playlist_name, track_uris, public=public
        )
        return PlaylistResult(
            playlist_name=request.playlist_name,
            spotify_url=spotify_url,
            track_count=len(track_uris),
            skipped_bands=preview.unmatched,
        )
