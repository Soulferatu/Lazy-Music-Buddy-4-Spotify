from flask import Flask

from .config import DevelopmentConfig
from .lineup import LineupRepository
from .services import PlaylistBuilder, SetlistFmClient, SpotifyClient


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.lineup = LineupRepository()
    app.spotify = SpotifyClient(
        client_id=app.config["SPOTIFY_CLIENT_ID"],
        client_secret=app.config["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=app.config["SPOTIFY_REDIRECT_URI"],
        app_refresh_token=app.config["SPOTIFY_APP_REFRESH_TOKEN"],
    )
    app.setlistfm = SetlistFmClient(api_key=app.config["SETLISTFM_API_KEY"])
    app.playlist_builder = PlaylistBuilder(app.spotify)

    from .routes import main

    app.register_blueprint(main)
    return app
