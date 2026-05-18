# Track Top-Up Plan — Handling Bands Below the 10-Track Cap

**Status (2026-05-18):** documented, **not executed**. Blocked on the same active Spotify shadow ban as the override retry.

This page is the handling guide for bands in `wacken_2026.json` whose `track_count` is below the 10-track cap. The catalogued plan with band-by-band tables lives in [Ten_song_fix.md](../Ten_song_fix.md); this page records **how to approach the work**, the pitfalls, and the decision points.

The cap itself (10 tracks per band) is intentional and stays. "Topping up" means moving bands from `< 10` to exactly `10`, not raising the cap.

## Current Distribution Snapshot

As of 2026-05-17 (v0.5.5 + 14 staged overrides) — 169 bands, 1,234 tracks (perfect would be 1,690):

| Tracks per band | # bands | Plan step |
|---:|---:|---|
| 10 | 74 | Leave alone |
| 9  | 8  | Step 5 |
| 8  | 8  | Step 4 |
| 7  | 13 | Step 3 |
| 6  | 15 | Step 2 |
| 5  | 33 | **Step 1 — start here** |
| 4  | 1  | Deferred (Mantar — likely true ceiling) |
| 3  | 1  | Deferred (9mm Headshot — override staged) |
| 2  | 2  | Deferred (Cowgirls From Hell, Focus) |
| 1  | 1  | Deferred (Novelization — known 1-track ceiling) |
| 0  | 13 | Deferred (12 have overrides staged; 1 `permanently_unresolved`) |

## Pre-Flight (mandatory before any batch retry)

1. **Probe Spotify with a single search call first.** A hidden 429 will silently wipe good track data — this is a hard rule in memory. Never run `--retry-unresolved` or any equivalent batch without a clean single-call 200 first.
2. **Confirm `artist_overrides.json` is in the expected state** (14 entries as of 2026-05-17).
3. **Snapshot `wacken_2026.json`** (git stash or filesystem copy) so a bad batch can be rolled back the same way it was after the first shadow-ban incident.

## Step 1a — Diagnose the "5-Track Plateau" Before Batching

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
