# Wacken Playlist Web App - Start Brief

## Original User Prompt

> I'd like to develop a web app that is hosted in a web page and can be saved as an app for my phone or open on a browser.
> I want you to first make an .md file and break down the development into stages, with detailed steps to be taken on my side, and with steps that you will take during the development.
> Indicate when a step will be higher in complexity and more likely to break the development.
>
> The starting idea of this app will be to take a list of bands that will play in Wacken Open Air 2026, and allow to select by checking which bands I'd like to see live, and it will make a playlist using the top 10 streamed songs of each band in spotify and add them all to a playlist. I'd like to be able to name the playlist as well.
>
> On a second stage I'd like to be able to select whether it will take songs from the most recently available setlist.fm for that band, or from the top 10 streamed in spotify.
>
> On a third stage, I'd like to have the possibility of selecting previous Wacken yeaars to make playlists as well, using historical lineup data available either from Wacken website or publicly available information.
>
> On a later stage I'd like to be able to mix different years and bands, and at this same stage I'd like a shuffle option which will select 5 out of 10 top streamed songs from 10 bands mixed accross different years of Wacken to make a nice blended metal playlist. Please break this stage down into steps so we can ensure that they work properly.
>
> IMPORTANT NOTE: Please check with me whenever you have questions. Ask me for the webapp development what kind of style, pallete, font and orther info you will add. Save this prompt together with the .MD file and name it Start.MD so I can call it out later. Use coding good practices and ensure proper working with github

## Current Repository Context

This is the correct repository for the Wacken playlist web app. Development should start from scratch here, with no need to preserve or merge with an older app direction.

Working assumption:

- This repository will contain the full Wacken playlist app.
- The app should be built as a browser-first Progressive Web App (PWA), installable on a phone.
- Early development can run locally before deployment is chosen.
- Secrets such as Spotify and setlist.fm credentials must never be committed.

## Project Goal

Build a responsive web app that lets users select Wacken Open Air bands and generate Spotify playlists from those selections.

The app should support two playlist ownership modes:

- App-owned mode: visitors do not log into Spotify. The backend uses one dedicated Spotify account owned by the app, creates the playlist there, and gives the visitor a Spotify link they can open, follow, save, or copy in their own account.
- Personal mode: a visitor logs into Spotify, grants playlist permissions, and the playlist is created directly in their Spotify account.

Recommended product order:

1. Build app-owned mode first, because it creates the simplest user experience.
2. Add personal mode later as an optional path for users who want playlist ownership.

## Important Spotify Constraint

Spotify playlist creation still requires OAuth access for a Spotify user account. There is no fully anonymous Spotify API flow that can create playlists.

This means:

- App-owned mode still needs one Spotify account for the app.
- That app account must authorize the app once through Spotify OAuth.
- The app stores the app account refresh token securely in local or production secrets.
- Generated playlists are owned by the app account.
- Users receive a playlist link, but they do not own that playlist unless they copy or recreate it in their own Spotify account.

## Decisions To Confirm Before UI Build

Please confirm these before the first app shell is built:

- Visual style: dark festival dashboard, clean Spotify-like utility app, Wacken-inspired heavy metal theme, or another direction.
- Palette: black/red/gold, black/green, dark neutral with accent colors, or custom colors.
- Font preference: modern sans-serif, condensed festival poster style for headings, system font, or a specific Google Font.
- App name.
- Logo/icon direction for phone install.
- Layout preference: compact checklist-first UI, rich band cards, or table/list view.
- Language: English only, Portuguese only, or bilingual.
- Whether the first release should use app-owned mode only.
- Whether local development is enough at first, or whether a hosting target should be selected early.

## Technical Direction

Recommended starting stack:

- Backend: Flask.
- Frontend: responsive HTML, CSS, and JavaScript served by Flask.
- PWA: web app manifest, service worker, theme color, installable icons, and mobile-safe layout.
- Spotify search and metadata: Spotify Web API.
- Spotify playlist creation: OAuth Authorization Code flow for the app-owned account first, then optional user OAuth later.
- setlist.fm: setlist.fm API, added after the first Spotify top-tracks version works.
- Data storage: local JSON files at first; SQLite once historical years, cached matches, saved mixes, or auth token records are introduced.
- Tests: focused Python tests for playlist-building and matching logic, plus manual browser checks for UI/PWA behavior.
- Hosting: choose later from Render, Fly.io, Railway, PythonAnywhere, or another Flask-friendly host.

## Execution Order

Build in this order unless a later decision changes the strategy:

1. Stage 0 - Fresh repository setup.
2. Stage 1 - App shell and static Wacken 2026 band selection.
3. Stage 2 - Spotify lookup and playlist preview without creating playlists.
4. Stage 3 - App-owned playlist creation.
5. Stage 4 - PWA polish for the first usable app-owned release.
6. Stage 5 - Optional personal Spotify login and user-owned playlists.
7. Stage 6 - setlist.fm song source.
8. Stage 7 - Previous Wacken years.
9. Stage 8 - Mixed-year and shuffle playlist generation.
10. Stage 9 - Deployment, production hardening, and release checklist.

## GitHub Practices

My development practices:

- Check `git status` before editing.
- Keep changes grouped by stage or feature.
- Avoid committing secrets or machine-specific files.
- Add `.env.example` for required environment variables.
- Add or update `.gitignore` early.
- Use clear commit messages after stable milestones.
- Keep documentation current when behavior changes.
- Add tests around risky logic, especially API matching, deduplication, OAuth, and shuffle behavior.

Your responsibilities:

- Review and answer design questions before UI implementation.
- Create Spotify Developer credentials for the app.
- Create or choose the dedicated app-owned Spotify account.
- Authorize the app-owned Spotify account once during setup.
- Add allowed redirect URLs in the Spotify Developer dashboard.
- Provide a setlist.fm API key when that stage begins.
- Review each completion gate before moving into higher-risk stages.
- Provide production hosting credentials or access if deployment begins.

## Complexity Labels

- Low: documentation, simple UI, static data, isolated setup.
- Medium: app flow, state handling, local storage, playlist-building logic.
- High: OAuth, third-party APIs, historical data quality, deployment, large randomization/deduplication flows.

## Stage 0 - Fresh Repository Setup

Goal: initialize this repository as a clean, runnable Wacken playlist app.

Order of execution:

1. Confirm design and product decisions.
2. Create the initial project structure.
3. Add documentation and environment templates.
4. Add a minimal runnable Flask route.
5. Verify the app runs locally.

Your steps:

- Confirm visual style, palette, font, app name, and language.
- Confirm Flask as the initial backend.
- Confirm app-owned mode as the first Spotify integration target.
- Confirm local-only development is enough for the first milestone.

My steps:

- Create the initial app structure.
- Add `README.md` with setup and run instructions.
- Add `.gitignore`.
- Add `.env.example` with expected variables.
- Add a Flask app entry point.
- Add a basic frontend folder structure.
- Add a local development command.
- Add a health check or simple app route.
- Verify the app runs locally.

Complexity: Low.

Higher-risk items:

- Choosing a stack that does not match the eventual hosting target can create migration work later.
- Leaving environment variable structure unclear can make OAuth setup harder.

Completion gate:

- The repository contains a clean runnable Flask app shell with setup documentation, `.env.example`, `.gitignore`, and no committed secrets.

## Stage 1 - App Shell And Wacken 2026 Band Selection

Goal: let users open the app, see Wacken 2026 bands, select bands, and enter a playlist name.

Order of execution:

1. Add initial Wacken 2026 lineup data.
2. Build the first responsive UI.
3. Add selection state and playlist name handling.
4. Add validation for empty selections and missing names.
5. Test the flow without Spotify integration.

Your steps:

- Confirm the source for Wacken Open Air 2026 lineup data.
- Confirm whether the first band list should be manually curated or imported automatically.
- Review the first UI direction before Spotify logic is added.

My steps:

- Add a lineup data file or simple data module.
- Build a responsive checklist, card list, or table view.
- Add playlist name input.
- Add selected-band summary.
- Add client-side and server-side validation.
- Add basic tests for selection payload handling where useful.

Complexity: Low to Medium.

Higher-risk items:

- Lineup data may change before the festival.
- A rich card UI can slow down early progress if the data model is still changing.

Completion gate:

- A user can select Wacken 2026 bands, enter a playlist name, submit the form, and see a local preview/confirmation without contacting Spotify.

## Stage 2 - Spotify Lookup And Playlist Preview

Goal: use Spotify data to match selected bands and preview the tracks that would be added, without creating a playlist yet.

Order of execution:

1. Add Spotify API configuration.
2. Implement app-level Spotify search access.
3. Match selected band names to Spotify artists.
4. Fetch top tracks for each matched artist.
5. Show a preview with warnings for missing or ambiguous matches.

Your steps:

- Create Spotify Developer app credentials.
- Provide local Spotify app settings through `.env`.
- Review matched artists and previewed tracks for a sample selection.

My steps:

- Add Spotify API client code.
- Add artist search.
- Add top-track lookup.
- Add basic matching rules and warnings.
- Add preview UI.
- Add tests for matching, duplicate handling, and empty results.

Complexity: Medium to High.

Higher-risk items:

- Spotify API access requires valid app credentials.
- Artist matching can be inaccurate when band names are ambiguous.
- Spotify top tracks depend on market and API behavior.

Completion gate:

- A user can select bands and see a Spotify-based preview of the tracks that will be used, including clear warnings for missing artists or tracks.

## Stage 3 - App-Owned Playlist Creation

Goal: create playlists under the dedicated app-owned Spotify account and share the resulting link with visitors.

Order of execution:

1. Create or choose the app-owned Spotify account.
2. Authorize that account through Spotify OAuth.
3. Store the refresh token securely outside Git.
4. Add backend playlist creation using the app-owned token.
5. Return the Spotify playlist link to the user.
6. Add rate-limit and error handling.

Your steps:

- Create or nominate the app-owned Spotify account.
- Log into that account during the OAuth setup flow.
- Add the local redirect URL in the Spotify Developer dashboard.
- Confirm whether generated playlists should be public.
- Review a test playlist created by the app account.

My steps:

- Add OAuth setup route or one-time token capture command.
- Add environment variables for the app-owned refresh token.
- Add backend playlist creation.
- Add track insertion.
- Add result page with Spotify link.
- Add partial success reporting.
- Add tests around playlist payload construction.

Complexity: High.

Higher-risk items:

- OAuth can fail if redirect URLs, scopes, or environment variables are wrong.
- The app-owned account can accumulate many playlists over time.
- Public playlists created too freely could need abuse prevention later.
- Refresh token handling must be secure.

Completion gate:

- A visitor can generate a Wacken 2026 playlist without logging into Spotify, and the app returns a working Spotify link owned by the app account.

## Stage 4 - First PWA Release Polish

Goal: make the app-owned version pleasant to use from phone and browser before adding more complex features.

Order of execution:

1. Add PWA manifest.
2. Add service worker.
3. Add icons and theme color.
4. Polish mobile layout.
5. Add loading, success, warning, and error states.
6. Perform a local installability check.

Your steps:

- Test the app on your phone or mobile browser.
- Confirm the app name and icon direction.
- Review the success/error messaging.

My steps:

- Add PWA manifest and service worker.
- Add app icon placeholders or final icons.
- Improve responsive layout.
- Add loading states while Spotify calls run.
- Add clear result and failure screens.
- Document known local PWA limitations.

Complexity: Medium.

Higher-risk items:

- Service worker caching can accidentally serve stale files.
- Mobile browsers differ in install behavior.

Completion gate:

- The app-owned playlist flow is usable on desktop and mobile, and the app has basic PWA install support.

## Stage 5 - Optional Personal Spotify Login

Goal: let users choose to create playlists directly in their own Spotify account.

Order of execution:

1. Add a clear mode choice: app-owned link or create in my Spotify.
2. Add user OAuth login.
3. Store user session data securely.
4. Create playlists under the logged-in user's Spotify account.
5. Add logout and session expiration handling.

Your steps:

- Confirm whether this mode should be added after app-owned mode is stable.
- Test Spotify login with your own account.
- Confirm the language explaining the difference between app-owned and personal playlists.

My steps:

- Add user login route.
- Add Spotify callback handling for users.
- Add session storage.
- Add user-owned playlist creation path.
- Add logout.
- Add tests for mode selection and auth-required behavior.

Complexity: High.

Higher-risk items:

- User OAuth adds more security and session complexity.
- Spotify redirect URLs must be exact for local and production environments.
- Users may be confused if ownership modes are not explained clearly.

Completion gate:

- A user can choose personal mode, log into Spotify, create a playlist in their own account, and log out.

## Stage 6 - Spotify Top Tracks Or Latest setlist.fm Setlist

Goal: let the user choose whether playlist songs come from Spotify top tracks or the most recent available setlist.fm setlist.

Order of execution:

1. Add song-source UI.
2. Integrate setlist.fm artist lookup.
3. Fetch latest setlist.
4. Match setlist songs back to Spotify tracks.
5. Add fallback and warning behavior.
6. Support both app-owned and personal playlist creation modes.

Your steps:

- Create or provide a setlist.fm API key.
- Confirm whether setlist-based playlists should include every song from the latest setlist or be capped at 10.
- Confirm fallback behavior when setlist.fm has no usable data for a band.
- Review mismatched song results.

My steps:

- Add source selector.
- Integrate setlist.fm artist and setlist lookup.
- Normalize setlist song names.
- Search Spotify for setlist songs by artist and title.
- Add warning messages for songs that cannot be matched.
- Store enough metadata to explain where playlist items came from.
- Add tests for source selection, fallback behavior, and missing song handling.

Complexity: High.

Higher-risk items:

- setlist.fm data may have alternate spellings, incomplete setlists, missing artists, or covers.
- Matching live song titles to Spotify recordings can be unreliable.
- API limits and terms must be respected.

Completion gate:

- A user can generate a playlist from Spotify top tracks or latest setlist data, with clear reporting for skipped or unmatched songs.

## Stage 7 - Previous Wacken Years

Goal: allow users to choose previous Wacken years and generate playlists from historical lineup data.

Order of execution:

1. Choose the first supported year range.
2. Research and select data sources.
3. Create a historical lineup data model.
4. Import or manually curate the first years.
5. Add year selection to the UI.
6. Reuse playlist generation from earlier stages.

Your steps:

- Confirm the first range of years to support.
- Confirm preferred data sources: official Wacken sources first, then public sources if needed.
- Review and approve historical lineup data quality for the first imported years.
- Decide whether historical data should be stored directly in the repository, cached locally, or imported into a database.

My steps:

- Research available historical lineup sources.
- Design a lineup data model with year, band name, source URL, and optional stage/day metadata.
- Build an import or curation process.
- Add a year selector.
- Display bands for the selected year.
- Reuse playlist creation and song source selection.
- Add source attribution in documentation or an app info/debug view.

Complexity: High.

Higher-risk items:

- Historical lineup data may be incomplete or inconsistent.
- Public sources may disagree.
- Automated scraping can break or violate source expectations.
- Supporting many years increases Spotify matching errors and API volume.

Completion gate:

- A user can select one previous Wacken year, choose bands from that lineup, and create a playlist through the existing ownership modes.

## Stage 8 - Mix Years And Bands

Goal: allow users to combine bands from multiple Wacken years into one playlist.

This stage is split into smaller parts because cross-year state and randomization can become fragile.

### Stage 8A - Multi-Year Selection

Order of execution:

1. Add multi-year controls.
2. Display combined lineups.
3. Add year labels.
4. Implement duplicate-band rules.

Your steps:

- Confirm how years should be selected: checkboxes, multi-select dropdown, or year range.
- Confirm whether duplicate band appearances across years should be merged or shown separately by year.

My steps:

- Add multi-year selection.
- Display combined lineups.
- Add visual year labels for each band.
- Implement duplicate handling rules.

Complexity: Medium.

Completion gate:

- A user can select multiple years and see a clear combined band list with duplicate handling.

### Stage 8B - Manual Cross-Year Band Selection

Order of execution:

1. Persist selected bands while changing years.
2. Add selected-band summary.
3. Add remove/edit actions.
4. Add ordering rules.

Your steps:

- Test selecting bands from different years.
- Confirm playlist ordering: by year, band name, selection order, or randomized.

My steps:

- Preserve selected bands while changing selected years.
- Add a selected-bands summary.
- Add remove and edit actions.
- Preserve selection state during navigation or refresh where reasonable.

Complexity: Medium.

Completion gate:

- A user can manually build a cross-year band selection and create a playlist from it.

### Stage 8C - Shuffle Playlist Generator

Goal: choose 10 bands across selected Wacken years, choose 5 songs out of each band's top 10 Spotify tracks, and create a blended 50-song playlist.

Order of execution:

1. Add shuffle configuration.
2. Select eligible bands.
3. Fetch top 10 tracks per selected band.
4. Randomly choose 5 tracks per band.
5. Deduplicate tracks.
6. Shuffle final order.
7. Show preview.
8. Create playlist after confirmation.

Your steps:

- Confirm whether the 10 bands are selected randomly by the app or manually by you.
- Confirm whether all selected bands must come from different years.
- Confirm whether shuffle should avoid repeated artists, repeated songs, or both.
- Confirm whether the final playlist should be reshuffled before adding to Spotify.

My steps:

- Build a shuffle configuration panel.
- Add rules for selecting 10 bands across chosen years.
- Fetch top 10 Spotify tracks per chosen band.
- Randomly choose 5 tracks per band.
- Deduplicate tracks.
- Mix the final order.
- Show a preview before playlist creation.
- Add a reshuffle action.
- Add tests for random selection boundaries, duplicate handling, and final playlist size.

Complexity: High.

Higher-risk items:

- Random selection can produce poor results without clear constraints.
- Deduplication can reduce the final playlist below 50 songs.
- Large multi-band Spotify lookups can hit API limits.
- Shuffle bugs are easy to miss without tests.

Completion gate:

- A user can generate, preview, reshuffle, and create a 50-song mixed-year playlist or see a clear warning when there are not enough eligible tracks.

### Stage 8D - Review, Save, And Reuse Mixes

Order of execution:

1. Decide whether saving is needed.
2. Add saved mix storage.
3. Add preview history.
4. Add recreate/update behavior.
5. Add export/import if useful.

Your steps:

- Confirm whether mixes should be saved locally, tied to Spotify login, or exportable.
- Review whether saved mixes need editing.

My steps:

- Add saved mix storage if desired.
- Add playlist preview history.
- Add ability to recreate or update a previous playlist.
- Add export/import if useful.

Complexity: Medium to High.

Higher-risk items:

- Saving user data introduces privacy, persistence, and cleanup responsibilities.

Completion gate:

- A user can save or reuse a mix in the agreed storage mode, or the feature is intentionally deferred.

## Stage 9 - Deployment, Production Hardening, And Release

Goal: make the app reliable from both phone and browser on a hosted URL.

Order of execution:

1. Choose hosting provider.
2. Configure production environment variables.
3. Add production Spotify redirect URLs.
4. Deploy the app.
5. Test app-owned playlist creation in production.
6. Test personal mode in production if enabled.
7. Test PWA install behavior.
8. Finalize release checklist.

Your steps:

- Choose a hosting provider.
- Add production Spotify redirect URL in Spotify Developer dashboard.
- Provide production environment variables securely.
- Test install behavior on your phone.
- Test Spotify flows from the hosted URL.
- Review final UI on mobile.

My steps:

- Configure production settings.
- Add deployment documentation.
- Verify PWA installability.
- Add responsive/mobile polish.
- Add loading, success, warning, and error states.
- Add logging for API failures.
- Add basic security headers and production configuration.
- Add a release checklist.

Complexity: Medium to High.

Higher-risk items:

- Hosted Spotify OAuth requires exact production redirect URLs.
- Service worker caching can accidentally serve stale files.
- Mobile browsers differ in PWA install behavior.
- Production secrets must be handled carefully.

Completion gate:

- The app is hosted, installable on a phone, and able to create Spotify playlists from the production URL using the enabled ownership modes.

## Possible Future Enhancements

- User login independent of Spotify.
- Favorite bands list.
- Playlist cover image generation.
- Wacken stage/day schedule planning once schedules are available.
- Conflict detection between bands playing at the same time.
- Export selected bands to CSV or JSON.
- Support other festivals.
- Shareable playlist recipes.
- Admin cleanup for old app-owned playlists.

## First Implementation Checklist

- Confirm visual style, palette, font, app name, and language.
- Confirm Flask as the initial backend.
- Confirm app-owned mode as the first playlist ownership mode.
- Create or choose the app-owned Spotify account.
- Add `.gitignore`.
- Add `.env.example`.
- Add `README.md`.
- Add Flask app shell.
- Add basic responsive frontend.
- Add initial Wacken 2026 lineup data source.
- Add Spotify lookup and preview.
- Add app-owned Spotify OAuth/token setup.
- Add app-owned playlist creation.
- Add PWA manifest and service worker.
