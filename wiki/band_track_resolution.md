# Band Track Resolution — As-Built Reference

This page documents the **offline pre-resolution system** shipping since v0.5.4 (2026-05-17) and rewritten for the library refactor in v0.5.9 (Phase 5+6). It is the authoritative reference for how bands become Spotify tracks in this project.

The original design proposal lives at [raw/spotify_search_proposal.md](../raw/spotify_search_proposal.md). The shipped implementation diverged from that proposal in several places — those divergences are called out below.

## Why It Exists

Two production problems forced the design:

1. **17-hour Spotify shadow ban (2026-05-17).** Bursts of search calls during user sessions — even legitimate ones — tripped a prolonged 429 wall on the app's client credentials. No user could generate a playlist for most of a day.
2. **Incomplete results for obscure bands.** Single-page searches returned < 10 tracks for smaller festival acts; runtime pagination amplified the call count and made the rate-limit problem worse.

The fix: move **every** Spotify search call into a developer-run offline script. User sessions only ever hit `POST /me/playlists` and `POST /playlists/{id}/items`.

## Component Map (post Phase 5+6)

```
scripts/resolve_lineup.py        ← run offline by dev; talks to Spotify /search + /artists/{id}/albums
                                  Canonical writer for data/library/spotify_tracks.json.
wacken_playlist/services/spotify.py
    SpotifyClient.get_client_credentials_token
    SpotifyClient.search_artist
    SpotifyClient.search_tracks_by_artist    ← artist:"NAME" qualifier
    SpotifyClient.search_tracks_plain        ← plain-text fallback
    SpotifyClient.create_playlist            ← runtime path; no /search calls
wacken_playlist/services/playlist.py
    PlaylistBuilder.build_preview            ← reads pre-resolved library only
    PlaylistBuilder.build_and_create         ← filter + create_playlist; honors excluded_uris
wacken_playlist/library.py
    LibraryRepository                        ← typed reads against data/library/*.json
wacken_playlist/lineup.py
    LineupRepository                         ← reads thin lineup; joins through LibraryRepository
wacken_playlist/models.py
    Track, Band, ArtistRecord
wacken_playlist/data/library/
    artists.json                             ← canonical artist registry (name, aliases, mbid, override_source, notes)
    spotify_tracks.json                      ← per-artist track cache (the resolver writes this)
    unresolved.json                          ← bands with no Spotify ID at all (empty today; schema reserved)
    setlists.json                            ← RESERVED for Stage 6 (setlist.fm)
wacken_playlist/data/lineups/
    wacken_2026.json                         ← thin pointer list: { year, source_urls, notes, bands: [spotify_ids], unresolved_names }
```

## Data Schema (post Phase 5+6)

**`data/library/artists.json`** — canonical artist registry, keyed by Spotify artist ID:

```json
"6wWVKhxIU2cEi0K81v7HvP": {
  "name": "Rammstein",
  "aliases": [],
  "mbid": null,
  "override_source": null,
  "notes": null
}
```

Entries whose `override_source` is non-null (currently `"manual_2026-05-17"`) were curated by hand because Spotify search picks the wrong artist for the project's canonical name. The resolver doesn't use this field for resolution itself — the artist ID is the join key — but it serves as documentation and lets future tooling distinguish hand-curated bands.

**`data/library/spotify_tracks.json`** — per-artist track cache, keyed by Spotify artist ID:

```json
"6wWVKhxIU2cEi0K81v7HvP": {
  "tracks": [
    { "uri": "spotify:track:...", "name": "Du Hast" },
    ...
  ],
  "track_count": 10,
  "resolved_at": "2026-05-19",
  "permanently_unresolved": false   // optional; only present for known-thin catalogs
}
```

Five artists carry `permanently_unresolved: true` today (Ballroom DJ Team, Blood Fire Death, Cowgirls From Hell, Wacken Firefighters, Heavysaurus). The resolver skips them on every retry mode.

**`data/lineups/wacken_2026.json`** — thin pointer list:

```json
{
  "year": 2026,
  "source_urls": [...],
  "notes": {
    "withdrawals": [...],
    "non_band_entries": [...]
  },
  "bands": ["1biWH85uIGqR8Nj7oKU5J9", "0hYxXnnFEBBK8JDab4lIEM", ...],
  "unresolved_names": []
}
```

## Two-Strategy Search + Albums Fallback

For each artist in the lineup the resolver runs:

1. **`artist:"NAME"` qualifier** — exact-artist match. Post-Feb-2026 Spotify caps this at ~5 results per page. Up to 5 pages (`MAX_PAGES_ARTIST`).
2. **Plain-text `NAME` search** — wider net, paginates further. Up to 5 pages (`MAX_PAGES_PLAIN`). Catches remixes, live versions, and compilations.

Results from both are:
- **Deduplicated by track URI.**
- **Deduplicated by case-insensitive title** — Spotify often returns the same song under multiple URIs (single / album / compilation / remaster).
- **Filtered by Spotify artist ID** — only tracks where the target artist appears are kept.
- **Capped at 10** (`MAX_TRACKS`) per band.

**Albums fallback** (added in v0.5.9): when search returns **zero** tracks tagged to the artist ID — typically because the project's canonical name diverges from the artist's Spotify display name — the resolver walks `/v1/artists/{id}/albums` (`album` + `single` groups) and pulls tracks from each album via `/v1/albums/{id}/tracks`, then applies the same artist-ID filter + URI/title dedup + 10-cap. This handles cases like 9mm Headshot (Spotify display name "9MM"). Without the fallback those artists would unresolve on every pass.

Filtering by artist ID (not by name string) eliminates four classes of bug:
- Case/capitalization mismatches ("Corrosion of Conformity" vs "Corrosion Of Conformity").
- Generic-name collisions (Europe, Focus, Saxon, Phantom).
- Covers and compilations attributed to a different artist on Spotify.
- Project canonical name ≠ Spotify display name (resolved by the albums fallback).

## Hand-Curated Artists (formerly "overrides")

Before Phase 5+6, generic-name disambiguation lived in a separate `artist_overrides.json` keyed by band name. After Phase 5+6 there is no separate overrides file — the lineup file already contains the (curated) Spotify artist ID per band, and `artists.json` keeps that ID's canonical name + the `override_source` marker for documentation.

Adding a new generic-name band:

1. Look up the correct artist ID at `open.spotify.com/artist/<ID>` and verify it's the right band (check albums, country, genre).
2. Add the ID to `wacken_playlist/data/lineups/wacken_YYYY.json` `bands` array.
3. Add an entry to `wacken_playlist/data/library/artists.json` with the canonical name and (for generic names) `override_source: "manual_<YYYY-MM-DD>"`.
4. Run `py scripts/resolve_lineup.py --retry-unresolved` (or full resolution) to populate the tracks.

## Permanently-Unresolved Bands

Some Wacken acts have **no** usable Spotify catalog — house DJs, festival firefighter parades, tribute bands, and one band (Heavysaurus) whose Spotify entry has only 2 unique recordings. Marking them with `permanently_unresolved: true` in `data/library/spotify_tracks.json` makes every retry mode skip them so they don't waste API calls or churn.

Currently flagged: Wacken Firefighters, Ballroom DJ Team, Blood Fire Death, Cowgirls From Hell, Heavysaurus.

## Resolver Modes

| Command | What it does |
|---|---|
| `py scripts/resolve_lineup.py` | Full resolution — iterate every artist ID in the lineup (alphabetical), refresh tracks. ~8–10 min for 169 bands. |
| `py scripts/resolve_lineup.py --test` | Smoke run on the first 10 artists. ~30 s. Use to validate API access. |
| `py scripts/resolve_lineup.py --resume-from-band N` | Resume a full run from band N (1-indexed in alphabetical order). |
| `py scripts/resolve_lineup.py --retry-unresolved` | Re-resolve every artist currently below 5 tracks (excluding permanently_unresolved). |
| `py scripts/resolve_lineup.py --retry-unresolved --below-threshold-only` | Same, but skip 0-track artists too (only 1–4). |
| `py scripts/resolve_lineup.py --retry-low-count N` | Re-resolve only artists at exactly N tracks. Idempotent — keeps the previous entry if the pass doesn't improve. |

## Safety: Never Overwrite Nonzero With Zero (v0.5.9)

The resolver's `_resolve_ids` core loop refuses to write a 0-track result over an entry that previously had nonzero tracks. Spotify intermittently returns 429 (rate limit) or 502 (gateway error) during long runs; without this guard, a transient failure late in the run would silently destroy good track data.

The patch landed after a failed full run during Phase 5+6 cutover (2026-05-19): bands 161–169 hit a 429 wall and were written as 0-track entries, costing ~450 tracks across 53 bands before the safeguard backup was restored. The pattern: probe first, retry mode + safety guard, never trust a single pass to be lossless.

## Runtime Behavior (User Sessions)

`PlaylistBuilder.build_preview` reads pre-resolved data only via `LineupRepository` → `LibraryRepository`. No Spotify calls.

`PlaylistBuilder.build_and_create`:
1. Calls `build_preview` to assemble matched / unmatched lists from the library.
2. Filters out any URIs in `request.excluded_uris` (the "yellow X" track-removal feature added in v0.5.4).
3. Raises `NoMatchedTracksError` if no URIs remain.
4. Calls `SpotifyClient.create_playlist(name, uris, public=True)` — the only Spotify call.

Result: **2–3 Spotify API calls per user session** (create + 1–2 add-items chunks of 100), regardless of how many bands the user picks.

## When to Re-Run the Resolver

| Trigger | Action |
|---|---|
| New band added to lineup | Edit `wacken_YYYY.json` + `artists.json`; run `--retry-unresolved` (will catch any artist below threshold including the new one). |
| Full lineup refresh / new year | New `wacken_YYYY.json` + entries in `artists.json`; full resolution run. |
| Generic-name band picks the wrong artist | Verify the correct artist ID, edit it in the lineup + `artists.json`, then `--retry-unresolved`. |
| Shadow ban during a retry | Stop. The safety guard means library data is preserved automatically. Wait for the ban to clear. Re-run when the probe call succeeds. |

## Known Pitfalls

- **Always probe Spotify before a batch retry.** A hidden 429 will cap every search to zero. The resolver does this automatically (`_probe_spotify`) at the start of every batch and aborts cleanly if the probe fails.
- **Never overwrite nonzero with zero.** Enforced in `_resolve_ids` — a transient API failure won't destroy good track data.
- **The `artist:"NAME"` qualifier cap.** Post-Feb-2026 Spotify caps this at ~5 results per page. Pagination on this leg is mostly pointless beyond ~2 pages; the plain-text leg does the heavy lifting.
- **Idempotence on full bands.** A re-resolution pass on a band already at 10 tracks should return the same 10. `--retry-low-count` treats no-improvement as a no-op.
- **Albums-fallback noise.** The fallback walks `album` + `single` only — it skips `compilation` and `appears_on` to avoid pulling in tribute / cover noise. Still, if a label re-releases a single under a new album, the fallback may surface release-variant duplicates; the title-dedup catches them.

## Divergences from `raw/spotify_search_proposal.md`

The proposal predates the implementation. Where they differ, this page is authoritative.

| Proposal said | Actually shipped |
|---|---|
| Replace `get_top_tracks`; drop the method name. | `get_top_tracks` kept (semantics changed) and now wraps the two-strategy search. `search_tracks_by_artist` and `search_tracks_plain` exist alongside it. |
| Single `search_tracks_by_artist` with offset loop. | Two-strategy search + URI dedup + title dedup + artist-ID filter + `/artists/{id}/albums` fallback. |
| No mention of overrides. | Hand-curated artist IDs live in `wacken_YYYY.json` + `artists.json` (`override_source` marker). Previously a separate file. |
| No mention of permanently-unresolved bands. | `permanently_unresolved` flag on `spotify_tracks.json` entries. |
| `Band` has `tracks: tuple[Track, ...]`, `track_count`, `unresolved`. | Same — shipped as proposed. |
| No `excluded_uris` on `PlaylistRequest`. | Added to support the yellow-X track-removal UX (v0.5.4). |
| Single lineup file holds bands + tracks. | Lineup split: lineup file holds only pointer list; library files hold artist registry + track cache (Phase 5+6 of the library refactor). |

## Related

- [wiki/library_refactor.md](library_refactor.md) — refactor that produced the current layout.
- [wiki/spotify_integration.md](spotify_integration.md) — high-level Spotify auth + endpoint notes.
- [wiki/stage5_deployment.md](stage5_deployment.md) — runtime context (zero search calls per session).
- [wiki/track_topup_plan.md](track_topup_plan.md) — staged retry plan for low-track bands (historical; track top-up landed in v0.5.8).
- [raw/spotify_search_proposal.md](../raw/spotify_search_proposal.md) — original design rationale.
