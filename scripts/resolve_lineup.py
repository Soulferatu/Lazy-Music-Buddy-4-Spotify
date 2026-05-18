#!/usr/bin/env python3
"""
Resolve Spotify tracks for Wacken Open Air lineup bands.

Runs offline once per lineup update. Stores results in wacken_2026.json
with embedded track URIs, eliminating runtime Spotify search calls.

Usage:
  py scripts/resolve_lineup.py                          # Full resolution (all bands)
  py scripts/resolve_lineup.py --test                   # Test run (first 10 bands)
  py scripts/resolve_lineup.py --resume-from-band 50    # Resume from band 50
  py scripts/resolve_lineup.py --retry-unresolved       # Re-resolve all bands in unresolved_bands.json
  py scripts/resolve_lineup.py --retry-unresolved --below-threshold-only
                                                        # Only retry bands with 1-4 tracks (skip zero-track)
  py scripts/resolve_lineup.py --retry-low-count 5      # Re-resolve bands in wacken_2026.json with exactly 5 tracks
  py scripts/resolve_lineup.py --retry-low-count 9      # ... or any other count below MAX_TRACKS (10)
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import date
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from wacken_playlist.services.spotify import SpotifyClient


RATE_LIMIT_DELAY = 1.5   # seconds between Spotify calls
MAX_TRACKS = 10
MAX_PAGES_ARTIST = 5     # pages to try with artist: qualifier (bumped 3->5 on 2026-05-18 after The Limit diagnostic)
MAX_PAGES_PLAIN = 5      # pages to try with plain-text query
DATA_FILE = Path("wacken_playlist/data/lineups/wacken_2026.json")
UNRESOLVED_FILE = Path("wacken_playlist/data/lineups/unresolved_bands.json")
OVERRIDES_FILE = Path("wacken_playlist/data/lineups/artist_overrides.json")


def _load_overrides() -> dict[str, str]:
    """Return {band_name: spotify_artist_id} from artist_overrides.json, or {}."""
    if not OVERRIDES_FILE.exists():
        return {}
    with OVERRIDES_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("overrides", {})


def _collect_tracks_for_artist(
    client: SpotifyClient,
    band_name: str,
    artist_id: str,
    delay: float,
) -> tuple[list[dict], float]:
    """
    Run two search strategies and return up to MAX_TRACKS tracks filtered by artist ID.

    Strategy 1: artist:"NAME" qualifier (up to MAX_PAGES_ARTIST pages).
    Strategy 2: plain-text NAME query (up to MAX_PAGES_PLAIN pages).

    Filtering by artist ID (not name) handles: case differences, generic band names,
    bands that Spotify stores with slightly different capitalization.

    Dedup is by URI and case-insensitive title — Spotify often returns multiple URIs
    for the same song (single, album, compilation, remaster). Keeping the first URI per
    title avoids "same song back-to-back" in generated playlists. Bands with two distinct
    songs that share a title (rare) will lose one; that trade-off is documented in
    wiki/track_topup_plan.md.

    Returns (tracks, updated_delay).
    """
    seen_uris: set[str] = set()
    seen_titles: set[str] = set()
    collected: list[dict] = []

    def _accept(track: dict) -> bool:
        """Return True if this track belongs to our target artist and isn't a duplicate."""
        artists = track.get("artists") or []
        if not any(a.get("id") == artist_id for a in artists):
            return False
        uri = track.get("uri", "")
        if not uri or uri in seen_uris:
            return False
        title_key = (track.get("name", "") or "").lower().strip()
        if title_key and title_key in seen_titles:
            return False
        seen_uris.add(uri)
        if title_key:
            seen_titles.add(title_key)
        return True

    # --- Strategy 1: artist:"NAME" qualifier ---
    for page in range(MAX_PAGES_ARTIST):
        if len(collected) >= MAX_TRACKS:
            break
        results = client.search_tracks_by_artist(band_name, limit=10, offset=page * 10)
        page_hits = 0
        for track in results:
            if _accept(track):
                collected.append({"uri": track["uri"], "name": track.get("name", "")})
                page_hits += 1
                if len(collected) >= MAX_TRACKS:
                    break
        time.sleep(delay)
        # Stop early if Spotify returned fewer than the page cap (nothing more to page through)
        if len(results) < 10 and page_hits == 0:
            break

    # --- Strategy 2: plain-text query ---
    for page in range(MAX_PAGES_PLAIN):
        if len(collected) >= MAX_TRACKS:
            break
        results = client.search_tracks_plain(band_name, limit=10, offset=page * 10)
        page_hits = 0
        for track in results:
            if _accept(track):
                collected.append({"uri": track["uri"], "name": track.get("name", "")})
                page_hits += 1
                if len(collected) >= MAX_TRACKS:
                    break
        time.sleep(delay)
        if not results:
            break  # no more results at all

    return collected[:MAX_TRACKS], delay


def resolve_band(
    client: SpotifyClient,
    band_name: str,
    current_delay: float,
    override_id: Optional[str] = None,
) -> tuple[dict, float]:
    """
    Resolve up to MAX_TRACKS track URIs for a band.

    Uses artist ID (not name) for filtering so generic names like "Europe" or
    "Phantom" are unambiguous — only tracks where the exact Spotify artist appears.

    If override_id is provided, skips search_artist entirely and uses it directly.

    Returns (resolved_data, updated_delay).
    """
    try:
        if override_id:
            artist_id = override_id
        else:
            artist = client.search_artist(band_name)
            if not artist:
                return (
                    {"spotify_id": None, "tracks": [], "track_count": 0, "unresolved": True},
                    current_delay,
                )
            artist_id = artist["id"]
            time.sleep(current_delay)

        tracks, updated_delay = _collect_tracks_for_artist(
            client, band_name, artist_id, current_delay
        )
        return (
            {"spotify_id": artist_id, "tracks": tracks, "track_count": len(tracks)},
            updated_delay,
        )

    except Exception as e:
        if "429" in str(e) or "rate" in str(e).lower():
            new_delay = min(current_delay * 1.5, 30)
            print(f"  ! Rate limit; increasing delay to {new_delay:.1f}s")
            return (
                {"spotify_id": None, "tracks": [], "track_count": 0, "unresolved": True},
                new_delay,
            )
        print(f"  X Error resolving {band_name}: {e}")
        return (
            {"spotify_id": None, "tracks": [], "track_count": 0, "unresolved": True},
            current_delay,
        )


def build_bands_from_json(data: dict) -> list[str]:
    """Extract band names from JSON."""
    bands = data.get("bands", [])
    if not bands:
        return []
    if isinstance(bands[0], str):
        return bands
    elif isinstance(bands[0], dict):
        return [b.get("name", "") for b in bands if b.get("name")]
    return []


def _classify(result: dict, name: str, today: str) -> Optional[dict]:
    """Return an unresolved entry dict if the result is unsatisfactory, else None."""
    if result.get("unresolved"):
        return {"name": name, "reason": "Not found on Spotify", "attempted_at": today}
    if result["track_count"] == 0:
        return {"name": name, "reason": "Zero tracks found on Spotify", "attempted_at": today}
    if result["track_count"] < 5:
        return {"name": name, "reason": f"Below threshold: {result['track_count']} tracks", "attempted_at": today}
    return None


def run(test_mode: bool = False, resume_from_band: Optional[int] = None) -> None:
    """Main resolution loop (full or partial run)."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    with DATA_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    client = SpotifyClient(
        client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", ""),
    )

    band_names = build_bands_from_json(data)
    if not band_names:
        print("No bands found in JSON")
        return

    if test_mode:
        band_names = band_names[:10]
        print(f"[TEST] Test mode: resolving first {len(band_names)} bands\n")
    else:
        print(f"[FULL] Full resolution mode: {len(band_names)} bands\n")

    start_idx = 0
    if resume_from_band is not None:
        start_idx = max(0, resume_from_band - 1)
        print(f"[RESUME] Resuming from band {resume_from_band} (index {start_idx})\n")

    resolved_bands: list[dict] = []
    unresolved_entries: list[dict] = []
    current_delay = RATE_LIMIT_DELAY
    today = date.today().isoformat()
    overrides = _load_overrides()
    if overrides:
        print(f"[OVERRIDES] {len(overrides)} manual artist-ID overrides loaded\n")

    for i, name in enumerate(band_names, 1):
        if i <= start_idx:
            continue

        override_id = overrides.get(name)
        if override_id:
            print(f"[{i}/{len(band_names)}] Resolving: {name}  (override -> {override_id})")
        else:
            print(f"[{i}/{len(band_names)}] Resolving: {name}")
        result, current_delay = resolve_band(client, name, current_delay, override_id=override_id)
        result["name"] = name
        result["resolved_at"] = today

        entry = _classify(result, name, today)
        if entry:
            reason = entry["reason"]
            if "Zero" in reason:
                print(f"  ! Zero tracks found (artist exists but no matching tracks)")
            elif "Not found" in reason:
                print(f"  ! Not found on Spotify")
            else:
                print(f"  ! Only {result['track_count']} track(s) found (below threshold)")
            unresolved_entries.append(entry)
        else:
            print(f"  + {result['track_count']} tracks resolved")

        resolved_bands.append(result)

    if resume_from_band is not None:
        with DATA_FILE.open(encoding="utf-8") as f:
            existing = json.load(f)
        existing_bands = existing.get("bands", [])
        prefix = [
            b if isinstance(b, dict)
            else {"name": b, "spotify_id": None, "tracks": [], "track_count": 0, "unresolved": True}
            for b in existing_bands[:start_idx]
        ]
        data["bands"] = prefix + resolved_bands
    else:
        data["bands"] = resolved_bands

    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if unresolved_entries:
        with UNRESOLVED_FILE.open("w", encoding="utf-8") as f:
            json.dump(
                {"unresolved": unresolved_entries, "updated_at": today},
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"\n[!] {len(unresolved_entries)} unresolved bands → {UNRESOLVED_FILE.name}")

    resolved_count = sum(1 for b in resolved_bands if not b.get("unresolved"))
    print(f"\n[OK] Resolution complete. Resolved: {resolved_count} / Unresolved: {len(unresolved_entries)}")


def retry_unresolved(below_threshold_only: bool = False) -> None:
    """
    Re-resolve bands from unresolved_bands.json using the improved two-strategy search
    with artist ID filtering.

    --below-threshold-only: skip bands that previously had zero tracks (they are likely
    genuinely absent from Spotify); only retry those that got 1-4 tracks.
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    if not UNRESOLVED_FILE.exists():
        print("unresolved_bands.json not found — nothing to retry.")
        return

    with UNRESOLVED_FILE.open(encoding="utf-8") as f:
        unresolved_data = json.load(f)

    candidates = unresolved_data.get("unresolved", [])
    # Always skip entries explicitly marked as permanently unresolved
    # (e.g. Wacken-local acts, tribute bands with no Spotify presence).
    candidates = [b for b in candidates if not b.get("permanently_unresolved")]
    if below_threshold_only:
        candidates = [b for b in candidates if b.get("reason", "").startswith("Below threshold")]
        mode_label = "below-threshold bands only"
    else:
        mode_label = "all unresolved bands (excluding permanently-unresolved)"

    if not candidates:
        print(f"No {mode_label} found in unresolved_bands.json.")
        return

    print(f"[RETRY] Re-resolving {len(candidates)} {mode_label}\n")

    client = SpotifyClient(
        client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", ""),
    )

    with DATA_FILE.open(encoding="utf-8") as f:
        lineup = json.load(f)

    bands_by_name: dict[str, dict] = {
        b["name"]: b for b in lineup.get("bands", []) if isinstance(b, dict)
    }

    overrides = _load_overrides()
    if overrides:
        print(f"[OVERRIDES] {len(overrides)} manual artist-ID overrides loaded\n")

    improved: list[str] = []
    still_unresolved: list[dict] = []
    today = date.today().isoformat()

    for i, entry in enumerate(candidates, 1):
        name = entry["name"]
        old_reason = entry.get("reason", "")
        print(f"[{i}/{len(candidates)}] Retrying: {name}  ({old_reason})")

        override_id = overrides.get(name)
        if override_id:
            artist_id = override_id
            print(f"  > artist ID (override): {artist_id}")
        else:
            artist = client.search_artist(name)
            if not artist:
                print(f"  ! Artist still not found on Spotify")
                still_unresolved.append({"name": name, "reason": "Not found on Spotify", "attempted_at": today})
                time.sleep(RATE_LIMIT_DELAY)
                continue
            artist_id = artist["id"]
            print(f"  > artist ID: {artist_id} ({artist['name']})")
            time.sleep(RATE_LIMIT_DELAY)

        tracks, _ = _collect_tracks_for_artist(client, name, artist_id, RATE_LIMIT_DELAY)
        new_count = len(tracks)

        result = {
            "name": name,
            "spotify_id": artist_id,
            "tracks": tracks,
            "track_count": new_count,
            "resolved_at": today,
        }
        if new_count == 0:
            result["unresolved"] = True

        if new_count >= 5:
            print(f"  + {new_count} tracks resolved — removed from unresolved list")
            improved.append(name)
        elif new_count > 0:
            old_count_str = old_reason.split(": ")[-1].split(" ")[0] if "Below threshold" in old_reason else "0"
            print(f"  ~ {new_count} tracks (was {old_count_str}) — still below threshold")
            still_unresolved.append({"name": name, "reason": f"Below threshold: {new_count} tracks", "attempted_at": today})
        else:
            print(f"  ! Zero tracks found — leaving in unresolved list")
            still_unresolved.append({"name": name, "reason": "Zero tracks found on Spotify", "attempted_at": today})

        # Update the lineup entry in-place
        if name in bands_by_name:
            bands_by_name[name].update(result)
        else:
            lineup["bands"].append(result)

        # Pace between bands
        time.sleep(RATE_LIMIT_DELAY)

    # Write updated lineup
    lineup["bands"] = list(bands_by_name.values())
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(lineup, f, ensure_ascii=False, indent=2)

    # Preserve unresolved entries we didn't touch, then write the updated list
    touched_names = {e["name"] for e in candidates}
    untouched = [b for b in unresolved_data.get("unresolved", []) if b["name"] not in touched_names]
    final_unresolved = untouched + still_unresolved

    with UNRESOLVED_FILE.open("w", encoding="utf-8") as f:
        json.dump({"unresolved": final_unresolved, "updated_at": today}, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Retry complete.")
    print(f"   Improved (>= 5 tracks): {len(improved)}" + (f" — {improved}" if improved else ""))
    print(f"   Still unresolved: {len(still_unresolved)}")
    print(f"   wacken_2026.json and unresolved_bands.json updated.")


def retry_low_count(target_count: int) -> None:
    """
    Re-resolve every band in wacken_2026.json whose current track_count == target_count.

    Used to top up bands stuck below MAX_TRACKS after a previous resolver pass with
    smaller pagination. Idempotent: if the re-resolution comes back with the same count
    or lower, the existing entry is kept (no destructive overwrite).
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    if target_count < 0 or target_count >= MAX_TRACKS:
        print(f"--retry-low-count must be between 0 and {MAX_TRACKS - 1} (got {target_count}).")
        return

    with DATA_FILE.open(encoding="utf-8") as f:
        lineup = json.load(f)

    bands = lineup.get("bands", [])
    targets = [b for b in bands if isinstance(b, dict) and b.get("track_count") == target_count]

    # Skip anything explicitly flagged permanently_unresolved in unresolved_bands.json.
    # The flag exists precisely to stop retry churn on artists with a known Spotify ceiling.
    perm_unresolved: set[str] = set()
    if UNRESOLVED_FILE.exists():
        with UNRESOLVED_FILE.open(encoding="utf-8") as f:
            ud = json.load(f)
        perm_unresolved = {
            e["name"] for e in ud.get("unresolved", [])
            if e.get("permanently_unresolved")
        }
    if perm_unresolved:
        skipped = [b for b in targets if b["name"] in perm_unresolved]
        targets = [b for b in targets if b["name"] not in perm_unresolved]
        for b in skipped:
            print(f"[SKIP] {b['name']} — permanently_unresolved")

    if not targets:
        print(f"No bands at track_count == {target_count} in {DATA_FILE.name}.")
        return

    print(f"[RETRY-LOW] Re-resolving {len(targets)} bands at track_count == {target_count}\n")

    client = SpotifyClient(
        client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", ""),
    )

    overrides = _load_overrides()
    if overrides:
        print(f"[OVERRIDES] {len(overrides)} manual artist-ID overrides loaded\n")

    bands_by_name = {b["name"]: b for b in bands if isinstance(b, dict)}
    today = date.today().isoformat()
    current_delay = RATE_LIMIT_DELAY
    improved: list[tuple[str, int, int]] = []
    unchanged: list[tuple[str, int]] = []

    for i, entry in enumerate(targets, 1):
        name = entry["name"]
        old_count = entry.get("track_count", 0)
        # Prefer the stored spotify_id if we already have one (avoids redundant search_artist).
        override_id = overrides.get(name) or entry.get("spotify_id")
        print(f"[{i}/{len(targets)}] {name}  (was {old_count})")

        result, current_delay = resolve_band(client, name, current_delay, override_id=override_id)
        new_count = result.get("track_count", 0)

        if new_count > old_count:
            print(f"  + {new_count} tracks (was {old_count})")
            bands_by_name[name].update({
                "spotify_id": result.get("spotify_id") or entry.get("spotify_id"),
                "tracks": result.get("tracks", []),
                "track_count": new_count,
                "resolved_at": today,
            })
            # Clear any stale unresolved flag now that we have a fuller result.
            bands_by_name[name].pop("unresolved", None)
            improved.append((name, old_count, new_count))
        else:
            print(f"  ~ {new_count} tracks (no improvement) — keeping previous entry untouched")
            unchanged.append((name, old_count))

        time.sleep(current_delay)

    lineup["bands"] = list(bands_by_name.values())
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(lineup, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] retry-low-count {target_count} complete.")
    print(f"   Improved: {len(improved)}")
    for name, old, new in improved:
        print(f"     {name}: {old} -> {new}")
    print(f"   Unchanged: {len(unchanged)}")
    if unchanged:
        for name, old in unchanged:
            print(f"     {name}: still {old}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve Spotify tracks for Wacken lineup bands.")
    parser.add_argument("--test", action="store_true", help="Test run: resolve only first 10 bands")
    parser.add_argument("--resume-from-band", type=int, help="Resume from band N (1-indexed)")
    parser.add_argument(
        "--retry-unresolved",
        action="store_true",
        help="Re-resolve only bands from unresolved_bands.json using artist-ID-based filtering",
    )
    parser.add_argument(
        "--below-threshold-only",
        action="store_true",
        help="With --retry-unresolved: only retry bands that got 1-4 tracks (skip zero-track bands)",
    )
    parser.add_argument(
        "--retry-low-count",
        type=int,
        metavar="N",
        help=f"Re-resolve bands in wacken_2026.json with exactly N tracks (0 <= N < {MAX_TRACKS}). Idempotent: keeps previous data if new pass doesn't improve.",
    )

    args = parser.parse_args()

    if args.retry_unresolved:
        retry_unresolved(below_threshold_only=args.below_threshold_only)
    elif args.retry_low_count is not None:
        retry_low_count(args.retry_low_count)
    else:
        run(test_mode=args.test, resume_from_band=args.resume_from_band)