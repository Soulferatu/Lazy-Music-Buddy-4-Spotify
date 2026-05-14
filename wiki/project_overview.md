# Project Overview

Purpose: define the stable product goal, current scope, and operating assumptions for Lazy Music Buddy. Source: [Start.MD](../Start.MD).

## Product Goal

Lazy Music Buddy is a browser-first Progressive Web App for building Spotify playlists from Wacken Open Air band selections.

The first user-facing flow should let someone:

1. Open the app in a browser or installed mobile PWA.
2. Select Wacken Open Air bands.
3. Name a playlist.
4. Generate or preview Spotify tracks for those bands.
5. Receive a Spotify playlist link once playlist creation is enabled.

## Current Scope

The app is focused on Wacken Open Air playlist generation. It starts with Wacken 2026 and later expands into previous years, cross-year mixes, and shuffle-based playlist generation.

Early work should prioritize a runnable local app, clear data structures, and a simple band-selection flow before adding high-risk API integrations.

## Ownership Modes

The app should eventually support two Spotify playlist ownership modes:

| Mode | Description | Product Order |
| --- | --- | --- |
| App-owned mode | The app uses a dedicated Spotify account and returns playlist links to visitors. | Build first |
| Personal mode | A visitor logs into Spotify and creates the playlist in their own account. | Add later |

App-owned mode is the first target because it gives visitors the simplest experience.

## Core Assumptions

- This repository contains the full Wacken playlist app.
- The app should be browser-first and installable on phones as a PWA.
- Local development is enough before a hosting provider is chosen.
- Secrets such as Spotify and setlist.fm credentials must never be committed.
- Flask is the starting backend.
- The frontend is responsive HTML, CSS, and JavaScript served by Flask.
- Tests should focus on playlist-building, matching, deduplication, OAuth-adjacent payload logic, and shuffle behavior.

## Early Product Decisions Still Needed

- Visual style.
- Palette.
- Font direction.
- App name.
- Logo or install icon direction.
- Initial layout style.
- Language.
- Confirmation that app-owned mode is the first release target.
- Confirmation that local-only development is enough for the first milestone.

## Related Pages

- [Development Stages](development_stages.md)
- [Spotify Integration](spotify_integration.md)
- [PWA Requirements](pwa_requirements.md)

