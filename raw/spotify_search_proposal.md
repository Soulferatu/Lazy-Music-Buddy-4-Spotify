# Spotify Search Proposal
## Lazy Music Buddy 4 Spotify — Track Resolution Strategy

---

## 1. Context and Problem Statement

### 1.1 The Project

Lazy Music Buddy 4 Spotify is a Flask-based PWA that lets users pick bands from the Wacken Open Air 2026 lineup and generate a Spotify playlist from their selections. The architecture plan (Phase 4A) defined a `SpotifyClient` service with the following interface for track retrieval:

```python
def search_artist(self, name: str) -> dict | None: ...
def get_top_tracks(self, artist_id: str, market: str = "US") -> list[dict]: ...
def create_playlist(self, name: str, track_uris: list[str]) -> str: ...
```

This describes a **two-step flow per band**: first resolve the artist's Spotify ID via search, then fetch their top tracks using that ID.

### 1.2 The API Deprecations

Two waves of Spotify Web API changes broke this plan before it was even implemented.

**November 2024 — First wave (removed entirely):**
- `GET /recommendations`
- `GET /audio-features`
- `GET /audio-analysis`
- Related artists endpoint
- Algorithmic and editorial playlists

**February 2026 — Second wave (Dev Mode apps):**
- `GET /artists/{id}/top-tracks` — **removed with no replacement**
- `GET /tracks`, `GET /artists` (batch endpoints) — removed
- `GET /browse/*` category endpoints — removed
- `GET /users/{id}` and `GET /users/{id}/playlists` — removed
- `POST /playlists/{id}/tracks` → renamed to `POST /playlists/{id}/items`
- Search `limit` capped at **10** (was 50)
- `popularity`, `available_markets`, `followers` fields removed from responses

The `get_top_tracks` method in the Phase 4A stub points directly to the removed `GET /artists/{id}/top-tracks` endpoint. **Stage 2 would be broken before it starts.**

### 1.3 Real-World Pain Points Encountered

Before the final proposal was settled, two production problems were identified from actual usage:

1. **Shadow ban (17-hour rate limit):** Firing too many Spotify API calls in a short window — even across legitimate endpoints — triggered a prolonged rate-limit response. This happened because requests were issued in bursts, one per band.

2. **Incomplete results for obscure bands:** Smaller festival acts returned fewer than 10 tracks from a single search call. Workarounds using offset-based pagination multiplied the call count further, compounding the rate-limiting risk.

---

## 2. Approaches Considered

### 2.1 Search as a Top-Tracks Replacement (Initial Proposal)

The first instinct was to replace `GET /artists/{id}/top-tracks` with `GET /search?type=track&q=artist:"Name"&limit=10`. This consolidates the two-step flow into one call per band and keeps Spotify's relevance ranking as a proxy for "most known songs."

**Per-user-session call count (20 bands selected):**
```
20 search calls + 1 create playlist + 1–2 add-items = ~23 calls per session
```

**Why this was rejected as the final answer:**

- Still fires N calls per user session — the burst pattern that caused the shadow ban remains.
- The search `limit` cap of 10 means obscure bands may return fewer matching results, requiring pagination (2–3 calls per band) — the same problem as before, just on a different endpoint.
- Primary artist filtering is needed to discard tracks where the band appears as a feature rather than the main act, adding logic complexity.
- Rate-limiting risk scales with usage: one user is fine; ten concurrent users are not.

### 2.2 Albums → Tracks Traversal

An alternative was to use `GET /artists/{id}/albums` followed by `GET /albums/{id}/tracks` per album. This was rejected because it produces **more** calls per band than the search approach, not fewer, with no meaningful quality advantage.

### 2.3 Pre-Resolution (Final Recommendation)

Since the Wacken lineup is **fixed and known in advance**, there is no reason to call the Spotify search API at all during a user's session. Track URIs can be resolved **once, offline, at build time**, stored in the JSON lineup file, and served directly at playlist-creation time.

This is the approach detailed in the rest of this document.

---

## 3. The Pre-Resolution Solution

### 3.1 Core Idea

Move all Spotify search and track-resolution work into a **developer-run script** (`scripts/resolve_lineup.py`) that executes once when the lineup is prepared. The results are persisted in `wacken_playlist/data/lineups/wacken_2026.json`. At runtime, `PlaylistBuilder` reads the pre-resolved URIs directly — zero Spotify search calls per user session.

### 3.2 Call Count Comparison

| Scenario | Search approach | Pre-resolution |
|---|---|---|
| Track resolution | N calls at request time | 0 calls at request time |
| Playlist creation | 1 call | 1 call |
| Add tracks (100 URIs/batch) | 1–2 calls | 1–2 calls |
| **Total per user session** | **N + 2–3** | **2–3, always** |
| Rate-limit risk | Scales with users | None |
| Obscure band pagination | Runtime, per user | Offline, once, with backoff |
| Unresolvable bands | Silent runtime failure | Known in advance, flagged |

### 3.3 How the Shadow Ban Is Eliminated

The shadow ban occurred because bursts of API calls were made synchronously within a short window. With pre-resolution, the **resolution script** is the only component that talks to the Spotify search API, and it does so with a deliberate delay between each call (see Section 4.2). User sessions never touch the search API at all. No matter how many users generate playlists simultaneously, the Spotify call count per session stays at 2–3.

### 3.4 How the Pagination Problem Is Eliminated

The resolution script runs offline, at the developer's pace. It can paginate through as many pages as needed to collect up to 10 good tracks per band, with a sleep between each page request. Obscure bands that genuinely have fewer than 10 tracks on Spotify are flagged in the JSON with their actual `track_count`, so the UI can inform users upfront rather than silently producing short playlists.

---

## 4. Implementation

### 4.1 Extended JSON Schema

`wacken_playlist/data/lineups/wacken_2026.json` gains a `tracks` array and resolution metadata per band:

```json
{
  "year": 2026,
  "source_urls": [
    "https://www.wacken.com/en/..."
  ],
  "bands": [
    {
      "name": "Rammstein",
      "spotify_id": "6wWVKhxIU2cEi0K81v7HvP",
      "tracks": [
        { "uri": "spotify:track:abc123", "name": "Du Hast" },
        { "uri": "spotify:track:def456", "name": "Sonne" },
        { "uri": "spotify:track:ghi789", "name": "Engel" }
      ],
      "resolved_at": "2026-05-17",
      "track_count": 10
    },
    {
      "name": "Some Obscure Act",
      "spotify_id": "1a2b3c4d5e6f",
      "tracks": [
        { "uri": "spotify:track:xyz001", "name": "Only Song" }
      ],
      "resolved_at": "2026-05-17",
      "track_count": 1
    },
    {
      "name": "Band Not On Spotify",
      "spotify_id": null,
      "tracks": [],
      "resolved_at": "2026-05-17",
      "track_count": 0,
      "unresolved": true
    }
  ]
}
```

Existing fields (`name`, `year`, `source_urls`) are unchanged. The new fields are additive — `LineupRepository` and `Band` dataclass require only minor extensions.

### 4.2 Resolution Script

`scripts/resolve_lineup.py` — runs once, developer-side, using client credentials (no user OAuth required):

```python
import time
import json
from pathlib import Path
from wacken_playlist.services.spotify import SpotifyClient

RATE_LIMIT_DELAY = 1.2   # seconds between Spotify calls — safe margin for Dev Mode
MAX_TRACKS = 10
DATA_FILE = Path("wacken_playlist/data/lineups/wacken_2026.json")


def resolve_band(client: SpotifyClient, band_name: str) -> dict:
    """
    Resolves up to MAX_TRACKS track URIs for a given band name.
    Uses pagination if the first page returns fewer results than expected.
    Filters results so only tracks where the band is the primary artist are kept.
    """
    # Step 1: find artist ID
    artist = client.search_artist(band_name)
    if not artist:
        return {"spotify_id": None, "tracks": [], "track_count": 0, "unresolved": True}

    time.sleep(RATE_LIMIT_DELAY)

    # Step 2: search tracks with pagination until MAX_TRACKS collected or pages exhausted
    collected = []
    offset = 0

    while len(collected) < MAX_TRACKS:
        results = client.search_tracks_by_artist(band_name, limit=10, offset=offset)
        
        # Only keep tracks where this band is the primary (first) artist
        filtered = [
            {"uri": t["uri"], "name": t["name"]}
            for t in results
            if t["artists"][0]["name"].lower() == band_name.lower()
        ]
        collected.extend(filtered)

        if len(results) < 10:
            break  # no more pages available

        offset += 10
        time.sleep(RATE_LIMIT_DELAY)

    tracks = collected[:MAX_TRACKS]
    return {
        "spotify_id": artist["id"],
        "tracks": tracks,
        "track_count": len(tracks),
    }


def run():
    with DATA_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    client = SpotifyClient.from_client_credentials()

    resolved_bands = []
    total = len(data["bands"])

    for i, band in enumerate(data["bands"], 1):
        name = band if isinstance(band, str) else band["name"]
        print(f"[{i}/{total}] Resolving: {name}")

        result = resolve_band(client, name)
        result["name"] = name
        result["resolved_at"] = "2026-05-17"  # or use datetime.date.today().isoformat()
        resolved_bands.append(result)

        if result.get("unresolved"):
            print(f"  ⚠ Not found on Spotify")
        elif result["track_count"] < 5:
            print(f"  ⚠ Only {result['track_count']} track(s) found — review manually")
        else:
            print(f"  ✓ {result['track_count']} tracks resolved")

    data["bands"] = resolved_bands

    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    unresolved = [b["name"] for b in resolved_bands if b.get("unresolved")]
    low_count = [b["name"] for b in resolved_bands if not b.get("unresolved") and b["track_count"] < 5]

    print(f"\n✅ Resolution complete.")
    print(f"   Unresolved ({len(unresolved)}): {unresolved or 'none'}")
    print(f"   Low track count (<5) ({len(low_count)}): {low_count or 'none'}")


if __name__ == "__main__":
    run()
```

**Runtime estimate:** 114 bands × ~1.2s delay × ~1.5 average pages = roughly 3–4 minutes. Run it once; never again unless the lineup changes.

### 4.3 `SpotifyClient` Interface Change

Replace `get_top_tracks` with `search_tracks_by_artist`. The `search_artist` method is retained for the resolution script.

```python
# REMOVE — points to a dead endpoint:
def get_top_tracks(self, artist_id: str, market: str = "US") -> list[dict]: ...

# ADD — used by the resolution script:
def search_tracks_by_artist(self, artist_name: str, limit: int = 10, offset: int = 0) -> list[dict]:
    """
    GET /search?type=track&q=artist:"name"&limit=N&offset=N
    Returns raw track objects from the Spotify search response.
    """
    ...
```

The `market` parameter is dropped entirely — it was only relevant to the removed endpoint.

### 4.4 `Band` Model Extension

`wacken_playlist/models.py` — add the resolved fields:

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Track:
    uri: str
    name: str

@dataclass(frozen=True)
class Band:
    name: str
    year: int
    spotify_id: str | None = None
    tracks: tuple[Track, ...] = field(default_factory=tuple)
    track_count: int = 0
    unresolved: bool = False
```

`LineupRepository.get_bands()` maps the JSON structure onto these dataclasses. No other service changes.

### 4.5 `PlaylistBuilder` at Runtime

With pre-resolved data, `build_and_create` becomes a simple filter-and-create:

```python
def build_and_create(self, request: PlaylistRequest) -> PlaylistResult:
    uris = []
    skipped = []

    for band in request.bands:
        if band.tracks:
            uris.extend(t.uri for t in band.tracks)
        else:
            skipped.append(band.name)

    playlist_url = self.spotify.create_playlist(request.playlist_name, uris)

    return PlaylistResult(
        playlist_name=request.playlist_name,
        spotify_url=playlist_url,
        track_count=len(uris),
        skipped_bands=skipped,
    )
```

Zero search calls. Zero pagination. Zero rate-limit exposure per user session.

### 4.6 `PlaylistBuilder` for the Preview

`build_preview` can now also surface resolution quality upfront:

```python
def build_preview(self, request: PlaylistRequest) -> PlaylistPreview:
    unresolved = [b.name for b in request.bands if b.unresolved]
    low_count = [b.name for b in request.bands if not b.unresolved and b.track_count < 5]

    return PlaylistPreview(
        playlist_name=request.playlist_name,
        bands=request.bands,
        track_count=sum(b.track_count for b in request.bands),
        unresolved_bands=unresolved,
        low_count_bands=low_count,
    )
```

Users see exactly how many tracks will be in their playlist — and which bands will be skipped — before hitting Spotify at all.

---

## 5. Architecture Impact Summary

| Component | Change required |
|---|---|
| `wacken_2026.json` | Extended with `spotify_id`, `tracks`, `track_count`, `resolved_at`, `unresolved` |
| `models.py` | Add `Track` dataclass; extend `Band` with resolved fields; extend `PlaylistPreview` |
| `lineup.py` (`LineupRepository`) | Map new JSON fields onto extended dataclasses |
| `services/spotify.py` | Replace `get_top_tracks` with `search_tracks_by_artist`; drop `market` param |
| `services/playlist.py` | `build_and_create` simplified; `build_preview` gains resolution quality info |
| `scripts/resolve_lineup.py` | **New** — one-time resolution script |
| `routes.py` | No changes |
| Templates | Optional: surface `unresolved_bands` and `low_count_bands` in preview UI |
| Tests | Update `mock_spotify` fixture; add `test_resolve_lineup.py` unit tests |

### Explicitly unchanged
- All Phase 1–3 and Phase 5–6 architecture work (config, i18n, CSRF, test split)
- The `create_playlist` method and playlist creation flow
- The `PlaylistRequest` and `PlaylistResult` dataclasses (minor extension only)
- OAuth flow (Stage 5) — unaffected

---

## 6. When to Re-Run the Resolution Script

| Trigger | Action |
|---|---|
| New bands added to the lineup | Re-run `resolve_lineup.py` for the new entries only (add `--band` flag) |
| Full lineup update (year change) | Create `wacken_2027.json`, run full resolution |
| A band's Spotify presence changes | Re-run for that band; update JSON manually if needed |
| Spotify rate limit during resolution | Increase `RATE_LIMIT_DELAY` and resume from last completed band |

The script is idempotent by design — re-running it on already-resolved bands simply overwrites with the same data.

---

## 7. Open Questions for Implementation

1. **Manual curation for `unresolved` bands** — should the UI show these as greyed-out (unselectable) or selectable with a warning?
2. **Track quality threshold** — is `track_count < 5` the right cutoff for a "low count" warning, or should it be lower?
3. **Refresh cadence** — Wacken 2026 lineups can be updated up to the event. A lightweight `--diff` mode for the resolution script (only resolving unresolved entries) would keep re-runs fast.
4. **`resolved_at` date** — consider storing this as an ISO datetime so staleness can be detected programmatically.
