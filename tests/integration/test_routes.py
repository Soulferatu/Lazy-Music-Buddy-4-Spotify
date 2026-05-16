from wacken_playlist.services import (
    SpotifyAPIError,
    SpotifyAuthError,
    SpotifyConfigError,
)


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "app": "wacken-playlist"}


def test_home_page_shows_stage_one_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Play[my W:O:A]list" in response.data
    assert b"language-switch" in response.data
    assert b"Cinzel+Decorative" in response.data
    assert b"Wacken 2026 selection" in response.data
    assert b"Def Leppard" in response.data


def test_preview_requires_playlist_name_and_band_selection(client):
    response = client.post("/preview", data={"playlist_name": "", "bands": []})

    assert response.status_code == 200
    assert b"Name the playlist" in response.data
    assert b"Select at least one" in response.data


def test_preview_supports_brazilian_portuguese_validation(client):
    response = client.post(
        "/preview",
        data={"playlist_name": "", "bands": [], "language": "pt-BR"},
    )

    assert response.status_code == 200
    assert "Dê um nome".encode() in response.data
    assert "Selecione pelo menos uma banda".encode() in response.data


def test_preview_shows_matched_tracks_and_total_count(client):
    response = client.post(
        "/preview",
        data={"playlist_name": "Holy Ground", "bands": ["Def Leppard", "Powerwolf"]},
    )

    assert response.status_code == 200
    assert b"Holy Ground" in response.data
    assert b"Def Leppard" in response.data
    assert b"Powerwolf" in response.data
    assert b"20 tracks matched" in response.data
    assert b"Track 1" in response.data


def test_preview_shows_unmatched_warning(client, mock_spotify):
    mock_spotify.search_artist.side_effect = lambda name: (
        {"id": "id-Powerwolf", "name": "Powerwolf"} if name == "Powerwolf" else None
    )

    response = client.post(
        "/preview",
        data={"playlist_name": "Test", "bands": ["Powerwolf", "Def Leppard"]},
    )

    assert response.status_code == 200
    assert b"notice-warning" in response.data
    assert b"Could not find on Spotify" in response.data
    assert b"Def Leppard" in response.data


def test_preview_all_unmatched_renders_zero_tracks(client, mock_spotify):
    mock_spotify.search_artist.side_effect = lambda name: None

    response = client.post(
        "/preview",
        data={"playlist_name": "Test", "bands": ["Def Leppard", "Powerwolf"]},
    )

    assert response.status_code == 200
    assert b"0 tracks matched" in response.data
    assert b"Def Leppard" in response.data


def test_preview_spotify_config_error(client, mock_spotify):
    mock_spotify.search_artist.side_effect = SpotifyConfigError("missing")

    response = client.post(
        "/preview",
        data={"playlist_name": "Test", "bands": ["Def Leppard"]},
    )

    assert response.status_code == 200
    assert b"Spotify credentials are not configured" in response.data


def test_preview_spotify_auth_error(client, mock_spotify):
    mock_spotify.search_artist.side_effect = SpotifyAuthError("nope")

    response = client.post(
        "/preview",
        data={"playlist_name": "Test", "bands": ["Def Leppard"]},
    )

    assert response.status_code == 200
    assert b"Could not authenticate with Spotify" in response.data


def test_preview_spotify_api_error(client, mock_spotify):
    mock_spotify.search_artist.side_effect = SpotifyAPIError("boom")

    response = client.post(
        "/preview",
        data={"playlist_name": "Test", "bands": ["Def Leppard"]},
    )

    assert response.status_code == 200
    assert b"Spotify returned an unexpected error" in response.data


def test_preview_renders_create_form_with_band_values(client):
    """Regression: the hidden `bands` inputs on the Create form must carry
    the actual band names — not empty strings — so /create receives them.
    """
    import re

    response = client.post(
        "/preview",
        data={"playlist_name": "Holy Ground", "bands": ["Def Leppard", "Powerwolf"]},
    )

    assert response.status_code == 200
    html = response.data.decode()
    # Find the create-form section and pull every hidden bands input from it.
    form_match = re.search(
        r'<form class="create-form".*?</form>', html, flags=re.DOTALL
    )
    assert form_match, "create-form not found in preview response"
    band_values = re.findall(
        r'name="bands" value="([^"]*)"', form_match.group(0)
    )
    assert band_values == ["Def Leppard", "Powerwolf"]


def test_create_success_renders_result_with_spotify_link(client, mock_spotify):
    mock_spotify.create_playlist.return_value = "https://open.spotify.com/playlist/abc"

    response = client.post(
        "/create",
        data={"playlist_name": "Holy Ground", "bands": ["Def Leppard", "Powerwolf"]},
    )

    assert response.status_code == 200
    assert b"Your playlist is live" in response.data
    assert b"https://open.spotify.com/playlist/abc" in response.data
    assert b"20 tracks were added" in response.data
    mock_spotify.create_playlist.assert_called_once()
    args, kwargs = mock_spotify.create_playlist.call_args
    assert args[0] == "Holy Ground"
    assert len(args[1]) == 20
    assert kwargs == {"public": True}


def test_create_reports_skipped_bands(client, mock_spotify):
    mock_spotify.search_artist.side_effect = lambda name: (
        {"id": "id-Powerwolf", "name": "Powerwolf"} if name == "Powerwolf" else None
    )
    mock_spotify.create_playlist.return_value = "https://open.spotify.com/playlist/abc"

    response = client.post(
        "/create",
        data={"playlist_name": "Mix", "bands": ["Powerwolf", "Def Leppard"]},
    )

    assert response.status_code == 200
    assert b"Some bands could not be matched" in response.data
    assert b"Def Leppard" in response.data


def test_create_no_matches_shows_error(client, mock_spotify):
    mock_spotify.search_artist.side_effect = lambda name: None

    response = client.post(
        "/create",
        data={"playlist_name": "Mix", "bands": ["Def Leppard", "Powerwolf"]},
    )

    assert response.status_code == 200
    assert b"None of the selected bands matched" in response.data
    mock_spotify.create_playlist.assert_not_called()


def test_create_requires_playlist_name_and_bands(client):
    response = client.post("/create", data={"playlist_name": "", "bands": []})

    assert response.status_code == 200
    assert b"Name the playlist" in response.data
    assert b"Select at least one" in response.data


def test_create_spotify_auth_error_surfaces_message(client, mock_spotify):
    mock_spotify.create_playlist.side_effect = SpotifyAuthError("nope")

    response = client.post(
        "/create",
        data={"playlist_name": "Test", "bands": ["Def Leppard"]},
    )

    assert response.status_code == 200
    assert b"Could not authenticate with Spotify" in response.data


def test_create_refresh_token_missing_surfaces_specific_message(client, mock_spotify):
    mock_spotify.create_playlist.side_effect = SpotifyConfigError(
        "SPOTIFY_APP_REFRESH_TOKEN is not set."
    )

    response = client.post(
        "/create",
        data={"playlist_name": "Test", "bands": ["Def Leppard"]},
    )

    assert response.status_code == 200
    assert b"App-owned Spotify account is not authorized yet" in response.data
