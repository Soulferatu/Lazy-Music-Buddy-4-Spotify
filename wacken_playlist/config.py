import logging
import os

logger = logging.getLogger(__name__)


class Config:
    """Base configuration class. All values read from environment."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or None
    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "")
    SPOTIFY_APP_REFRESH_TOKEN = os.environ.get("SPOTIFY_APP_REFRESH_TOKEN", "")
    SETLISTFM_API_KEY = os.environ.get("SETLISTFM_API_KEY", "")
    WTF_CSRF_ENABLED = True
    # Phase 3 of the library refactor: when True, LineupRepository reads
    # wacken_YYYY.thin.json (pointer list) and joins with LibraryRepository.
    # When False (current default), it reads the fat wacken_YYYY.json directly.
    # Flag will be flipped on in Phase 4.
    USE_THIN_LINEUPS = False


class DevelopmentConfig(Config):
    """Development configuration. Provides safe fallback for SECRET_KEY."""
    DEBUG = True

    def __init__(self):
        if not Config.SECRET_KEY:
            logger.warning(
                "SECRET_KEY is not set; using insecure development fallback. "
                "Set SECRET_KEY in your environment before any non-local use."
            )

    SECRET_KEY = Config.SECRET_KEY or "dev-only-insecure"


class TestingConfig(Config):
    """Testing configuration. All values are fixed for reproducible tests."""
    TESTING = True
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration. Fails loudly if SECRET_KEY is absent."""

    @classmethod
    def validate(cls):
        if not os.environ.get("SECRET_KEY"):
            raise RuntimeError(
                "SECRET_KEY must be set in the environment before starting "
                "the app in production."
            )
