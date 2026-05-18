# Track Top-Up Plan — Handling Bands Below the 10-Track Cap

**Status (2026-05-18):** **Steps 1–5 effectively done (v0.5.8). 136/169 bands at 10-track cap.** Total 1,234 → 1,485 tracks.

### Resolver hardening done this session
- `--retry-low-count N` flag added to [scripts/resolve_lineup.py](../scripts/resolve_lineup.py); idempotent; honors `permanently_unresolved` from `unresolved_bands.json`.
- `MAX_PAGES_ARTIST` bumped 3 → 5 after the Limit diagnostic showed pages 3–4 of the `artist:"NAME"` qualifier returning tracks the resolver was missing.
- **Case-insensitive title dedup** added to `_collect_tracks_for_artist`. Spotify often returns multiple URIs for the same song (single / album / compilation / remaster); dedup-by-URI alone let release-variant duplicates slip through.

### Findings during execution
- **Global dedup sweep** on `wacken_2026.json` found **40 bands** with title-duplicate tracks inflating their counts. Biggest drops: Evil Jared 7→4, Arroganz/Alien Ant Farm/Goodnight Greatness 10→7. Re-fetch sweeps with the bumped pagination then pushed most of these up to 10.
- **Heavysaurus** (`6uyCfgv8FWIc2mifriVXqw`) — only 2 unique songs across 6 release URIs. Deduped to 2 tracks, flagged `permanently_unresolved`.
- **The Limit** (`3nV9wzwFVAOJAjiSeFvcaf`) — 6 → 9 unique tracks after the pagination bump + title dedup.
- **Name-collision casualties** — Minotaurus (`2Yye71KtHwVbox5ST6254N`) and Sacred Steel (`1YIOK7G8mxLZE6FhuSVqBy`) have correct artist IDs (the artists exist and previously had tracks captured), but Spotify's `artist:"NAME"` search now ranks a *different* artist with the same name as the top hit. The artist-ID filter correctly rejects → 0 fresh matches; the idempotent guard preserved the previously-captured 8 and 9 tracks. Adding more would require switching to `/v1/artists/{id}/albums` for affected bands — deferred (small payoff).
- **Evil Jared** — only 4 unique songs on Spotify after dedup. Likely real ceiling.
- **Electric Bassboy** — only 6 unique songs on Spotify after dedup. Likely real ceiling.

Diagnostic on Judas Priest disproved the plan's original theories — root cause of the 5-track plateau was stale data from an earlier resolver pass, not a resolver bug (see "Step 1a outcome" below).

This page is the handling guide for bands in `wacken_2026.json` whose `track_count` is below the 10-track cap. The catalogued plan with band-by-band tables lives in [Ten_song_fix.md](../Ten_song_fix.md); this page records **how to approach the work**, the pitfalls, and the decision points.

The cap itself (10 tracks per band) is intentional and stays. "Topping up" means moving bands from `< 10` to exactly `10`, not raising the cap.

## Current Distribution Snapshot

As of 2026-05-18 (v0.5.8, after full top-up + global dedup + re-fetch sweeps) — 169 bands, **1,485 tracks** (perfect would be 1,690):

| Tracks per band | # bands | Status |
|---:|---:|---|
| 10 | 136 | ✅ At cap (was 74) |
| 9  | 5   | ✅ Real ceilings / name-collision casualties |
| 8  | 7   | ✅ Real ceilings / name-collision casualties |
| 7  | 0   | ✅ All cleared (was 13) |
| 6  | 1   | Electric Bassboy — real ceiling (only 6 unique on Spotify) |
| 4  | 2   | Mantar, Evil Jared — real ceilings |
| 3  | 1   | 9mm Headshot — override staged |
| 2  | 3   | Cowgirls From Hell, Focus, **Heavysaurus** (`permanently_unresolved`) |
| 1  | 1   | Novelization — known 1-track ceiling |
| 0  | 13  | Deferred (overrides or `permanently_unresolved` staged) |
| 4  | 1  | Deferred (Mantar — likely true ceiling) |
| 3  | 1  | Deferred (9mm Headshot — override staged) |
| 2  | 2  | Deferred (Cowgirls From Hell, Focus) |
| 1  | 1  | Deferred (Novelization — known 1-track ceiling) |
| 0  | 13 | Deferred (12 have overrides staged; 1 `permanently_unresolved`) |

## Pre-Flight (mandatory before any batch retry)

1. **Probe Spotify with a single search call first.** A hidden 429 will silently wipe good track data — this is a hard rule in memory. Never run `--retry-unresolved` or any equivalent batch without a clean single-call 200 first.
2. **Confirm `artist_overrides.json` is in the expected state** (14 entries as of 2026-05-17).
3. **Snapshot `wacken_2026.json`** (git stash or filesystem copy) so a bad batch can be rolled back the same way it was after the first shadow-ban incident.

## Step 1a Outcome (2026-05-18) — Stale Data, Not a Resolver Bug

Both theories below turned out to be **wrong**. A diagnostic run of `_collect_tracks_for_artist` against Judas Priest (artist ID `2tRsMl4eGxwoNabM08Dm4I`) with current code returned **15 candidate tracks** just from the `artist:"NAME"` leg alone (3 pages × 5 results, every one kept by the artist-ID filter). The cap inside the function (`MAX_TRACKS = 10`) would land the band at exactly 10.

What was actually wrong: the 33 bands stuck at 5 tracks were written into `wacken_2026.json` during an earlier resolver pass with smaller pagination constants. Their `resolved_at` says 2026-05-17 (the v0.5.5 rollout day), so date alone didn't reveal it — but the data was effectively pre-v0.5.5. No code change to the resolution logic was needed; just re-running over those bands with the existing code fixed all 33.

**Lesson for Steps 2–5:** spending one diagnostic call before each batch is still worthwhile, but expect the same answer (stale data) unless the resolver itself changes between runs.

## Step 1a — Diagnose the "5-Track Plateau" Before Batching (historical)

33 of the bands at exactly 5 tracks are mainstream metal acts (Judas Priest, Sabaton, Powerwolf, Lamb Of God, Arch Enemy, Sepultura, Def Leppard, …). Their low count is almost certainly a **resolver artifact**, not real Spotify scarcity. Two plausible causes:

1. **Plain-text leg under-paginating.** Stage 4 raised the runtime `PlaylistBuilder` pagination to 5 pages, but the offline resolver path may not match. URI dedup + artist-ID filter then leaves exactly the 5 results from the `artist:"NAME"` leg.
2. **Artist-ID filter discarding compilation / "Various Artists" hits.** Correct behavior, but it lowers yield from the plain-text leg for popular acts that appear on many compilations.

**Run the resolver on one obvious case (e.g. Judas Priest) with verbose logging before batching.** The outcome decides the fix:

- If pagination → patch the offline path to mirror Stage 4's 5-page setting. Same fix lifts most of Steps 1–5 in one re-run.
- If filter over-discarding → tune the filter (accept tracks where the target artist is *any* listed artist, not strictly primary) and re-run.

## Step 1b — Run the Batch

The existing `--below-threshold-only` flag targets the `unresolved_bands.json` set, **not** the 5-track-in-main-file set. Two ways to address bands already in `wacken_2026.json`:

- **(Recommended)** Add a new flag, e.g. `--retry-low-count <N>`, that re-resolves any band in `wacken_2026.json` whose `track_count < N`. Steps 2–5 then become one-line invocations: `--retry-low-count 6`, `7`, `8`, `9`.
- Or a one-shot script that filters `wacken_2026.json` and calls the resolver's per-band function directly.

## Steps 2–5 — Repeat for 6, 7, 8, 9 Tracks

Same command, raise the threshold one step at a time. Doing them in **separate runs** (not a single `--retry-low-count 10`) keeps each batch small enough to roll back cleanly if Spotify starts throttling mid-run.

## After Each Step

- Commit `wacken_2026.json` only after spot-checking 2–3 bands per batch (open the URIs in a browser, confirm the artist).
- Bump `wacken_playlist/version.py` once per batch so the PWA cache busts.
- Update CLAUDE.md "Current Stage" with the new total and the count of `< 10`-track bands remaining.

## Returning to the Deferred Tail

With the resolver behavior understood from Steps 1–5:

1. Any override gaps surface (currently none — E.N.D. and Force are in `artist_overrides.json` as of 2026-05-17).
2. Run `--retry-unresolved` to pick up Novelization's and Maschine's single tracks.
3. Mark Novelization and Maschine `permanently_unresolved` once their 1 known track is captured.
4. Mantar at 4 tracks is likely a true Spotify ceiling — verify manually, then leave or flag.

## Success Criteria

- ≥ 90 % of the 5-track band batch reaches 10 tracks after Step 1.
- Each subsequent step (6, 7, 8, 9) reaches 10 for ≥ 90 % of its bands.
- **Idempotence:** no band that already had 10 tracks loses any.
- **No artist-ID drift:** spot-checks confirm the right artist for at least 2 bands per step.
- `version.py` bumped and CLAUDE.md + PHASES.md updated after each step.

## Rollback

If a retry batch damages `wacken_2026.json` (the shadow-ban scenario):

1. Stop the script immediately.
2. `git checkout HEAD -- wacken_playlist/data/lineups/wacken_2026.json`.
3. Wait until probing Spotify with a single search call returns a clean 200 before retrying.

## Related

- [Ten_song_fix.md](../Ten_song_fix.md) — band-by-band tables and execution plan.
- [wiki/band_track_resolution.md](band_track_resolution.md) — as-built resolver reference.
- [scripts/resolve_lineup.py](../scripts/resolve_lineup.py) — the resolver itself.
