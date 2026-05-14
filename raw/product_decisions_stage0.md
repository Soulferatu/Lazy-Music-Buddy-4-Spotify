# Product Decisions — Stage 0

Resolved product and design decisions captured during Stage 0 and Stage 1 setup.

## App Name

Play[my W:O:A]list

## Visual Style

Dark festival dashboard. Background near-black (#141316), accented with festival gold and strong contrast white text.

## Fonts

- Headings: Cinzel Decorative (Bold 700) — festival poster weight.
- Body and UI: Inter (Regular 400, SemiBold 600, Bold 700, ExtraBold 800).
- Accent / secondary: Special Elite.
- Source: Google Fonts.

## Language

Bilingual: English (en) and Brazilian Portuguese (pt-BR). Language is switchable in the UI without a page reload.

## Layout

Checklist-first. The band list is a scrollable checklist. The playlist name input and preview are in the same single-page flow.

## Backend

Flask, with an app factory pattern (`create_app`).

## Spotify Ownership Mode — First Target

App-owned mode first. The app uses a dedicated Spotify account and returns playlist links. Visitors do not log into Spotify in the first release.

## PWA

Progressive Web App from the start. Manifest and service worker added as stubs in Stage 1, to be completed in Stage 4.

## Local Development

Local development is enough for Stage 0 through Stage 4. Hosting provider chosen later.

## Decisions Still Open

- Logo and install icon (placeholder SVG exists, final icon not designed).
- Hosting provider (deferred to Stage 9).
- Personal Spotify login mode (deferred to Stage 5).
