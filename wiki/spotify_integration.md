# Spotify Integration

Purpose: capture the Spotify-specific product constraints, ownership modes, setup responsibilities, and implementation risks. Source: [Start.MD](../Start.MD).

## Core Constraint

Spotify playlist creation requires OAuth access for a Spotify user account. There is no fully anonymous Spotify API path that can create playlists.

This affects both planned ownership modes:

- App-owned mode still needs a dedicated Spotify account owned by the app.
- Personal mode needs each visitor to log into Spotify and grant playlist permissions.

## Ownership Modes

| Mode | Owner Of Created Playlist | User Login Required | Build Order |
| --- | --- | --- | --- |
| App-owned mode | Dedicated app Spotify account | No visitor login | First |
| Personal mode | Visitor's Spotify account | Yes | Later |

In app-owned mode, visitors receive a playlist link they can open, follow, save, or copy into their own account, but they do not own the playlist.

## App-Owned Mode Requirements

The app-owned flow needs:

1. Spotify Developer app credentials.
2. A dedicated app-owned Spotify account.
3. A one-time OAuth authorization for that account.
4. A securely stored refresh token.
5. Backend playlist creation using the app account token.
6. Track insertion.
7. A result page that returns the Spotify playlist link.
8. Rate-limit and error handling.

Secrets must stay in local or production environment variables and must not be committed.

## Personal Mode Requirements

The personal mode flow needs:

1. A clear UI choice between app-owned and personal playlist creation.
2. User OAuth login.
3. Spotify callback handling.
4. Secure session storage.
5. Playlist creation in the logged-in user's account.
6. Logout and session expiration behavior.

This mode should wait until app-owned creation is stable because it adds security and session complexity.

## Spotify Preview Flow

Before playlist creation, the app should support Spotify lookup and preview:

1. Configure Spotify API access.
2. Search Spotify artists for selected band names.
3. Match selected band names to likely Spotify artist records.
4. Fetch top tracks for matched artists.
5. Show a preview with warnings for missing or ambiguous matches.

Preview should happen before creation so bad matches can be reviewed before playlists are written.

## Risks

- Redirect URLs, scopes, and environment variables must match exactly.
- Artist matching can be inaccurate when band names are ambiguous.
- Spotify top tracks depend on market and API behavior.
- The app-owned account can accumulate many playlists over time.
- Public playlist creation may need abuse prevention later.
- Refresh tokens must be stored securely.
- Larger historical and shuffle flows can increase API volume.

## User Responsibilities

- Create Spotify Developer credentials.
- Create or choose the dedicated app-owned Spotify account.
- Authorize the app-owned account once during setup.
- Add local and production redirect URLs in the Spotify Developer dashboard.
- Confirm whether app-owned playlists should be public.
- Review test playlists and artist matches.

## Implementation Responsibilities

- Add Spotify API client code.
- Add artist search and top-track lookup.
- Add matching rules and warning reporting.
- Add OAuth setup route or one-time token capture command.
- Add environment variable documentation.
- Add playlist creation and track insertion.
- Add tests around matching, duplicate handling, empty results, and playlist payload construction.

## Related Pages

- [Project Overview](project_overview.md)
- [Development Stages](development_stages.md)
- [PWA Requirements](pwa_requirements.md)

