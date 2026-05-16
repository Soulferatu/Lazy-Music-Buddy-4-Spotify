# Deployment Guide — Play[my W:O:A]list

This guide covers deploying the Flask app to Vercel for public access.

## Prerequisites

- Vercel account (free tier is sufficient)
- Production domain name (optional; Vercel provides a free `*.vercel.app` domain)
- Spotify app credentials from the [Developer Dashboard](https://developer.spotify.com/dashboard)
- Spotify app account refresh token (set up in [Stage 3](wiki/stage3_playlist_creation.md))

## Vercel Deployment Steps

### 1. Connect Repository to Vercel

1. Visit [vercel.com](https://vercel.com) and sign in with GitHub/GitLab/Bitbucket.
2. Click **"Add New..."** → **"Project"**.
3. Select this repository.
4. Vercel auto-detects it as a Python app and uses `vercel.json` configuration.

### 2. Configure Environment Variables

In the Vercel dashboard, go to **Project Settings** → **Environment Variables** and add:

| Variable | Value | Source |
|---|---|---|
| `SECRET_KEY` | 64-char random string | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SPOTIFY_CLIENT_ID` | Your Spotify app ID | [Spotify Dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_CLIENT_SECRET` | Your Spotify app secret | [Spotify Dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_APP_REFRESH_TOKEN` | Refresh token from Stage 3 | See [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md) |

### 3. Update Spotify Redirect URL

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) → Your App → **Edit Settings**.
2. Under **Redirect URIs**, add:
   ```
   https://yourdomain.vercel.app/auth/spotify/callback
   ```
   (Replace `yourdomain` with your Vercel project name, or use a custom domain if configured.)

### 4. Deploy

Push the `stage-5-deployment` branch to the repository. Vercel automatically deploys on push.

```bash
git push origin stage-5-deployment
```

Once deployed, visit your app's URL (shown in Vercel dashboard) and test:
- **Full flow:** select bands → preview → create playlist → open in Spotify
- **PWA install:** on mobile/desktop, install from the address bar
- **Mobile responsiveness:** test on a phone or DevTools
- **Stale assets:** do a hard refresh (Ctrl+Shift+R) to clear old service worker cache

### 5. Optional: Custom Domain

1. In Vercel dashboard, go to **Project Settings** → **Domains**.
2. Add your custom domain and follow DNS setup instructions.
3. Update Spotify redirect URL to match: `https://yourdomain.com/auth/spotify/callback`.

## Troubleshooting

### "Redirect URI mismatch" Error

The Spotify redirect URL in the Vercel environment must **exactly match** the one registered in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

**Local development:** `http://127.0.0.1:1337/auth/spotify/callback`  
**Production:** `https://yourdomain.vercel.app/auth/spotify/callback`

Both must be registered in the dashboard.

### Service Worker Cache Issues

Old versions of static assets may remain cached in browsers. To force a cache bust, increment `version.py` and commit.

### Cold Starts

Vercel may spin down idle apps. The first request after inactivity may take 5–10 seconds. This is normal and improves with traffic.

## Next Steps

- **Stage 6:** Add setlist.fm as an alternative song source.
- **Stage 7:** Import historical Wacken lineups.
- **Stage 8:** Cross-year shuffle playlists.
- **Optional:** Personal Spotify login (users create playlists in their own account).

See [PHASES.md](PHASES.md) for the full roadmap.
