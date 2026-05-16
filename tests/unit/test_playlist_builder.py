from unittest.mock import MagicMock

import pytest

from wacken_playlist.models import Band, PlaylistRequest
from wacken_playlist.services import (
    NoMatchedTracksError,
    PlaylistBuilder,
    SpotifyClient,
)


def _request(*band_names: str, name: str = "Test playlist") -> PlaylistRequest:
    return PlaylistRequest(
        playlist_name=name,
        bands=[Band(name=n, year=2026) for n in band_names],
    )


def _make_builder(search_results=None, top_tracks_per_artist=2):
    """Wire a SpotifyClient mock that returns fake artists/tracks."""
    mock_spotify = MagicMock(spec=SpotifyClient)

    def search(name):
        if search_results is None:
            return {"id": f"id-{name}", "name": name, "popularity": 50}
        return search_results.get(name)

    mock_spotify.search_artist.side_effect = search
    mock_spotify.get_top_tracks.side_effect = lambda artist_name, market="US": [
        {
            "name": f"Song {i+1}",
            "artist": artist_name,
            "uri": f"spotify:track:{artist_name}-{i+1}",
        }
        for i in range(top_tracks_per_artist)
    ]
    mock_spotify.create_playlist.return_value = "https://open.spotify.com/playlist/x"
    return PlaylistBuilder(mock_spotify), mock_spotify


def test_build_preview_matches_each_band_and_counts_tracks():
    builder, _ = _make_builder(top_tracks_per_artist=10)
    preview = builder.build_preview(_request("Powerwolf", "Sabaton", "Saxon"))

    assert preview.track_count == 30
    assert [m.band.name for m in preview.matched] == ["Powerwolf", "Sabaton", "Saxon"]
    assert preview.unmatched == []


def test_build_preview_collects_unmatched_bands():
    builder, _ = _make_builder(
        search_results={
            "Powerwolf": {"id": "p", "name": "Powerwolf"},
            "Totally Fake Band": None,
        },
        top_tracks_per_artist=3,
    )
    preview = builder.build_preview(_request("Powerwolf", "Totally Fake Band"))

    assert preview.unmatched == ["Totally Fake Band"]
    assert [m.band.name for m in preview.matched] == ["Powerwolf"]
    assert preview.track_count == 3


def test_build_preview_with_all_unmatched_returns_zero_tracks():
    builder, _ = _make_builder(
        search_results={"Powerwolf": None, "Sabaton": None}
    )
    preview = builder.build_preview(_request("Powerwolf", "Sabaton"))

    assert preview.track_count == 0
    assert preview.matched == []
    assert preview.unmatched == ["Powerwolf", "Sabaton"]


def test_build_preview_with_empty_selection():
    builder, mock_spotify = _make_builder()
    preview = builder.build_preview(_request())

    assert preview.track_count == 0
    assert preview.matched == []
    mock_spotify.search_artist.assert_not_called()


def test_build_and_create_collects_track_uris_and_calls_create_playlist():
    builder, mock_spotify = _make_builder(top_tracks_per_artist=2)
    result = builder.build_and_create(_request("Powerwolf", "Sabaton", name="Mix"))

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
    builder, _ = _make_builder(
        search_results={
            "Powerwolf": {"id": "p", "name": "Powerwolf"},
            "Totally Fake Band": None,
        },
        top_tracks_per_artist=3,
    )
    result = builder.build_and_create(_request("Powerwolf", "Totally Fake Band"))

    assert result.skipped_bands == ["Totally Fake Band"]
    assert result.track_count == 3


def test_build_and_create_raises_when_no_matches():
    builder, mock_spotify = _make_builder(
        search_results={"Powerwolf": None, "Sabaton": None}
    )
    with pytest.raises(NoMatchedTracksError):
        builder.build_and_create(_request("Powerwolf", "Sabaton"))
    mock_spotify.create_playlist.assert_not_called()
