# Wacken Playlist Buddy

Wacken Playlist Buddy is a Flask-based Progressive Web App for creating Spotify playlists from Wacken Open Air band selections.

The first implementation target is app-owned playlist creation: visitors choose bands and receive a Spotify playlist link created by a dedicated app Spotify account. A later optional mode will let users log into Spotify and create playlists in their own accounts.

## Current Status

Stage 1 is the active baseline:

- Flask app factory.
- Wacken 2026 starter lineup checklist.
- Playlist name input.
- Local playlist preview without Spotify calls.
- Health endpoint.
- PWA manifest and service worker placeholders.
- Environment variable template.

## Local Setup

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Run the app:

```powershell
py -m flask --app wacken_playlist:create_app --debug run --host 127.0.0.1 --port 1337
```

Open `http://127.0.0.1:1337`.

Restart the dev server cleanly:

```powershell
.\scripts\restart-dev.ps1
```

To use another port:

```powershell
.\scripts\restart-dev.ps1 -Port 1338
```

## Useful Commands

Run tests:

```powershell
python -m pytest
```

Check the health endpoint after starting the server:

```powershell
Invoke-RestMethod http://127.0.0.1:1337/health
```

## Environment Variables

See `.env.example` for expected variables. Real credentials belong in `.env` or production secrets and must not be committed.

Spotify credentials will be added when the Spotify lookup and app-owned playlist stages begin.
