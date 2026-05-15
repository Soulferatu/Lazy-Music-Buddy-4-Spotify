import os


class Config:
    """Base configuration class. All values read from environment."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or None
    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "")
    SPOTIFY_APP_REFRESH_TOKEN = os.environ.get("SPOTIFY_APP_REFRESH_TOKEN", "")
    SETLISTFM_API_KEY = os.environ.get("SETLISTFM_API_KEY", "")


class DevelopmentConfig(Config):
    """Development configuration. Provides safe fallback for SECRET_KEY."""
    DEBUG = True
    SECRET_KEY = Config.SECRET_KEY or "dev-only-insecure"


class TestingConfig(Config):
    """Testing configuration. All values are fixed for reproducible tests."""
    TESTING = True
    SECRET_KEY = "test-secret"


class ProductionConfig(Config):
    """Production configuration. Requires SECRET_KEY from environment."""
    pass
