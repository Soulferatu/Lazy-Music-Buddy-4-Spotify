# Stage 1 Implementation

Purpose: record what was built during Stage 0 and Stage 1, which files own which responsibilities, and what is needed before Stage 2 begins. Source: codebase and [raw/product_decisions_stage0.md](../raw/product_decisions_stage0.md).

## Status

Complete. The app runs locally and passes the Stage 1 completion gate: a user can select Wacken 2026 bands, enter a playlist name, submit the form, and see a local preview without contacting Spotify.

## What Was Built

### Application Structure

| File or Folder | Purpose |
| --- | --- |
| `wacken_playlist/__init__.py` | Flask app factory (`create_app`). Registers the main blueprint. |
| `wacken_playlist/routes.py` | Main blueprint. Handles `GET /`, `POST /preview`, and `GET /health`. |
| `wacken_playlist/lineup.py` | Wacken 2026 band list and source URL references. |
| `wacken_playlist/templates/index.html` | Single-page Jinja2 template for band selection, playlist name input, and local preview. |
| `wacken_playlist/static/css/styles.css` | Dark festival theme styles. |
| `wacken_playlist/static/js/app.js` | Client-side language switching and checklist interaction. |
| `wacken_playlist/static/manifest.webmanifest` | PWA manifest stub (to be completed in Stage 4). |
| `wacken_playlist/static/service-worker.js` | Service worker stub (to be completed in Stage 4). |
| `wacken_playlist/static/icons/icon.svg` | Placeholder install icon (final icon deferred). |
| `tests/test_app.py` | Tests for route responses, preview validation, health endpoint, and lineup data. |
| `scripts/restart-dev.ps1` | PowerShell helper to cleanly restart the local dev server. |
| `.env.example` | Template for required environment variables (no secrets committed). |
| `requirements.txt` | Python dependencies. |
| `README.md` | Local setup and run instructions. |

### Routes

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/` | Renders the band checklist and playlist name input. |
| POST | `/preview` | Validates selection and name, returns local preview without Spotify. |
| GET | `/health` | Returns `{"status": "ok", "app": "wacken-playlist"}`. |

### Language Support

- Bilingual: English (`en`) and Brazilian Portuguese (`pt-BR`).
- Language is carried through the form as a hidden input and switched client-side without a reload.
- Server-side validation messages are translated using a `MESSAGES` dict in `routes.py`.

### Preview Logic

The preview at Stage 1 is local only. It calculates `track_count = len(selected_bands) * 10` and returns the band list and playlist name as confirmation. No Spotify calls are made.

### Lineup Data

`lineup.py` contains the manually curated Wacken 2026 band list and a list of source URLs for attribution. The source URLs are displayed in the UI to acknowledge data provenance.

## How To Run

```powershell
py -m flask --app wacken_playlist:create_app --debug run --host 127.0.0.1 --port 1337
```

Or using the helper script:

```powershell
.\scripts\restart-dev.ps1
```

## Stage 2 Prerequisites

Before Stage 2 can begin:

- Spotify Developer app credentials must be created (Client ID and Client Secret).
- Credentials must be added to `.env` (not committed).
- The Spotify Client Credentials flow (no user login) is enough for artist search and top-track lookup at Stage 2.
- App-owned OAuth (refresh token) is added at Stage 3, not Stage 2.

See [wiki/spotify_integration.md](spotify_integration.md) for the full Spotify setup responsibilities and risks.

## Related Pages

- [Project Overview](project_overview.md)
- [Development Stages](development_stages.md)
- [Spotify Integration](spotify_integration.md)
- [PWA Requirements](pwa_requirements.md)
