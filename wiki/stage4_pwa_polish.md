# Stage 4 — First PWA Release Polish

**Completed:** 2026-05-16  
**Branch:** `stage4/pwa-polish`  
**Version bump:** `0.3.0-embers` → `0.4.0-pwa`

## Goal

Make the app-owned playlist flow pleasant on mobile and desktop before adding more features. No new Spotify functionality — purely UX, PWA compliance, and housekeeping.

## What Was Delivered

### Loading states (`app.js`, `i18n/*.json`, `styles.css`)

When the user clicks **Preview playlist** or **Create Spotify playlist**, the button immediately disables and relabels itself using new i18n keys:

| Key | EN | PT-BR |
|---|---|---|
| `preview_loading` | Looking up bands on Spotify… | Buscando bandas no Spotify… |
| `create_loading` | Creating your playlist… | Criando sua playlist… |

The `button:disabled` CSS rule (`opacity: 0.55; cursor: not-allowed; pointer-events: none`) prevents double-submits and provides visual feedback during the 2–5 second Spotify wait.

### Mobile auto-scroll to summary (`app.js`, `index.html`)

The `<aside class="summary">` now carries a `data-state` attribute (`idle` / `preview` / `result`) set server-side by Jinja2. On page load, if `data-state !== 'idle'` and the viewport is narrower than 920 px (the breakpoint where workspace columns stack), JS calls `summary.scrollIntoView({ behavior: 'smooth', block: 'start' })`. This saves the user from scrolling past 87 band tiles to see their result.

### Dynamic countdown (`app.js`, `index.html`)

The hardcoded "74 days" number was replaced with a JS-calculated countdown. The `<b id="countdown-days" data-target-date="2026-07-29">` element holds the target date as a data attribute; JS computes `Math.ceil((target - now) / msPerDay)` on each page load. Target: **2026-07-29** (Wednesday before Wacken opens Thursday July 30 — when the Infield / Holy Grounds opens for campers).

Countdown label and unit are also now i18n-aware:

| Key | EN | PT-BR |
|---|---|---|
| `countdown_label` | Holy Grounds in | Holy Grounds em |
| `countdown_unit` | days | dias |

### Stale copy fixed (`i18n/*.json`)

`ready_copy` previously read "This step stays local. Spotify search, warnings, and playlist creation begin in later stages." — which was no longer true since Stage 2. Updated to:

- EN: "Select the bands you want to hear and click 'Preview playlist' to see what Spotify has for each act."
- PT-BR: "Selecione as bandas que quer ouvir e clique em 'Pré-visualizar playlist' para ver o que o Spotify tem para cada artista."

### Apple PWA meta tags (`index.html`)

Added to `<head>` for Safari / iOS Add to Home Screen support:

```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="My W:O:A">
<link rel="apple-touch-icon" href="/static/icons/icon.png">
```

Without `apple-mobile-web-app-capable`, iOS Safari does not enter standalone mode when launched from the home screen. `black-translucent` lets the status bar overlay the `#141316` background for a full-bleed look.

### Manifest `scope` (`manifest.webmanifest`)

Added `"scope": "/"`. Without `scope`, some browsers default to the directory of `start_url`, which can cause out-of-scope navigation to open in the browser rather than the installed app shell.

### Service worker fix (`templates/service-worker.js`)

`self.skipWaiting()` was present in both the `install` and `activate` handlers. It is only meaningful in `install` (forces the new SW to take control immediately rather than waiting for all tabs to close). In `activate`, after `install` has already resolved, it is a no-op. Removed from `activate` to match the documented pattern.

## Known Local PWA Limitations

- **Chrome on localhost:** "Add to Home Screen" / install banner requires HTTPS in production. Chrome may suppress the prompt on `http://localhost` but the flow still works from the hosted URL (Stage 9).
- **Safari on iOS:** Requires the user to manually tap Share → Add to Home Screen. There is no automatic install prompt on iOS regardless of deployment.
- **Firefox on Android:** Supports PWA install but the A2HS UI differs from Chrome. Behavior is correct but visually different.
- **Service worker cache on dev:** The SW caches assets aggressively. When iterating locally, always open DevTools → Application → Service Workers → Unregister, or use incognito mode to see the latest version. A `version.py` bump is the canonical way to bust the cache in production.
- **Offline support:** The current fetch strategy is network-first with cache fallback. The app requires Spotify API access to function; offline mode returns the cached shell but cannot create playlists.

## Files Changed

| File | Change |
|---|---|
| `wacken_playlist/i18n/en.json` | Added `preview_loading`, `create_loading`, `countdown_label`, `countdown_unit`; fixed `ready_copy` |
| `wacken_playlist/i18n/pt-BR.json` | Same in Portuguese |
| `wacken_playlist/templates/index.html` | Apple PWA meta tags; `id`/`data-target-date` on countdown `<b>`; `data-i18n` on countdown label/unit; `data-state` on `<aside class="summary">` |
| `wacken_playlist/static/js/app.js` | Dynamic countdown; loading states on preview and create form submit; mobile auto-scroll |
| `wacken_playlist/static/css/styles.css` | `button:disabled` style |
| `wacken_playlist/static/manifest.webmanifest` | Added `"scope": "/"` |
| `wacken_playlist/templates/service-worker.js` | Removed redundant `self.skipWaiting()` from activate handler |
| `wacken_playlist/version.py` | Bumped `APP_VERSION` to `"0.4.0-pwa"` |
