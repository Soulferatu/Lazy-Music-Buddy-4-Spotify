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


def test_preview_shows_selected_bands_and_track_count(client):
    response = client.post(
        "/preview",
        data={"playlist_name": "Holy Ground", "bands": ["Def Leppard", "Powerwolf"]},
    )

    assert response.status_code == 200
    assert b"Holy Ground" in response.data
    assert b"Def Leppard" in response.data
    assert b"Powerwolf" in response.data
    assert b"20 tracks" in response.data
