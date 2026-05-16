# Wiki Ingest Log

Track every ingest operation here. An ingest operation is any time source material is added to `raw/`, summarized into `wiki/`, or used to update `index.md`.

## Log Format

| Date | Operation | Source | Output | Notes |
| --- | --- | --- | --- | --- |
| 2026-05-14 | Created wiki scaffold | [Start.MD](Start.MD) | [index.md](index.md), [wiki_start.md](wiki_start.md), `raw/`, `wiki/` | Added the initial LLM wiki structure and workflow documentation. |
| 2026-05-14 | Ingested project overview | [Start.MD](Start.MD) | [wiki/project_overview.md](wiki/project_overview.md), [index.md](index.md) | Summarized the product goal, scope, assumptions, ownership modes, and unresolved early decisions. |
| 2026-05-14 | Ingested development stages | [Start.MD](Start.MD) | [wiki/development_stages.md](wiki/development_stages.md), [index.md](index.md) | Extracted the staged roadmap, stage gates, Stage 8 breakdown, and cross-stage risks. |
| 2026-05-14 | Ingested Spotify integration notes | [Start.MD](Start.MD) | [wiki/spotify_integration.md](wiki/spotify_integration.md), [index.md](index.md) | Extracted OAuth constraints, ownership modes, setup responsibilities, preview flow, and implementation risks. |
| 2026-05-14 | Ingested PWA requirements | [Start.MD](Start.MD) | [wiki/pwa_requirements.md](wiki/pwa_requirements.md), [index.md](index.md) | Extracted installability, mobile layout, service worker, local check, deployment, and production-readiness notes. |
| 2026-05-14 | Built Stage 0 and Stage 1 app | Codebase | `wacken_playlist/`, `tests/`, `scripts/`, `requirements.txt`, `README.md`, `.env.example` | Flask app factory, bilingual routes, Wacken 2026 lineup, local preview flow, PWA stubs, health endpoint, dev restart script. |
| 2026-05-14 | Captured product decisions | Codebase review | [raw/product_decisions_stage0.md](raw/product_decisions_stage0.md) | Recorded confirmed choices: app name, dark festival theme, Cinzel Decorative + Inter fonts, bilingual EN/PT-BR, checklist layout, app-owned Spotify mode first. |
| 2026-05-14 | Updated project overview | [raw/product_decisions_stage0.md](raw/product_decisions_stage0.md) | [wiki/project_overview.md](wiki/project_overview.md) | Replaced open decisions table with confirmed choices. Moved remaining open items to a separate section. |
| 2026-05-14 | Updated development stages | Codebase, [Start.MD](Start.MD) | [wiki/development_stages.md](wiki/development_stages.md) | Added Status column. Marked Stage 0 and Stage 1 as Done. Marked Stage 2 as Next. Added Current Stage section. |
| 2026-05-14 | Created Stage 1 implementation record | Codebase | [wiki/stage1_implementation.md](wiki/stage1_implementation.md), [index.md](index.md) | Documented file responsibilities, routes, language support, preview logic, lineup data, run commands, and Stage 2 prerequisites. |
| 2026-05-14 | Tagged alpha release | Stage 0 + Stage 1 completion | `v0.1.0-alpha` on main | First tagged release. Stage 0 and Stage 1 complete. App runs locally with band selection, bilingual UI, local preview, PWA stubs. Stage 2 (Spotify lookup) is next. |
| 2026-05-15 | Visual enhancements post-alpha | Icon and banner assets | `v0.1.1` on main | Added metal skull logo (icon.png) and fire banner (banner.png) with parallax effect. Updated service worker to v4 cache. Improved PWA presentation and visual impact. |
| 2026-05-15 | Updated Stage 1 wiki | [wiki/stage1_implementation.md](wiki/stage1_implementation.md) | Post-Alpha Visual Enhancements section | Documented icon, banner, and service worker v4 updates in the Stage 1 implementation record. |
| 2026-05-16 | Built Stage 3 app-owned playlist creation | Codebase | `wacken_playlist/services/spotify.py`, `wacken_playlist/services/playlist.py`, `wacken_playlist/routes.py`, `wacken_playlist/templates/index.html`, `wacken_playlist/i18n/*.json`, `tests/`, [.env.example](.env.example) | Added OAuth setup flow (`/auth/spotify/login` + callback), refresh-token-based `create_playlist`, `PlaylistBuilder.build_and_create`, CSRF-protected `POST /create`, result UI, unit + integration tests, and i18n keys for the new states. Operator captures the refresh token once, then the Create button is functional. Default visibility public. |
| 2026-05-16 | Created Stage 3 wiki page | Codebase | [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md), [index.md](index.md) | Documented the OAuth flow, `SpotifyClient` extensions, builder + route behavior, error-to-i18n mapping, test coverage, and the operator setup walkthrough. |
| 2026-05-16 | Migrated Stage 3 to Feb 2026 Spotify API | [Spotify Feb 2026 changelog](https://developer.spotify.com/documentation/web-api/references/changes/february-2026) | `wacken_playlist/services/spotify.py`, `tests/unit/test_spotify_client.py`, [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md) | Live testing returned bare HTTP 403 "Forbidden" with no detail. Root cause was Spotify removing `POST /users/{user_id}/playlists` → `POST /me/playlists` and `POST /playlists/{id}/tracks` → `POST /playlists/{id}/items` in their February 2026 changelog (not reverted in March 2026). Switched to the new endpoints; removed the now-unneeded `/me` lookup. Tests updated; 61/61 green. |

## Ingest Checklist

- Add or update source material in `raw/`.
- Create or update processed knowledge pages in `wiki/`.
- Update [index.md](index.md) with new pages and relationships.
- Add a new row to this log with the date, source, output, and notes.
- Keep source material separate from interpretation.
