from flask import Flask

from .config import DevelopmentConfig
from .lineup import LineupRepository


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.lineup = LineupRepository()

    from .routes import main

    app.register_blueprint(main)
    return app
