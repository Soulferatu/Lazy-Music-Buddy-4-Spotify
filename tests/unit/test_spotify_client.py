import time
from unittest.mock import patch

import pytest

from wacken_playlist.services.spotify import (
    SpotifyAuthError,
    SpotifyClient,
    SpotifyConfigError,
)


def _make_client():
    return SpotifyClient(client_id="cid", client_secret="csecret")


def _mock_post(json_payload):
    mock = patch("wacken_playlist.services.spotify.requests.post").start()
    mock.return_value.json.return_value = json_payload
    mock.return_value.raise_for_status = lambda: None
    return mock


def _mock_get(json_payload):
    mock = patch("wacken_playlist.services.spotify.requests.get").start()
    mock.return_value.json.return_value = json_payload
    mock.return_value.raise_for_status = lambda: None
    return mock


@pytest.fixture(autouse=True)
def _stop_patches():
    yield
    patch.stopall()


def test_unconfigured_client_raises_config_error():
    client = SpotifyClient(client_id="", client_secret="")
    with pytest.raises(SpotifyConfigError):
        client.get_client_credentials_token()


def test_get_token_caches_until_expiry():
    client = _make_client()
    mock_post = _mock_post({"access_token": "tok-1", "expires_in": 3600})

    assert client.get_client_credentials_token() == "tok-1"
    assert client.get_client_credentials_token() == "tok-1"
    assert mock_post.call_count == 1


def test_get_token_refreshes_when_expired():
    client = _make_client()
    client._token = "old"
    client._token_expires_at = time.time() - 1
    _mock_post({"access_token": "new", "expires_in": 3600})

    assert client.get_client_credentials_token() == "new"


def test_search_artist_prefers_exact_name_match():
    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000
    _mock_get({
        "artists": {
            "items": [
                {"id": "popular", "name": "Hello", "popularity": 80},
                {"id": "exact", "name": "Helloween", "popularity": 60},
            ]
        }
    })

    result = client.search_artist("Helloween")
    assert result["id"] == "exact"


def test_search_artist_falls_back_to_highest_popularity():
    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000
    _mock_get({
        "artists": {
            "items": [
                {"id": "a", "name": "Other", "popularity": 30},
                {"id": "b", "name": "Another", "popularity": 70},
            ]
        }
    })

    result = client.search_artist("NotMatching")
    assert result["id"] == "b"


def test_search_artist_returns_none_when_no_results():
    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000
    _mock_get({"artists": {"items": []}})

    assert client.search_artist("Totally Fake Band") is None


def test_get_top_tracks_returns_up_to_ten_with_artist_field():
    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000
    _mock_get({
        "tracks": {
            "items": [
                {"name": f"Track {i}", "artists": [{"name": "Powerwolf"}]}
                for i in range(12)
            ]
        }
    })

    tracks = client.get_top_tracks("Powerwolf")
    assert len(tracks) == 10
    assert tracks[0] == {"name": "Track 0", "artist": "Powerwolf"}


def test_auth_failure_raises_spotify_auth_error():
    client = _make_client()
    import requests

    with patch(
        "wacken_playlist.services.spotify.requests.post",
        side_effect=requests.RequestException("boom"),
    ):
        with pytest.raises(SpotifyAuthError):
            client.get_client_credentials_token()
