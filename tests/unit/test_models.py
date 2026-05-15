import pytest

from wacken_playlist.models import Band, PlaylistPreview, PlaylistRequest, PlaylistResult


def test_band_is_frozen():
    band = Band(name="Powerwolf", year=2026)
    with pytest.raises(Exception):
        band.name = "Sabaton"  # type: ignore[misc]


def test_band_equality_uses_name_and_year():
    assert Band("Powerwolf", 2026) == Band("Powerwolf", 2026)
    assert Band("Powerwolf", 2026) != Band("Powerwolf", 2025)
    assert Band("Powerwolf", 2026) != Band("Sabaton", 2026)


def test_band_is_hashable():
    assert {Band("Powerwolf", 2026), Band("Powerwolf", 2026)} == {Band("Powerwolf", 2026)}


def test_playlist_request_defaults():
    req = PlaylistRequest(playlist_name="x", bands=[Band("Powerwolf", 2026)])
    assert req.language == "en"
    assert req.song_source == "spotify_top"


def test_playlist_result_defaults_to_no_skipped_bands():
    result = PlaylistResult(
        playlist_name="x",
        spotify_url="https://open.spotify.com/playlist/abc",
        track_count=10,
    )
    assert result.skipped_bands == []


def test_playlist_preview_carries_track_count():
    preview = PlaylistPreview(
        playlist_name="x",
        bands=[Band("Powerwolf", 2026)],
        track_count=10,
    )
    assert preview.track_count == 10
    assert preview.bands[0].name == "Powerwolf"
