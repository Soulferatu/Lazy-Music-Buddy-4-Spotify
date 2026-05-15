from unittest.mock import MagicMock

import pytest

from wacken_playlist.models import Band, PlaylistRequest
from wacken_playlist.services import PlaylistBuilder, SpotifyClient


@pytest.fixture
def builder():
    return PlaylistBuilder(spotify=MagicMock(spec=SpotifyClient))


def _request(*band_names: str, name: str = "Test playlist") -> PlaylistRequest:
    return PlaylistRequest(
        playlist_name=name,
        bands=[Band(name=n, year=2026) for n in band_names],
    )


def test_build_preview_counts_ten_tracks_per_band(builder):
    preview = builder.build_preview(_request("Powerwolf", "Sabaton", "Saxon"))
    assert preview.track_count == 30
    assert preview.playlist_name == "Test playlist"
    assert [b.name for b in preview.bands] == ["Powerwolf", "Sabaton", "Saxon"]


def test_build_preview_with_empty_selection(builder):
    preview = builder.build_preview(_request())
    assert preview.track_count == 0
    assert preview.bands == []


def test_build_preview_does_not_call_spotify():
    mock_spotify = MagicMock(spec=SpotifyClient)
    builder = PlaylistBuilder(mock_spotify)
    builder.build_preview(_request("Powerwolf"))
    mock_spotify.search_artist.assert_not_called()
    mock_spotify.get_top_tracks.assert_not_called()


def test_build_and_create_not_yet_implemented(builder):
    with pytest.raises(NotImplementedError):
        builder.build_and_create(_request("Powerwolf"))
