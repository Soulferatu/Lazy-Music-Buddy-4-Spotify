"""Production WSGI entry point.

Run with: gunicorn wsgi:application
"""
from wacken_playlist import create_app
from wacken_playlist.config import ProductionConfig

application = create_app(ProductionConfig)
