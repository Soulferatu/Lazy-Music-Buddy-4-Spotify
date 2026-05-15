from unittest.mock import MagicMock

import pytest

from wacken_playlist import create_app
from wacken_playlist.config import TestingConfig
from wacken_playlist.services import PlaylistBuilder, SpotifyClient


def _default_mock_spotify() -> MagicMock:
    """A SpotifyClient mock that resolves any band to a matching artist."""
    mock = MagicMock(spec=SpotifyClient)
    mock.is_configured = True
    mock.search_artist.side_effect = lambda name: {
        "id": f"id-{name}",
        "name": name,
        "popularity": 50,
    }
    mock.get_top_tracks.side_effect = lambda artist_name, market="US": [
        {"name": f"Track {i+1}", "artist": artist_name} for i in range(10)
    ]
    mock.create_playlist.return_value = "https://open.spotify.com/playlist/xyz"
    return mock


@pytest.fixture
def mock_spotify() -> MagicMock:
    return _default_mock_spotify()


@pytest.fixture
def app(mock_spotify):
    """Flask app with Spotify mocked out by default."""
    app = create_app(TestingConfig)
    app.spotify = mock_spotify
    app.playlist_builder = PlaylistBuilder(mock_spotify)
    return app


@pytest.fixture
def client(app):
    return app.test_client()
