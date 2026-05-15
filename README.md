# Wacken Playlist Buddy

Wacken Playlist Buddy is a Flask-based Progressive Web App for creating Spotify playlists from Wacken Open Air band selections.

The first implementation target is app-owned playlist creation: visitors choose bands and receive a Spotify playlist link created by a dedicated app Spotify account. A later optional mode will let users log into Spotify and create playlists in their own accounts.

## Current Status

Stage 1 is the active baseline. The architecture migration (phases 1–6) is complete; see [wiki/development_stages.md](wiki/development_stages.md) for the roadmap and [ARCH_MIGRATION_PLAN.md](ARCH_MIGRATION_PLAN.md) for what each phase delivered.

Working today:

- Flask app factory with typed config (`Development`, `Testing`, `Production`).
- Wacken 2026 starter lineup checklist (data lives in `wacken_playlist/data/lineups/wacken_2026.json`).
- Playlist name input.
- Local playlist preview without Spotify calls (`PlaylistBuilder.build_preview`).
- Health endpoint at `/health`.
- PWA manifest + service worker (`/service-worker.js`) with single-source versioning via `wacken_playlist/version.py`.
- Bilingual UI (EN / pt-BR) sourced from `wacken_playlist/i18n/*.json`.
- CSRF protection on all POST forms.
- Environment variable template.

## Local Setup

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
.\scripts\restart-dev.ps1            # or: .\scripts\restart-dev.ps1 -Port 1338
```

### macOS / Linux (bash or zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
chmod +x scripts/dev.sh              # first time only
./scripts/dev.sh                     # or: ./scripts/dev.sh 1338
```

Open `http://127.0.0.1:1337`.

### Manual run (any platform)

```bash
python -m flask --app wacken_playlist:create_app --debug run --host 127.0.0.1 --port 1337
```

## Useful Commands

Run tests:

```bash
python -m pytest                     # full suite
python -m pytest tests/unit          # unit only — no Flask app, no I/O
python -m pytest tests/integration   # integration — uses test_client
```

Check the health endpoint after starting the server:

```bash
curl http://127.0.0.1:1337/health
# PowerShell: Invoke-RestMethod http://127.0.0.1:1337/health
```

## Production

```bash
gunicorn wsgi:application
```

`ProductionConfig.validate()` fails fast if `SECRET_KEY` is not present in the environment.

## Environment Variables

See `.env.example` for expected variables. Real credentials belong in `.env` or production secrets and must not be committed.

Spotify credentials will be added when the Spotify lookup and app-owned playlist stages begin.
