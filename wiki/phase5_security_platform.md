# Phase 5 — Security and Platform Hardening

**Status:** Implemented
**Related:** [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md)

## Overview

Phase 5 closes the security gaps that would matter once Stage 3 (real Spotify writes) and Stage 5 (user OAuth) land, and centralizes the version string the PWA caches against.

## What Changed

### 5A — CSRF protection

- `Flask-WTF>=1.2` added to `requirements.txt`.
- `CSRFProtect` initialized in `create_app()`.
- `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` added to the preview form.
- `TestingConfig` sets `WTF_CSRF_ENABLED = False` so integration tests don't need to fetch tokens.
- A unit test asserts that `DevelopmentConfig` blocks a tokenless POST.

GET-only routes (`/health`, `/service-worker.js`, `/`) are inherently CSRF-safe and need no exemption.

### 5B — SECRET_KEY enforcement

`ProductionConfig.validate()` raises `RuntimeError` if `SECRET_KEY` is missing from the environment. `create_app()` calls it before instantiating Flask, and afterwards re-reads `SECRET_KEY` from `os.environ` into `app.config` (Config class attributes are frozen at import time).

`DevelopmentConfig` retains the `dev-only-insecure` fallback but logs a warning when `SECRET_KEY` is absent so the gap is never silent.

### 5C — `wsgi.py`

Top-level `wsgi.py` exposes `application = create_app(ProductionConfig)` for Gunicorn / uWSGI:

```bash
gunicorn wsgi:application
```

Because `ProductionConfig.validate()` runs at app creation, missing secrets fail fast at process startup instead of mid-request.

### 5D — Single-source app version

| What | Where |
|---|---|
| Source string | `wacken_playlist/version.py` → `APP_VERSION` |
| Template injection | `create_app()` context processor → `app_version` |
| Static asset busting | `url_for('static', ..., v=app_version)` in `index.html` |
| Client-side hook | `window.__appVersion = "<version>"` script tag |
| Service worker cache key | `CACHE_NAME = "wacken-playlist-<version>"` |

The service worker was moved from `static/` to `templates/` and is now served by the Flask route `GET /service-worker.js` with `Service-Worker-Allowed: /` — giving it **root scope** (previously confined to `/static/`). `app.js` registers it at `/service-worker.js` with `{ scope: "/" }`.

Bumping `APP_VERSION` now consistently:
1. Changes the SW cache name (old caches purged on next activate).
2. Busts every static asset query string.
3. Updates `window.__appVersion` for any client code that wants to react.

## Tests

New: `tests/unit/test_security.py`

- `ProductionConfig` raises without `SECRET_KEY`, accepts it from env.
- `TestingConfig` disables CSRF; `DevelopmentConfig` keeps it on.
- Tokenless POST to `/preview` is rejected under CSRF.
- `APP_VERSION` appears in rendered HTML and as `window.__appVersion`.
- `/service-worker.js` returns the templated body with the correct MIME type and `Service-Worker-Allowed` header — and `{{ app_version }}` is fully substituted.

Integration tests in `tests/test_app.py` were updated to instantiate `create_app(TestingConfig)` instead of the default so they don't fail CSRF.

Full suite: **29/29 passing.**

## What's Next

- **Phase 6** — Test architecture: `conftest.py` with shared fixtures, formal `unit/` vs `integration/` split, cross-platform `dev.sh` for macOS/Linux contributors.
- Stage 3 (playlist creation) and Stage 5 (user OAuth) prerequisites from this phase are now satisfied.
