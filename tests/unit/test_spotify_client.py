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


def test_get_top_tracks_paginates_when_first_page_has_too_few_matches():
    """When page 0 doesn't yield 10 matches (because some entries are
    covers or unrelated), the client should fetch page 1 to fill in."""
    from unittest.mock import MagicMock

    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000

    page_0 = {
        "tracks": {
            "items": [
                {"name": "P0 cover", "artists": [{"name": "Cover Band"}], "uri": "u:c0"},
            ] + [
                {"name": f"P0 hit {i}", "artists": [{"name": "Powerwolf"}], "uri": f"u:0-{i}"}
                for i in range(9)
            ]
        }
    }
    page_1 = {
        "tracks": {
            "items": [
                {"name": "P1 hit", "artists": [{"name": "Powerwolf"}], "uri": "u:1-0"},
                {"name": "P1 cover", "artists": [{"name": "Cover Band"}], "uri": "u:c1"},
            ] + [
                {"name": f"P1 filler {i}", "artists": [{"name": "Other"}], "uri": f"u:1-{i+1}"}
                for i in range(8)
            ]
        }
    }

    responses = [MagicMock(), MagicMock()]
    for resp, payload in zip(responses, [page_0, page_1]):
        resp.raise_for_status = lambda: None
        resp.json.return_value = payload

    with patch(
        "wacken_playlist.services.spotify.requests.get",
        side_effect=responses,
    ) as mock_get:
        tracks = client.get_top_tracks("Powerwolf")

    assert mock_get.call_count == 2
    assert len(tracks) == 10
    names = [t["name"] for t in tracks]
    assert names[:9] == [f"P0 hit {i}" for i in range(9)]
    assert names[9] == "P1 hit"
    # Confirm offsets were 0 then 10.
    first_offset = mock_get.call_args_list[0].kwargs["params"]["offset"]
    second_offset = mock_get.call_args_list[1].kwargs["params"]["offset"]
    assert (first_offset, second_offset) == (0, 10)


def test_get_top_tracks_caps_at_two_pages():
    """Hard cap at MAX_TOP_TRACKS_PAGES=2 even if neither page filled
    the bucket — we stop instead of looping indefinitely."""
    from unittest.mock import MagicMock

    client = _make_client()
    client._token = "t"
    client._token_expires_at = time.time() + 1000

    page = {
        "tracks": {
            "items": [
                {"name": "ours", "artists": [{"name": "Sparseband"}], "uri": "u:a"},
            ] + [
                {"name": f"junk {i}", "artists": [{"name": "Other"}], "uri": f"u:j-{i}"}
                for i in range(9)
            ]
        }
    }

    responses = []
    for _ in range(3):
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        # Each page must have a fresh items list (we de-dupe by uri).
        resp.json.return_value = {
            "tracks": {
                "items": [
                    {"name": f"ours-{len(responses)}", "artists": [{"name": "Sparseband"}], "uri": f"u:a-{len(responses)}"},
                ] + [
                    {"name": f"junk-{len(responses)}-{i}", "artists": [{"name": "Other"}], "uri": f"u:j-{len(responses)}-{i}"}
                    for i in range(9)
                ]
            }
        }
        responses.append(resp)

    with patch(
        "wacken_playlist.services.spotify.requests.get",
        side_effect=responses,
    ) as mock_get:
        tracks = client.get_top_tracks("Sparseband")

    assert mock_get.call_count == 2  # capped — would otherwise hit 3
    assert len(tracks) == 2  # one match per page, two pages


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
