"""Tests for PlaylistBuilder.

Post-v0.5.4, build_preview reads pre-resolved tracks embedded on the
Band object — no runtime Spotify calls. The SpotifyClient mock here
only matters for build_and_create's create_playlist call.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from wacken_playlist.models import Band, PlaylistRequest, Track
from wacken_playlist.services import (
    NoMatchedTracksError,
    PlaylistBuilder,
    SpotifyClient,
)


def _band(
    name: str,
    *,
    tracks: int = 10,
    spotify_id: str | None = None,
    permanently_unresolved: bool = False,
) -> Band:
    """Build a Band with `tracks` pre-resolved Track entries.

    `tracks=0` (and/or `spotify_id=None`) produces an "unmatched" band
    in the builder's terminology — it has no Spotify data to assemble.
    """
    sid = spotify_id if spotify_id is not None else (f"id-{name}" if tracks > 0 else None)
    track_tuple = tuple(
        Track(uri=f"spotify:track:{name}-{i+1}", name=f"Song {i+1}")
        for i in range(tracks)
    )
    return Band(
        name=name,
        year=2026,
        spotify_id=sid,
        tracks=track_tuple,
        track_count=tracks,
        permanently_unresolved=permanently_unresolved,
    )


def _request(*bands: Band, name: str = "Test playlist") -> PlaylistRequest:
    return PlaylistRequest(playlist_name=name, bands=list(bands))


def _make_builder() -> tuple[PlaylistBuilder, MagicMock]:
    """Wire a SpotifyClient mock that only handles create_playlist."""
    mock_spotify = MagicMock(spec=SpotifyClient)
    mock_spotify.create_playlist.return_value = "https://open.spotify.com/playlist/x"
    return PlaylistBuilder(mock_spotify), mock_spotify


def test_build_preview_matches_each_band_and_counts_tracks():
    builder, _ = _make_builder()
    preview = builder.build_preview(_request(
        _band("Powerwolf", tracks=10),
        _band("Sabaton", tracks=10),
        _band("Saxon", tracks=10),
    ))

    assert preview.track_count == 30
    assert [m.band.name for m in preview.matched] == ["Powerwolf", "Sabaton", "Saxon"]
    assert preview.unmatched == []


def test_build_preview_collects_unmatched_bands():
    builder, _ = _make_builder()
    preview = builder.build_preview(_request(
        _band("Powerwolf", tracks=3),
        _band("Totally Fake Band", tracks=0),
    ))

    assert preview.unmatched == ["Totally Fake Band"]
    assert [m.band.name for m in preview.matched] == ["Powerwolf"]
    assert preview.track_count == 3


def test_build_preview_with_all_unmatched_returns_zero_tracks():
    builder, _ = _make_builder()
    preview = builder.build_preview(_request(
        _band("Powerwolf", tracks=0),
        _band("Sabaton", tracks=0),
    ))

    assert preview.track_count == 0
    assert preview.matched == []
    assert preview.unmatched == ["Powerwolf", "Sabaton"]


def test_build_preview_with_empty_selection():
    builder, mock_spotify = _make_builder()
    preview = builder.build_preview(_request())

    assert preview.track_count == 0
    assert preview.matched == []
    # Pre-resolution: no Spotify calls regardless of input.
    mock_spotify.search_artist.assert_not_called()
    mock_spotify.get_top_tracks.assert_not_called()


def test_build_and_create_collects_track_uris_and_calls_create_playlist():
    builder, mock_spotify = _make_builder()
    result = builder.build_and_create(_request(
        _band("Powerwolf", tracks=2),
        _band("Sabaton", tracks=2),
        name="Mix",
    ))

    mock_spotify.create_playlist.assert_called_once()
    args, kwargs = mock_spotify.create_playlist.call_args
    assert args[0] == "Mix"
    assert args[1] == [
        "spotify:track:Powerwolf-1",
        "spotify:track:Powerwolf-2",
        "spotify:track:Sabaton-1",
        "spotify:track:Sabaton-2",
    ]
    assert kwargs == {"public": True}
    assert result.spotify_url == "https://open.spotify.com/playlist/x"
    assert result.track_count == 4
    assert result.skipped_bands == []


def test_build_and_create_reports_skipped_bands():
    builder, _ = _make_builder()
    result = builder.build_and_create(_request(
        _band("Powerwolf", tracks=3),
        _band("Totally Fake Band", tracks=0),
    ))

    assert result.skipped_bands == ["Totally Fake Band"]
    assert result.track_count == 3


def test_build_and_create_raises_when_no_matches():
    builder, mock_spotify = _make_builder()
    with pytest.raises(NoMatchedTracksError):
        builder.build_and_create(_request(
            _band("Powerwolf", tracks=0),
            _band("Sabaton", tracks=0),
        ))
    mock_spotify.create_playlist.assert_not_called()


def test_build_and_create_honors_excluded_uris():
    """The yellow-X track-removal UX (v0.5.4) drops URIs from the
    create_playlist call. Excluded entries are never sent to Spotify."""
    builder, mock_spotify = _make_builder()
    band = _band("Powerwolf", tracks=4)
    excluded = ["spotify:track:Powerwolf-2", "spotify:track:Powerwolf-4"]
    request = PlaylistRequest(
        playlist_name="Mix",
        bands=[band],
        excluded_uris=excluded,
    )
    result = builder.build_and_create(request)

    args, _ = mock_spotify.create_playlist.call_args
    assert args[1] == [
        "spotify:track:Powerwolf-1",
        "spotify:track:Powerwolf-3",
    ]
    assert result.track_count == 2
