# Wacken Playlist Buddy

Wacken Playlist Buddy is a Flask-based Progressive Web App for creating Spotify playlists from Wacken Open Air band selections.

The first implementation target is app-owned playlist creation: visitors choose bands and receive a Spotify playlist link created by a dedicated app Spotify account. A later optional mode will let users log into Spotify and create playlists in their own accounts.

## Current Status

Stage 0 is the active baseline:

- Flask app factory.
- Basic home page.
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
flask --app wacken_playlist:create_app run
```

Open `http://127.0.0.1:5000`.

## Useful Commands

Run tests:

```powershell
python -m pytest
```

Check the health endpoint after starting the server:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

## Environment Variables

See `.env.example` for expected variables. Real credentials belong in `.env` or production secrets and must not be committed.

Spotify credentials will be added when the Spotify lookup and app-owned playlist stages begin.
