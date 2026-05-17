"""Single source of truth for the app version string.

Bumping APP_VERSION:
- Invalidates the service worker cache (CACHE_NAME embeds it).
- Busts static-file query strings in templates (`?v={{ app_version }}`).
- Updates the manifest version exposed via window.__appVersion.
"""

APP_VERSION = "0.5.4"