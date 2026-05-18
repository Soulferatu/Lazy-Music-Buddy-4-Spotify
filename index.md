# Lazy Music Buddy Wiki Index

This is the master index for the project wiki. It tracks processed knowledge pages, their source material, and the relationships between concepts.

## Wiki Map

| Wiki Page | Purpose | Source Material | Related Pages |
| --- | --- | --- | --- |
| [wiki_start.md](wiki_start.md) | Explains the wiki workflow, search process, and update rules. | [Start.MD](Start.MD) | Project planning, ingest log |
| [wiki/project_overview.md](wiki/project_overview.md) | Defines the stable product goal, current scope, and operating assumptions. | [Start.MD](Start.MD) | Development stages, Spotify integration, PWA requirements |
| [wiki/development_stages.md](wiki/development_stages.md) | Summarizes the staged roadmap, complexity, gates, and sequencing risks. | [Start.MD](Start.MD) | Project overview, Spotify integration, PWA requirements |
| [wiki/spotify_integration.md](wiki/spotify_integration.md) | Captures Spotify OAuth, ownership modes, preview flow, setup responsibilities, and risks. | [Start.MD](Start.MD) | Project overview, development stages, PWA requirements, band track resolution |
| [wiki/pwa_requirements.md](wiki/pwa_requirements.md) | Captures installability, mobile behavior, local checks, deployment relationship, and PWA risks. | [Start.MD](Start.MD) | Project overview, development stages, Spotify integration |
| [wiki/stage1_implementation.md](wiki/stage1_implementation.md) | Records what was built in Stage 0 and Stage 1, file responsibilities, routes, and Stage 2 prerequisites. | Codebase, [raw/product_decisions_stage0.md](raw/product_decisions_stage0.md) | Development stages, Spotify integration, PWA requirements |
| [wiki/stage2_spotify_preview.md](wiki/stage2_spotify_preview.md) | Records what Stage 2 delivers, the Spotify port into the service layer, configuration, and tests. | Codebase, original branch `stage2/spotify-preview` | Phase 4 services, development stages, Spotify integration |
| [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md) | Records the Stage 3 build: OAuth setup flow, `SpotifyClient` create_playlist, `PlaylistBuilder.build_and_create`, `POST /create`, result UI, and operator setup walkthrough. | Codebase | Stage 2 preview, Spotify integration, development stages |
| [wiki/stage4_pwa_polish.md](wiki/stage4_pwa_polish.md) | Records Stage 4: loading states, mobile auto-scroll, dynamic countdown, Apple PWA meta tags, manifest scope, SW fix, version bump; known local PWA limitations. | Codebase | PWA requirements, Stage 3 playlist creation |
| [wiki/stage5_deployment.md](wiki/stage5_deployment.md) | Records Stage 5: Vercel deployment, production env vars, redirect URL setup, PWA install on production origin, cache-busting workflow, and smoke-test checklist. | Codebase, [DEPLOYMENT.md](DEPLOYMENT.md), [vercel.json](vercel.json) | PWA requirements, Stage 4 polish, band track resolution |
| [wiki/band_track_resolution.md](wiki/band_track_resolution.md) | Records the as-built offline pre-resolution system: `scripts/resolve_lineup.py`, two-strategy search, artist-ID filter, `artist_overrides.json`, `permanently_unresolved` flag, runtime `PlaylistBuilder` behavior, JSON schema. | Codebase, [raw/spotify_search_proposal.md](raw/spotify_search_proposal.md) | Spotify integration, Stage 5 deployment, track top-up plan |
| [wiki/track_topup_plan.md](wiki/track_topup_plan.md) | Documents how to handle bands still below the 10-track cap: pre-flight checks, the "5-track plateau" diagnostic, staged retry by track count, success criteria, rollback. | [Ten_song_fix.md](Ten_song_fix.md), Codebase | Band track resolution, Spotify integration |

## Knowledge Areas

### Product Direction

- Project brief and staged roadmap: [Start.MD](Start.MD), [PHASES.md](PHASES.md)
- Operating instructions for Claude: [CLAUDE.md](CLAUDE.md)
- Wiki workflow: [wiki_start.md](wiki_start.md)
- Project overview: [wiki/project_overview.md](wiki/project_overview.md)
- Development stages (current: **Stage 6 — setlist.fm** is next; Stages 0–5 done): [wiki/development_stages.md](wiki/development_stages.md)
- Spotify integration: [wiki/spotify_integration.md](wiki/spotify_integration.md)
- PWA requirements: [wiki/pwa_requirements.md](wiki/pwa_requirements.md)

### Implementation Records

- Stage 0 and Stage 1 build details: [wiki/stage1_implementation.md](wiki/stage1_implementation.md)
- Stage 2 Spotify preview: [wiki/stage2_spotify_preview.md](wiki/stage2_spotify_preview.md)
- Stage 3 playlist creation: [wiki/stage3_playlist_creation.md](wiki/stage3_playlist_creation.md)
- Stage 4 PWA polish: [wiki/stage4_pwa_polish.md](wiki/stage4_pwa_polish.md)
- Stage 5 deployment: [wiki/stage5_deployment.md](wiki/stage5_deployment.md)
- Architecture migration phases 1–6: [wiki/phase1_config_models.md](wiki/phase1_config_models.md) … [wiki/phase6_test_architecture.md](wiki/phase6_test_architecture.md)
- Resolved product decisions: [raw/product_decisions_stage0.md](raw/product_decisions_stage0.md)

### Integrations

- Spotify OAuth and playlist creation: [wiki/spotify_integration.md](wiki/spotify_integration.md)
- Offline band track resolution (v0.5.4+): [wiki/band_track_resolution.md](wiki/band_track_resolution.md)
- Track top-up plan for low-count bands: [wiki/track_topup_plan.md](wiki/track_topup_plan.md)

### App Delivery

- PWA and mobile installability: [wiki/pwa_requirements.md](wiki/pwa_requirements.md)
- Vercel deployment: [wiki/stage5_deployment.md](wiki/stage5_deployment.md), [DEPLOYMENT.md](DEPLOYMENT.md)

### Ingest Tracking

- Every source-to-wiki update should be recorded in [log.md](log.md).

## Relationship Rules

- `raw/` contains original source documents or captured notes.
- `wiki/` contains processed, rewritten knowledge pages.
- `index.md` links wiki pages together and records how they relate.
- `log.md` records what was ingested, when it was ingested, and what changed.

## Next Pages To Create

- `wiki/setlistfm_integration.md` for setlist.fm lookup, matching, fallback rules, and API risks (Stage 6).
- `wiki/historical_lineup_data.md` for previous Wacken years, source attribution, and curation rules (Stage 7).
