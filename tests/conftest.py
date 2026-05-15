from unittest.mock import MagicMock

import pytest

from wacken_playlist import create_app
from wacken_playlist.config import TestingConfig
from wacken_playlist.services import SpotifyClient


@pytest.fixture
def app():
    return create_app(TestingConfig)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_spotify():
    """A MagicMock that exposes the SpotifyClient interface with safe defaults."""
    mock = MagicMock(spec=SpotifyClient)
    mock.is_configured = True
    mock.search_artist.return_value = {"id": "abc123", "name": "Test Band"}
    mock.get_top_tracks.return_value = [
        {"uri": "spotify:track:xyz", "name": "Song 1"},
    ]
    mock.create_playlist.return_value = "https://open.spotify.com/playlist/xyz"
    return mock
