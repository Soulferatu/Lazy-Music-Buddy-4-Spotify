# Development Stages

Purpose: provide a concise roadmap for the app build, with stage goals, complexity, and completion gates. Source: [Start.MD](../Start.MD).

## Stage Summary

| Stage | Goal | Complexity | Status | Completion Gate |
| --- | --- | --- | --- | --- |
| Stage 0 - Fresh repository setup | Initialize a clean, runnable Wacken playlist app. | Low | **Done** | Runnable Flask shell with setup docs, `.env.example`, `.gitignore`, and no committed secrets. |
| Stage 1 - App shell and Wacken 2026 band selection | Let users select Wacken 2026 bands and enter a playlist name. | Low to Medium | **Done** | User can submit selected bands and playlist name and see a local preview or confirmation without Spotify. |
| Stage 2 - Spotify lookup and playlist preview | Match selected bands to Spotify artists and preview tracks without creating a playlist. | Medium to High | **Done** | User sees Spotify-based track previews with warnings for missing artists or tracks. |
| Stage 3 - App-owned playlist creation | Create playlists under a dedicated Spotify account and return a shareable link. | High | Pending | Visitor can generate a Wacken 2026 playlist without logging into Spotify. |
| Stage 4 - First PWA release polish | Make the app-owned version pleasant on phone and browser. | Medium | Pending | App-owned playlist flow works on desktop and mobile with basic PWA install support. |
| Stage 5 - Optional personal Spotify login | Let users create playlists directly in their own Spotify account. | High | Pending | User can log into Spotify, create a playlist in their account, and log out. |
| Stage 6 - Spotify top tracks or latest setlist.fm setlist | Add song source choice between Spotify top tracks and latest setlist.fm data. | High | Pending | User can generate from either source with reporting for skipped or unmatched songs. |
| Stage 7 - Previous Wacken years | Support historical Wacken lineup years. | High | Pending | User can select one previous year, choose bands, and create a playlist. |
| Stage 8 - Mix years and bands | Let users combine bands from multiple Wacken years. | Medium to High | Pending | User can build, preview, reshuffle, and optionally save mixed-year playlists. |
| Stage 9 - Deployment and production release | Host the app reliably with production configuration. | Medium to High | Pending | Hosted app is installable and can create Spotify playlists from production. |

## Current Stage

**Stage 3 — App-owned playlist creation.**

Stages 0–2 are complete. Stage 2 originally landed on the `stage2/spotify-preview` feature branch and was later ported into the new service-layer architecture on `arch-refactor/phase-1-config-models` — see [Stage 2 implementation](stage2_spotify_preview.md). Stage 3 introduces OAuth for the dedicated app-owned Spotify account and the first real `POST` that mutates Spotify state.

## Stage 8 Breakdown

Stage 8 is intentionally split into smaller pieces because cross-year selection and randomization are more fragile than single-year playlist flows.

| Substage | Focus | Completion Gate |
| --- | --- | --- |
| Stage 8A - Multi-year selection | Select multiple years, display combined lineups, and handle duplicate bands. | User can select multiple years and see a clear combined list. |
| Stage 8B - Manual cross-year band selection | Preserve selected bands while changing years and show an editable summary. | User can manually build a cross-year band selection. |
| Stage 8C - Shuffle playlist generator | Select 10 bands, choose 5 of each band's top 10 tracks, deduplicate, and shuffle. | User can generate, preview, reshuffle, and create a 50-song mix or see a clear warning. |
| Stage 8D - Review, save, and reuse mixes | Decide whether to save mixes and support reuse if needed. | User can save or reuse a mix, or the feature is intentionally deferred. |

## Cross-Stage Risks

- OAuth and Spotify playlist creation are high-risk and should be isolated behind clear setup docs.
- Lineup data can change or disagree across sources.
- Historical data quality can affect matching accuracy.
- Random playlist generation needs tests for size, uniqueness, and fallback behavior.
- Service worker caching can make PWA bugs confusing if cache invalidation is not handled deliberately.

## Current Development Bias

Build stable, testable layers in order:

1. Local app and static data.
2. Selection and validation.
3. Spotify preview.
4. App-owned playlist creation.
5. PWA polish.
6. More complex ownership, setlist, historical, and shuffle flows.

## Architecture Refactoring

To support the complexity of Stages 2–9, the codebase is undergoing a structured architecture migration. See [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md) for the full 6-phase plan.

Current progress:
- **Phase 1 — Config and Models** ✓ [Details](phase1_config_models.md)
- **Phase 2 — Data Layer** ✓ [Details](phase2_data_layer.md)
- **Phase 3 — i18n Centralization** ✓ [Details](phase3_i18n.md)
- **Phase 4 — Service Layer Scaffolding** ✓ [Details](phase4_services.md)
- **Phase 5 — Security and Platform Hardening** ✓ [Details](phase5_security_platform.md)
- **Phase 6 — Test Architecture** ✓ [Details](phase6_test_architecture.md)

Architecture migration complete. Stage 2 (Spotify lookup) has been ported into the new service layer; next product step is Stage 3 (app-owned playlist creation).

## Related Pages

- [Project Overview](project_overview.md)
- [Spotify Integration](spotify_integration.md)
- [PWA Requirements](pwa_requirements.md)
- [Architecture Migration Plan](../ARCH_MIGRATION_PLAN.md)

