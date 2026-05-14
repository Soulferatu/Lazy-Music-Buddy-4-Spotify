# PWA Requirements

Purpose: capture the installable app, mobile, and production-readiness requirements for Lazy Music Buddy. Source: [Start.MD](../Start.MD).

## Product Intent

Lazy Music Buddy should work as a browser-first web app that can also be saved as an app on a phone.

The PWA work should come after the first app-owned playlist flow is usable, so polish is applied to a real workflow instead of a placeholder screen.

## Baseline Requirements

- Responsive HTML, CSS, and JavaScript served by Flask.
- Mobile-safe layout.
- Web app manifest.
- Service worker.
- Theme color.
- Installable app icons.
- Loading, success, warning, and error states.
- Local installability check.
- Manual phone or mobile browser testing.

## Stage 4 Scope

Stage 4 is the first PWA polish milestone.

Order of work:

1. Add PWA manifest.
2. Add service worker.
3. Add icons and theme color.
4. Polish mobile layout.
5. Add loading, success, warning, and error states.
6. Perform a local installability check.

Completion gate:

The app-owned playlist flow is usable on desktop and mobile, and the app has basic PWA install support.

## Deployment Relationship

Full production confidence waits until Stage 9, when the app has a hosted URL and production settings.

Stage 9 includes:

- Choosing a hosting provider.
- Configuring production environment variables.
- Adding production Spotify redirect URLs.
- Deploying the app.
- Testing Spotify flows from the hosted URL.
- Testing PWA install behavior.
- Reviewing the final mobile UI.
- Adding production security headers and logging.

## Risks

- Service worker caching can accidentally serve stale files.
- Mobile browsers differ in install behavior.
- Hosted Spotify OAuth requires exact production redirect URLs.
- Production secrets must be handled carefully.
- A hosting target chosen too early or too late can create extra migration work.

## User Responsibilities

- Test the app on a phone or mobile browser.
- Confirm app name and icon direction.
- Review success and error messaging.
- Choose hosting provider when deployment begins.
- Provide production hosting access and environment variables when needed.

## Implementation Responsibilities

- Add manifest and service worker files.
- Add app icons or placeholders.
- Improve responsive layout.
- Add UI states around Spotify calls.
- Document known local PWA limitations.
- Verify installability during local and production checks.
- Add deployment documentation and release checklist.

## Related Pages

- [Project Overview](project_overview.md)
- [Development Stages](development_stages.md)
- [Spotify Integration](spotify_integration.md)

