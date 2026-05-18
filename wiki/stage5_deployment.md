# Stage 5 — Deployment (Vercel)

**Status:** ✅ Done (2026-05-16). App is live on Vercel with full PWA support.

This page captures **what shipped** and **how to operate it**. The user-facing operator walkthrough lives in [DEPLOYMENT.md](../DEPLOYMENT.md); this page documents the as-built configuration and the decisions behind it.

## What Stage 5 Delivered

- **Hosting provider:** Vercel (free tier; auto-deploys on push).
- **Entry point:** `wsgi.py` exposes the Flask app factory; Vercel's Python runtime imports it.
- **Build config:** [vercel.json](../vercel.json) — Python build target, routing rules, environment-variable wiring.
- **Ignore file:** `.vercelignore` excludes `tests/`, docs, `.git/`, `__pycache__/`, and resolver build artifacts.
- **HTTPS:** automatic via Vercel; the Spotify redirect URL on production must be `https://`.
- **Production config:** `wacken_playlist/config.py::ProductionConfig` validates required env vars on app boot; secure cookies + CSRF on by default; `DEBUG=False`, `TESTING=False`.
- **Security headers:** CSP and X-Frame-Options applied to all responses (see `wacken_playlist/__init__.py`).
- **PWA on production origin:** verified installable from the live URL on both mobile (iOS + Android) and desktop browsers.

## Required Environment Variables (Vercel Project Settings)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session + CSRF signing. Generate with `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `SPOTIFY_CLIENT_ID` | Spotify Developer app ID. |
| `SPOTIFY_CLIENT_SECRET` | Spotify Developer app secret. |
| `SPOTIFY_APP_REFRESH_TOKEN` | Refresh token captured in Stage 3 via `/auth/spotify/login`. |

There is **no** `SPOTIFY_REDIRECT_URI` env var in production — the redirect URL is computed from the request host, but it **must be registered in the Spotify dashboard verbatim** (both the local `http://127.0.0.1:1337/auth/spotify/callback` and the production `https://<domain>/auth/spotify/callback`).

## Critical Configuration Points

- **Redirect URL must match exactly** — Spotify rejects mismatches with no useful error.
- **Cache busts via `version.py`** — Vercel does not invalidate the service worker for you. Bump `APP_VERSION` whenever shipping static-asset, manifest, or service-worker changes.
- **Cold starts** — Vercel spins down idle apps; first request after inactivity takes 5–10 s. This is expected.
- **No Docker** — Vercel's Python runtime handles deps via `requirements.txt`; no container build needed.
- **Resolver artifacts are not deployed** — `resolution_output.txt` and `_bandcounts.txt` are excluded by `.vercelignore`. Only the resolved `wacken_2026.json` ships.

## Runtime Spotify Posture (Post-v0.5.4)

Stage 5 is paired with the offline pre-resolution system (see [band_track_resolution.md](band_track_resolution.md)). The combined effect:

- **Per-user-session Spotify calls:** 2–3 (create playlist + 1–2 add-items chunks). No search.
- **Rate-limit exposure:** essentially zero at the user-session level. The only remaining Spotify-side risk is on the offline resolver, which the developer runs locally.
- **Shadow-ban protection:** because users never hit `/search`, the 17-hour shadow ban that motivated v0.5.4 cannot recur from production traffic.

## Smoke-Test Checklist (run after every prod deploy)

1. Open the live URL in a fresh incognito window.
2. Confirm the Wacken 2026 lineup loads (169 bands).
3. Toggle EN ↔ pt-BR — translations swap.
4. Select 3 bands → click Preview → tracks appear.
5. Click Create → playlist URL returned → open it in Spotify and confirm tracks added.
6. Install as PWA on mobile (Add to Home Screen on iOS / Install on Android Chrome) and on desktop Chrome.
7. Hard refresh (Ctrl+Shift+R) to confirm the latest `version.py` busted the SW cache.

## Known Limitations

- **No personal Spotify login.** All playlists are created under the app-owned account; the share URL is the deliverable. Personal login is an [Optional Stage](../PHASES.md#optional-stage--personal-spotify-login).
- **Duplicate playlist names allowed.** Each Create click produces a fresh playlist with a new ID; there is no de-duplication on the app account side.
- **Cold-start latency.** Acceptable for current usage; revisit if/when traffic warrants Vercel Pro.

## References

- [DEPLOYMENT.md](../DEPLOYMENT.md) — operator walkthrough.
- [vercel.json](../vercel.json) — build/route config.
- [wiki/phase5_security_platform.md](phase5_security_platform.md) — CSRF, SECRET_KEY enforcement, `wsgi.py`.
- [wiki/band_track_resolution.md](band_track_resolution.md) — why per-session search calls are zero.
- [PHASES.md](../PHASES.md#stage-5--deployment--public-release-) — roadmap entry.
