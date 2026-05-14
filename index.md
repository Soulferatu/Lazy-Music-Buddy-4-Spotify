# Lazy Music Buddy Wiki Index

This is the master index for the project wiki. It tracks processed knowledge pages, their source material, and the relationships between concepts.

## Wiki Map

| Wiki Page | Purpose | Source Material | Related Pages |
| --- | --- | --- | --- |
| [wiki_start.md](wiki_start.md) | Explains the wiki workflow, search process, and update rules. | [Start.MD](Start.MD) | Project planning, ingest log |
| [wiki/project_overview.md](wiki/project_overview.md) | Defines the stable product goal, current scope, and operating assumptions. | [Start.MD](Start.MD) | Development stages, Spotify integration, PWA requirements |
| [wiki/development_stages.md](wiki/development_stages.md) | Summarizes the staged roadmap, complexity, gates, and sequencing risks. | [Start.MD](Start.MD) | Project overview, Spotify integration, PWA requirements |
| [wiki/spotify_integration.md](wiki/spotify_integration.md) | Captures Spotify OAuth, ownership modes, preview flow, setup responsibilities, and risks. | [Start.MD](Start.MD) | Project overview, development stages, PWA requirements |
| [wiki/pwa_requirements.md](wiki/pwa_requirements.md) | Captures installability, mobile behavior, local checks, deployment relationship, and PWA risks. | [Start.MD](Start.MD) | Project overview, development stages, Spotify integration |

## Knowledge Areas

### Product Direction

- Project brief and staged roadmap: [Start.MD](Start.MD)
- Wiki workflow: [wiki_start.md](wiki_start.md)
- Project overview: [wiki/project_overview.md](wiki/project_overview.md)
- Development stages: [wiki/development_stages.md](wiki/development_stages.md)
- Spotify integration: [wiki/spotify_integration.md](wiki/spotify_integration.md)
- PWA requirements: [wiki/pwa_requirements.md](wiki/pwa_requirements.md)

### Integrations

- Spotify OAuth and playlist creation: [wiki/spotify_integration.md](wiki/spotify_integration.md)

### App Delivery

- PWA and mobile installability: [wiki/pwa_requirements.md](wiki/pwa_requirements.md)

### Ingest Tracking

- Every source-to-wiki update should be recorded in [log.md](log.md).

## Relationship Rules

- `raw/` contains original source documents or captured notes.
- `wiki/` contains processed, rewritten knowledge pages.
- `index.md` links wiki pages together and records how they relate.
- `log.md` records what was ingested, when it was ingested, and what changed.

## Next Pages To Create

- `wiki/setlistfm_integration.md` for setlist.fm lookup, matching, fallback rules, and API risks.
- `wiki/historical_lineup_data.md` for previous Wacken years, source attribution, and curation rules.
