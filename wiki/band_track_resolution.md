# Band Track Resolution — As-Built Reference

This page documents the **offline pre-resolution system** that has been shipping since v0.5.4 (2026-05-17). It is the authoritative reference for how bands become Spotify tracks in this project.

The original design proposal lives at [raw/spotify_search_proposal.md](../raw/spotify_search_proposal.md). The shipped implementation diverged from that proposal in several places — those divergences are called out below.

## Why It Exists

Two production problems forced the design:

1. **17-hour Spotify shadow ban (2026-05-17).** Bursts of search calls during user sessions — even legitimate ones — tripped a prolonged 429 wall on the app's client credentials. No user could generate a playlist for most of a day.
2. **Incomplete results for obscure bands.** Single-page searches returned < 10 tracks for smaller festival acts; runtime pagination amplified the call count and made the rate-limit problem worse.

The fix: move **every** Spotify search call into a developer-run offline script. User sessions only ever hit `POST /me/playlists` and `POST /playlists/{id}/items`.

## Component Map

```
scripts/resolve_lineup.py        ← run offline by dev; talks to Spotify /search
wacken_playlist/services/spotify.py
    SpotifyClient.search_artist
    SpotifyClient.search_tracks_by_artist    ← artist:"NAME" qualifier
    SpotifyClient.search_tracks_plain        ← plain-text fallback
    SpotifyClient.get_top_tracks             ← two-strategy wrapper (legacy name kept)
    SpotifyClient.create_playlist            ← runtime path; no /search calls
wacken_playlist/services/playlist.py
    PlaylistBuilder.build_preview            ← reads pre-resolved JSON only
    PlaylistBuilder.build_and_create         ← filter + create_playlist; honors excluded_uris
wacken_playlist/models.py
    Track, Band (with tracks/spotify_id/track_count/unresolved)
wacken_playlist/data/lineups/
    wacken_2026.json                         ← resolved truth
    artist_overrides.json                    ← manual band-name → artist-ID map
    unresolved_bands.json                    ← audit log + permanently_unresolved flags
```

## Data Schema

`wacken_2026.json` per-band record:

```json
{
  "name": "Rammstein",
  "spotify_id": "6wWVKhxIU2cEi0K81v7HvP",
  "tracks": [
    { "uri": "spotify:track:abc123", "name": "Du Hast" },
    ...
  ],
  "track_count": 10,
  "resolved_at": "2026-05-17",
  "unresolved": false
}
```

`artist_overrides.json` (currently **14 entries** as of 2026-05-17):

```json
{
  "overrides": { "<band name>": "<spotify_artist_id>", ... },
  "low_track_count_notes": { "<band name>": "<reason>" },
  "updated_at": "2026-05-17"
}
```

`unresolved_bands.json` entries gain an optional `"permanently_unresolved": true` flag plus a `"note"` explaining why (Wacken-local act, house DJ, tribute band with no Spotify presence). `--retry-unresolved` skips these.

## Two-Strategy Search (v0.5.5)

The resolver runs **two** queries per band and merges the results:

1. **`artist:"NAME"` qualifier** — exact-artist match. Post-Feb-2026 Spotify caps this at ~5 results per page.
2. **Plain-text `NAME` search** — wider net, paginates further. Catches remixes, live versions, and compilations.

Results from both are:
- **Deduplicated by track URI.**
- **Filtered by Spotify artist ID** — only tracks where the band is the primary (or only) artist on the target ID are kept.
- **Capped at 10** per band.

Filtering by artist ID (not by name string) eliminates three classes of bug:
- Case/capitalization mismatches ("Corrosion of Conformity" vs "Corrosion Of Conformity").
- Generic-name collisions (Europe, Focus, Saxon, Phantom).
- Covers and compilations attributed to a different artist on Spotify.

## Artist-ID Override Path

For generic names, `search_artist` cannot reliably pick the correct top hit. The resolver consults `artist_overrides.json` **before** calling `search_artist`. If the band name is present, the override ID is used directly and the search step is skipped.

Override IDs are looked up manually on `open.spotify.com/artist/<ID>` and verified before being committed.

Current overrides cover bands like: The Haunted, Mantar, Craft, Mr. Hurley Und Die Pulveraffen, The Other, Focus, Trold, Krogi, Phantom, 9mm Headshot, E.N.D., Force, Novelization, Maschine.

## Permanently-Unresolved Bands

Some Wacken acts have **no** Spotify presence — house DJs, festival firefighter parades, tribute bands. Marking them `"permanently_unresolved": true` in `unresolved_bands.json` (with a `"note"` field) makes `--retry-unresolved` skip them so they don't waste API calls on every retry pass.

Currently flagged: Wacken Firefighters, Ballroom DJ Team, Blood Fire Death, Cowgirls From Hell.

## Retry Modes

| Command | What it does |
|---|---|
| `py scripts/resolve_lineup.py` | Full lineup resolution from scratch. Slow; intended for new years. |
| `py scripts/resolve_lineup.py --retry-unresolved` | Re-resolve every band in `unresolved_bands.json` that isn't flagged `permanently_unresolved`. Uses overrides. |
| `py scripts/resolve_lineup.py --retry-unresolved --below-threshold-only` | Same as above, but skip bands with zero tracks — only re-resolve those with 1–4. |

> **Not yet implemented:** a `--retry-low-count <N>` flag that targets bands already in `wacken_2026.json` with `track_count < N`. The track top-up plan ([wiki/track_topup_plan.md](track_topup_plan.md)) calls for adding this.

## Runtime Behavior (User Sessions)

`PlaylistBuilder.build_preview` reads pre-resolved data only. No Spotify calls.

`PlaylistBuilder.build_and_create`:
1. Calls `build_preview` to assemble matched / unmatched lists from the JSON.
2. Filters out any URIs in `request.excluded_uris` (the "yellow X" track-removal feature added in v0.5.4).
3. Raises `NoMatchedTracksError` if no URIs remain.
4. Calls `SpotifyClient.create_playlist(name, uris, public=True)` — the only Spotify call.

Result: **2–3 Spotify API calls per user session** (create + 1–2 add-items chunks of 100), regardless of how many bands the user picks.

## Divergences from `raw/spotify_search_proposal.md`

The proposal predates the implementation. Where they differ, this page is authoritative.

| Proposal said | Actually shipped |
|---|---|
| Replace `get_top_tracks`; drop the method name. | `get_top_tracks` kept (semantics changed) and now wraps the two-strategy search. `search_tracks_by_artist` and `search_tracks_plain` exist alongside it. |
| Single `search_tracks_by_artist` with offset loop. | Two-strategy search + URI dedup + artist-ID filter + `_recover_tracks` last-resort path. |
| No mention of overrides. | `artist_overrides.json` is consulted before `search_artist`. |
| No mention of permanently-unresolved bands. | `permanently_unresolved` flag added to `unresolved_bands.json`. |
| `Band` has `tracks: tuple[Track, ...]`, `track_count`, `unresolved`. | Same — shipped as proposed. |
| No `excluded_uris` on `PlaylistRequest`. | Added to support the yellow-X track-removal UX (v0.5.4). |

## When to Re-Run the Resolver

| Trigger | Action |
|---|---|
| New band added to lineup | Re-run targeted (or full `--retry-unresolved` if added to unresolved file). |
| Full lineup refresh / new year | New `wacken_YYYY.json`, full resolution run. |
| Generic-name band picks the wrong artist | Add an entry to `artist_overrides.json`, then `--retry-unresolved`. |
| Shadow ban during a retry | Stop. Restore `wacken_2026.json` from HEAD. Wait for ban to clear. Probe with **one** search call before resuming. |

## Known Pitfalls

- **Always probe Spotify before a batch retry.** A hidden 429 will silently wipe good track data — this happened on the first override retry and is now a hard rule in memory.
- **The `artist:"NAME"` qualifier cap.** Post-Feb-2026 Spotify caps this at ~5 results per page. Pagination on this leg is mostly pointless beyond ~2 pages; the plain-text leg does the heavy lifting.
- **Idempotence on full bands.** A re-resolution pass on a band already at 10 tracks should return the same 10. The track top-up plan treats this as a success criterion.

## Related

- [wiki/spotify_integration.md](spotify_integration.md) — high-level Spotify auth + endpoint notes.
- [wiki/stage5_deployment.md](stage5_deployment.md) — runtime context (zero search calls per session).
- [wiki/track_topup_plan.md](track_topup_plan.md) — staged retry plan for low-track bands.
- [raw/spotify_search_proposal.md](../raw/spotify_search_proposal.md) — original design rationale.
