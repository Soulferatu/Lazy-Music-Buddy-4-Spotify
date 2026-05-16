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
    assert tracks[0] == {"name": "Track 0", "artist": "Powerwolf", "uri": ""}


def test_get_top_tracks_paginates_across_all_query_strategies():
    """When the artist: query and the first plain-text page combined don't
    yield 10 matches, the client moves on to the second plain-text page."""
    from unittest.mock import MagicMock

    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000

    # artist: query — 3 reliable matches
    artist_page = {
        "tracks": {
            "items": [
                {"name": f"A hit {i}", "artists": [{"name": "Powerwolf"}], "uri": f"u:a-{i}"}
                for i in range(3)
            ] + [
                {"name": f"A junk {i}", "artists": [{"name": "Other"}], "uri": f"u:aj-{i}"}
                for i in range(7)
            ]
        }
    }
    # plain offset 0 — 5 new matches
    plain_0 = {
        "tracks": {
            "items": [
                {"name": f"P0 hit {i}", "artists": [{"name": "Powerwolf"}], "uri": f"u:p0-{i}"}
                for i in range(5)
            ] + [
                {"name": f"P0 junk {i}", "artists": [{"name": "Other"}], "uri": f"u:p0j-{i}"}
                for i in range(5)
            ]
        }
    }
    # plain offset 10 — 4 more matches (brings total to 12, capped at 10)
    plain_10 = {
        "tracks": {
            "items": [
                {"name": f"P1 hit {i}", "artists": [{"name": "Powerwolf"}], "uri": f"u:p1-{i}"}
                for i in range(4)
            ] + [
                {"name": f"P1 junk {i}", "artists": [{"name": "Other"}], "uri": f"u:p1j-{i}"}
                for i in range(6)
            ]
        }
    }

    responses = []
    for payload in [artist_page, plain_0, plain_10]:
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        resp.json.return_value = payload
        responses.append(resp)

    with patch(
        "wacken_playlist.services.spotify.requests.get",
        side_effect=responses,
    ) as mock_get:
        tracks = client.get_top_tracks("Powerwolf")

    assert mock_get.call_count == 3
    assert len(tracks) == 10
    # Verify query order: artist: first, then plain text with offset 0 and 10
    assert 'artist:' in mock_get.call_args_list[0].kwargs["params"]["q"]
    assert mock_get.call_args_list[1].kwargs["params"]["q"] == "Powerwolf"
    assert mock_get.call_args_list[1].kwargs["params"]["offset"] == 0
    assert mock_get.call_args_list[2].kwargs["params"]["offset"] == 10


def test_get_top_tracks_caps_at_six_queries():
    """Hard cap: artist: query + MAX_TOP_TRACKS_PAGES(5) plain-text pages = 6
    total queries, even if none of them filled the bucket."""
    from unittest.mock import MagicMock

    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000

    responses = []
    for i in range(7):  # 7 prepared; only 6 should be consumed
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        resp.json.return_value = {
            "tracks": {
                "items": [
                    {"name": f"hit-{i}", "artists": [{"name": "Sparseband"}], "uri": f"u:h-{i}"},
                ] + [
                    {"name": f"junk-{i}-{j}", "artists": [{"name": "Other"}], "uri": f"u:j-{i}-{j}"}
                    for j in range(9)
                ]
            }
        }
        responses.append(resp)

    with patch(
        "wacken_playlist.services.spotify.requests.get",
        side_effect=responses,
    ) as mock_get:
        tracks = client.get_top_tracks("Sparseband")

    assert mock_get.call_count == 6  # artist: + 5 plain pages, never a 7th
    assert len(tracks) == 6  # one match per query


def test_get_top_tracks_filters_out_tracks_by_other_artists():
    """Plain-text /search returns covers and unrelated tracks; we must
    drop anything whose primary artist isn't the one we asked for."""
    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000
    _mock_get({
        "tracks": {
            "items": [
                {"name": "Real", "artists": [{"name": "Powerwolf"}]},
                {"name": "Cover", "artists": [{"name": "Some Cover Band"}]},
                {"name": "Mixed", "artists": [
                    {"name": "Other"}, {"name": "Powerwolf"},
                ]},
                {"name": "Empty", "artists": []},
                {"name": "Case", "artists": [{"name": "POWERWOLF"}]},
            ]
        }
    })

    tracks = client.get_top_tracks("Powerwolf")
    names = [t["name"] for t in tracks]
    assert names == ["Real", "Case"]


def test_auth_failure_raises_spotify_auth_error():
    client = _make_client()
    import requests

    with patch(
        "wacken_playlist.services.spotify.requests.post",
        side_effect=requests.RequestException("boom"),
    ):
        with pytest.raises(SpotifyAuthError):
            client.get_client_credentials_token()


def test_create_playlist_without_refresh_token_raises_config_error():
    client = SpotifyClient(client_id="cid", client_secret="csecret")
    with pytest.raises(SpotifyConfigError):
        client.create_playlist("Test", ["spotify:track:1"])


def test_create_playlist_posts_to_me_and_adds_items_in_chunks():
    """Verifies the February-2026-compatible endpoints:
    POST /me/playlists for creation and POST /playlists/{id}/items for
    adding tracks (the previous /users/{user_id}/playlists and
    /playlists/{id}/tracks endpoints were removed by Spotify).
    """
    from unittest.mock import MagicMock

    client = SpotifyClient(
        client_id="cid",
        client_secret="csecret",
        redirect_uri="http://x/cb",
        app_refresh_token="rt",
    )

    def mock_post(url, headers=None, data=None, json=None, timeout=None):
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = lambda: None
        if url.endswith("/api/token"):
            response.json.return_value = {
                "access_token": "app-tok",
                "expires_in": 3600,
            }
        elif url.endswith("/me/playlists"):
            response.json.return_value = {
                "id": "pl-1",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/pl-1"},
            }
        else:
            response.json.return_value = {"snapshot_id": "snap"}
        return response

    uris = [f"spotify:track:{i}" for i in range(205)]

    with patch("wacken_playlist.services.spotify.requests.post", side_effect=mock_post) as post:
        url = client.create_playlist("Mix", uris, public=True)

    assert url == "https://open.spotify.com/playlist/pl-1"
    # 1 token refresh + 1 create + ceil(205/100)=3 chunked adds = 5 POSTs
    assert post.call_count == 5
    create_call = post.call_args_list[1]
    assert create_call.args[0].endswith("/me/playlists")
    assert create_call.kwargs["json"] == {"name": "Mix", "public": True}
    add_calls = post.call_args_list[2:]
    for call in add_calls:
        assert call.args[0].endswith("/playlists/pl-1/items")
    chunk_sizes = [len(call.kwargs["json"]["uris"]) for call in add_calls]
    assert chunk_sizes == [100, 100, 5]


def test_create_playlist_caches_app_access_token():
    from unittest.mock import MagicMock

    client = SpotifyClient(
        client_id="cid",
        client_secret="csecret",
        app_refresh_token="rt",
    )

    def mock_post(url, headers=None, data=None, json=None, timeout=None):
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = lambda: None
        if url.endswith("/api/token"):
            response.json.return_value = {"access_token": "tok", "expires_in": 3600}
        elif url.endswith("/me/playlists"):
            response.json.return_value = {
                "id": "pl",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/pl"},
            }
        else:
            response.json.return_value = {"snapshot_id": "s"}
        return response

    with patch("wacken_playlist.services.spotify.requests.post", side_effect=mock_post) as post:
        client.create_playlist("A", ["spotify:track:1"])
        client.create_playlist("B", ["spotify:track:2"])

    token_calls = [c for c in post.call_args_list if c.args[0].endswith("/api/token")]
    assert len(token_calls) == 1
