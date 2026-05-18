import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .config import DevelopmentConfig, ProductionConfig
from .library import LibraryRepository
from .lineup import LineupRepository
from .services import PlaylistBuilder, SetlistFmClient, SpotifyClient
from .version import APP_VERSION

csrf = CSRFProtect()


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    is_production = isinstance(config_class, type) and issubclass(config_class, ProductionConfig)
    if is_production:
        config_class.validate()
    app.config.from_object(config_class)
    if is_production:
        # Class attributes are frozen at import time; refresh from env at startup.
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    csrf.init_app(app)

    app.lineup = LineupRepository()
    app.library = LibraryRepository()
    app.spotify = SpotifyClient(
        client_id=app.config["SPOTIFY_CLIENT_ID"],
        client_secret=app.config["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=app.config["SPOTIFY_REDIRECT_URI"],
        app_refresh_token=app.config["SPOTIFY_APP_REFRESH_TOKEN"],
    )
    app.setlistfm = SetlistFmClient(api_key=app.config["SETLISTFM_API_KEY"])
    app.playlist_builder = PlaylistBuilder(app.spotify)

    @app.context_processor
    def inject_app_version():
        return {"app_version": APP_VERSION}

    from .routes import main

    app.register_blueprint(main)
    return app
