# Ten_song_fix — Plan to top every band up to 10 Spotify tracks

> **Status (2026-05-18):** **Steps 1–5 effectively done** (v0.5.8). 136/169 bands at 10-track cap (was 74). Total 1,234 → 1,485 tracks. Resolver hardened: `MAX_PAGES_ARTIST` 3→5, case-insensitive title dedup, `--retry-low-count N` flag (idempotent, honors `permanently_unresolved`). Global title-dedup sweep revealed 40 bands had release-variant duplicates inflating counts. **Heavysaurus** flagged `permanently_unresolved`. Remaining below-cap bands are real Spotify ceilings, name-collision casualties (Minotaurus, Sacred Steel — search ranks a different artist first), or already deferred.
> Diagnostic outcome (recorded for the wiki): the "5-track plateau" was **stale data**, not a resolver bug. The current resolver yields 15+ candidate tracks for major artists; the low counts were written by a previous pass with smaller pagination. Re-running with the existing code fixes it.
> For the handling guide and pitfalls, see [wiki/track_topup_plan.md](wiki/track_topup_plan.md). For the as-built resolver this plan operates on, see [wiki/band_track_resolution.md](wiki/band_track_resolution.md).

Source: [wacken_playlist/data/lineups/wacken_2026.json](wacken_playlist/data/lineups/wacken_2026.json) as resolved on 2026-05-17 (v0.5.5 + staged overrides).

**Cap:** the offline resolver in [scripts/resolve_lineup.py](scripts/resolve_lineup.py) tops out at 10 tracks per band on purpose. "Topping up" means moving as many bands as possible from `< 10` to exactly `10`, not raising the cap.

**Total today:** 169 bands, 1,234 tracks. Perfect would be 1,690.

---

## Distribution snapshot

| Tracks | # bands | Status in this plan |
|---:|---:|---|
| 10 | 136 (was 74) | ✅ Done |
| 9  | 5 (was 8)  | ✅ Done — real ceilings or name-collision casualties (I See Red, Nergal, Sacred Steel, Speak In Whispers, The Limit) |
| 8  | 7 (was 8)  | ✅ Done — real ceilings or name collisions (Cursed Abyss, Europe, Midhaven, Minotaurus, President, Sinamort, Wüstenberg) |
| 7  | 0 (was 13) | ✅ Step 3 done — all 13 cleared (post-dedup the 4 stragglers all hit 10) |
| 6  | 1 (was 15) | ✅ Electric Bassboy is the only one left; only 6 unique songs on Spotify |
| 5  | 0 (was 33) | ✅ Step 1 done — all 33 → 10 |
| 4  | 2  | Deferred (Mantar — known low avail; **Evil Jared** — only 4 unique songs after dedup) |
| 3  | 1  | Deferred (9mm Headshot — override staged) |
| 2  | 3  | Deferred (Cowgirls From Hell, Focus, **Heavysaurus** — `permanently_unresolved`) |
| 1  | 1  | Deferred (Novelization) |
| 0  | 13 | Deferred (most have overrides or `permanently_unresolved` staged) |

---

## Step 1 — 33 bands at 5 tracks (highest leverage)

Many of these are mainstream metal acts that obviously have > 5 tracks on Spotify (Judas Priest, Sabaton, Powerwolf, Lamb Of God, Def Leppard, Arch Enemy, Sepultura, Airbourne, Alestorm, Black Label Society…). Their low count is almost certainly a **resolver pagination / dedup artifact**, not a real Spotify scarcity. Expect a very high success rate here.

| Band |
|---|
| Ad Infinitum |
| Airbourne |
| Alestorm |
| Alien Ant Farm |
| Angelus Apatrida |
| Any Given Day |
| Arch Enemy |
| Black Label Society |
| Bleed From Within |
| Crematory |
| Def Leppard |
| Employed To Serve |
| Future Palace |
| H-Blockx |
| Hatebreed |
| Judas Priest |
| Kadavar |
| Kim Dracula |
| Kittie |
| Lacuna Coil |
| Lamb Of God |
| Nothing More |
| Of Mice & Men |
| Orbit Culture |
| Paradise Lost |
| Powerwolf |
| Sabaton |
| Sepultura |
| The Butcher Sisters |
| The Hardkiss |
| Thrown |
| Thundermother |
| Vended |

## Step 2 — 15 bands at 6 tracks

| Band |
|---|
| Animals As Leaders |
| Cruachan |
| Dubioza Kolektiv |
| Fit For An Autopsy |
| Guilt Trip |
| Heavysaurus |
| Life Of Agony |
| Manntra |
| Misery Index |
| Our Promise |
| Running Wild |
| Sagenbringer |
| Savatage |
| The Limit |
| Wytch Hazel |

## Step 3 — 13 bands at 7 tracks

| Band |
|---|
| Alcest |
| Bear McCreary |
| Blood Command |
| Castle Rat |
| Electric Bassboy |
| Evil Jared |
| Faun |
| Firespawn |
| Hardline |
| Kupfergold |
| Paleface Swiss |
| Vreid |
| Year Of The Goat |

## Step 4 — 8 bands at 8 tracks

| Band |
|---|
| Deafheaven |
| Kärbholz |
| Metaklapa |
| Municipal Waste |
| Pig Destroyer |
| President |
| Saviourself |
| Triptykon |

## Step 5 — 8 bands at 9 tracks

| Band |
|---|
| Anaal Nathrakh |
| Emperor |
| Grand Magus |
| Heartless Human Harvest |
| Midhaven |
| Rose Tattoo |
| Sinamort |
| The Gathering |

---

## Deferred — handled later

Per [CLAUDE.md](CLAUDE.md) and the v0.5.5 / override notes in [PHASES.md](PHASES.md):

### Below threshold (1–4 tracks)
- **Mantar (4)** — flagged in CLAUDE.md as genuinely low-availability on Spotify. May be a true ceiling.
- **9mm Headshot (3)** — override staged in `artist_overrides.json` as `9MM`. Awaits retry after the active Spotify shadow ban clears.
- **Cowgirls From Hell (2)** — flagged `permanently_unresolved` (Wacken-local / tribute style act, no Spotify presence beyond what's already captured). PHASES.md Stage 5 note.
- **Focus (2)** — generic name; override staged (correct Spotify artist ID added to `artist_overrides.json`). Awaits retry.
- **Novelization (1)** — PHASES.md notes Novelization has **only 1 song on Spotify**. To be marked `permanently_unresolved` after the retry confirms that single track.

### Zero tracks
All 13 of these are either already covered by a staged override or already flagged `permanently_unresolved`:

| Band | Status per CLAUDE.md / PHASES.md |
|---|---|
| Ballroom DJ Team | `permanently_unresolved` (house DJ act) |
| Blood Fire Death | `permanently_unresolved` (Wacken-local / tribute) |
| Craft | Override staged in `artist_overrides.json` |
| E.N.D. | Override staged in `artist_overrides.json` (added 2026-05-17) |
| Force | Override staged in `artist_overrides.json` (added 2026-05-17) |
| Krogi | Override staged as `EVIL JARED x KROGI` |
| Maschine | Override staged (Dieter "Maschine" Birr); **only 1 song on Spotify**, will be flagged `permanently_unresolved` after retry captures it |
| Mr. Hurley Und Die Pulveraffen | Override staged |
| Phantom | Override staged as `Phantom G.D.L` |
| The Haunted | Override staged |
| The Other | Override staged |
| Trold | Override staged |
| Wacken Firefighters | `permanently_unresolved` (Wacken-local) |

All 13 zero-track bands are now either covered by a staged override or flagged `permanently_unresolved`. No open override gaps remain — execution is blocked only on the Spotify shadow ban clearing.

---

## Why so many well-known bands are stuck at 5

Mainstream bands at exactly 5 is suspicious. Likely causes inside [scripts/resolve_lineup.py](scripts/resolve_lineup.py)::`_collect_tracks_for_artist`:

1. **Post-Feb-2026 Spotify cap** — the `artist:"NAME"` qualifier returns ≤ 5 results per page (documented in CLAUDE.md "Band Track Resolution Strategy").
2. **Plain-text leg under-paginating** — Stage 4 raised the *runtime* `PlaylistBuilder` pagination to 5 pages, but the *offline* resolver path may not match. If the plain-text leg stops after the first page, deduplication by URI plus the artist-ID filter can easily leave just 5 unique tracks for the most popular artists (where Spotify returns lots of duplicate hits / compilation appearances).
3. **Artist-ID filter discarding "Various Artists" tribute / compilation hits** — correct behavior, but it lowers the yield from the plain-text leg.

Step 1's first job is to confirm which of those it is before running anything in bulk.

---

## Execution plan

### Pre-flight (before any step)
1. **Probe Spotify first.** Memory rule from prior session: a bare `--retry-unresolved` during a shadow ban silently wiped good data once already. Run a single search call (one band) and confirm a clean 200 before doing anything batch.
2. Confirm `artist_overrides.json` is in the state CLAUDE.md describes (14 entries). If a retry happened in between, refresh from disk.
3. Snapshot `wacken_2026.json` (git stash / copy) so a bad batch can be rolled back the same way it was after the previous shadow ban.

### Step 1a — diagnose the "5-track plateau"
Before running a bulk retry on 33 bands, run the resolver against **one obvious case** (e.g. Judas Priest or Sabaton) with verbose logging and confirm whether the plain-text leg is paginating deeply enough. Two outcomes:

- If pagination is the cause → patch the resolver (mirror Stage 4's 5-page setting in the offline path) and the same fix lifts most of Steps 1–5 in one re-run.
- If artist-ID filter is over-discarding → tune the filter (e.g. accept tracks where the target artist is *any* listed artist, not only the primary) and re-run.

Only after that diagnostic gives a clean result on one band do we batch.

### Step 1b — run the 5-track batch
- `py scripts/resolve_lineup.py --retry-unresolved --below-threshold-only` won't help here (those flags target the `unresolved_bands.json` set, not the 5-track-in-main-file set). Need either:
  - A new flag, e.g. `--retry-low-count <N>`, that re-resolves any band in `wacken_2026.json` whose `track_count < N`, **or**
  - A one-shot script that reads `wacken_2026.json`, filters bands with `track_count == 5`, and calls the same resolution function used by the main resolver.
- I recommend adding the flag — it makes Steps 2–5 a one-line invocation with `--retry-low-count 6`, `7`, `8`, `9`.

### Step 2–5 — repeat for 6, 7, 8, 9
Same command, raise the threshold one at a time. Doing them in separate runs (not one big `--retry-low-count 10`) keeps each batch small enough to roll back cleanly if Spotify starts throttling mid-run.

### After each step
- Commit `wacken_2026.json` only after spot-checking 2–3 bands per batch (open the URIs, confirm they're the right artist).
- Bump `version.py` once per batch so the PWA cache busts.
- Update CLAUDE.md "Current Stage" with the new total and the count of `< 10`-track bands remaining.

### Then return to the deferred list
With the resolver behavior understood, circle back to the 1–4 and 0 track bands:
1. Fill the two remaining override gaps (**E.N.D.**, **Force**).
2. Run `--retry-unresolved` to pick up Novelization and Maschine's single tracks.
3. Mark Novelization and Maschine `permanently_unresolved` once their 1 track is captured.

---

## Success criteria

- ≥ 90 % of the 5-track band batch reaches 10 tracks after Step 1.
- Each subsequent step (6, 7, 8, 9) reaches 10 for ≥ 90 % of its bands.
- No band that already had 10 tracks loses any (the new resolver pass must be **idempotent for full bands**).
- No artist-ID drift: spot-check confirms the right artist for at least 2 bands per step.
- `version.py` bumped, CLAUDE.md + PHASES.md updated after each completed step.
