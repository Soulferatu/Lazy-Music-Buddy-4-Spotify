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
    # Pull a real pre-resolved track name through to confirm the embedded
    # library data is being surfaced (not a Spotify mock).
    assert b"Hysteria" in response.data


def test_preview_shows_limited_presence_notice_for_wacken_local(client):
    """Selecting a wacken_local_or_tribute band shows the new ember
    notice (the legacy 'Could not find on Spotify' warning was retired
    for these bands so they don't get double-flagged)."""
    response = client.post(
        "/preview",
        data={"playlist_name": "Test", "bands": ["Powerwolf", "Wacken Firefighters"]},
    )

    assert response.status_code == 200
    assert b"notice-info" in response.data
    assert b"Limited Spotify presence" in response.data
    assert b"Wacken Firefighters" in response.data
    # Reason-specific copy fires for the wacken_local_or_tribute reason.
    assert b"Wacken-local or tribute acts" in response.data


def test_preview_shows_limited_presence_notice_for_thin_catalog(client):
    """Heavysaurus has a real Spotify presence but only 2 unique tracks
    — the thin_catalog explanation should fire instead of the local-act
    copy."""
    response = client.post(
        "/preview",
        data={"playlist_name": "Test", "bands": ["Powerwolf", "Heavysaurus"]},
    )

    assert response.status_code == 200
    assert b"notice-info" in response.data
    assert b"Heavysaurus" in response.data
    assert b"very small Spotify catalog" in response.data


def test_preview_zero_track_band_does_not_trigger_legacy_warning(client):
    """A permanently-unresolved band that's also flagged is filtered out
    of the legacy `unmatched` list so the yellow warning stays quiet for
    these bands."""
    response = client.post(
        "/preview",
        data={"playlist_name": "Test", "bands": ["Wacken Firefighters"]},
    )

    assert response.status_code == 200
    # Notice-warning class wraps the legacy warning; if it appears at all
    # in the rendered preview, it must NOT be about Wacken Firefighters.
    assert b"notice-info" in response.data  # new notice fired
    # The legacy warning's headline shouldn't surface for this band.
    # (We can't assert the class is absent globally because i18n bundle
    #  embeds copy elsewhere — instead check the warning-list contents.)
    import re
    html = response.data.decode()
    legacy = re.search(
        r'<div class="notice notice-warning".*?</div>', html, flags=re.DOTALL
    )
    if legacy:
        assert "Wacken Firefighters" not in legacy.group(0)


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


def test_create_spotify_api_error_surfaces_message(client, mock_spotify):
    """Post-v0.5.4 the only runtime Spotify call is create_playlist via
    /create. /preview no longer talks to Spotify, so error surfacing
    moved entirely to the create path."""
    mock_spotify.create_playlist.side_effect = SpotifyAPIError("boom")

    response = client.post(
        "/create",
        data={"playlist_name": "Test", "bands": ["Def Leppard"]},
    )

    assert response.status_code == 200
    # The i18n copy was renamed during the rate-limit hotfix work; the
    # current key surfaces the rate-limit guidance.
    assert b"Spotify is temporarily unavailable" in response.data


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
    """If the only band selected has zero pre-resolved tracks (e.g. a
    wacken_local act), /create raises NoMatchedTracksError and renders
    the error copy without calling Spotify."""
    response = client.post(
        "/create",
        data={"playlist_name": "Mix", "bands": ["Wacken Firefighters"]},
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
