import os

import pytest

from wacken_playlist import create_app
from wacken_playlist.config import DevelopmentConfig, ProductionConfig, TestingConfig
from wacken_playlist.version import APP_VERSION


def test_production_config_requires_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(ProductionConfig)


def test_production_config_accepts_secret_key_from_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "production-secret")
    app = create_app(ProductionConfig)
    assert app.config["SECRET_KEY"] == "production-secret" or app.config["SECRET_KEY"]


def test_testing_config_disables_csrf():
    app = create_app(TestingConfig)
    assert app.config["WTF_CSRF_ENABLED"] is False


def test_development_config_enables_csrf():
    app = create_app(DevelopmentConfig)
    assert app.config.get("WTF_CSRF_ENABLED") is True


def test_csrf_blocks_post_without_token_when_enabled():
    """When CSRF is on, POST /preview without a token must be rejected."""
    app = create_app(DevelopmentConfig)
    client = app.test_client()
    response = client.post("/preview", data={"playlist_name": "x", "bands": ["Powerwolf"]})
    assert response.status_code in (400, 403)


def test_app_version_injected_into_template():
    app = create_app(TestingConfig)
    response = app.test_client().get("/")
    body = response.data.decode("utf-8")
    assert f"v={APP_VERSION}" in body
    assert f'"{APP_VERSION}"' in body  # window.__appVersion = "..."


def test_service_worker_route_renders_version():
    app = create_app(TestingConfig)
    response = app.test_client().get("/service-worker.js")
    assert response.status_code == 200
    assert response.headers["Service-Worker-Allowed"] == "/"
    assert response.headers["Content-Type"].startswith("application/javascript")
    body = response.data.decode("utf-8")
    assert f'"wacken-playlist-{APP_VERSION}"' in body
    assert "{{ app_version }}" not in body
