#!/usr/bin/env python3
"""
Resolve Spotify tracks for Wacken Open Air lineup bands.

Runs offline once per lineup update. Stores results in wacken_2026.json
with embedded track URIs, eliminating runtime Spotify search calls.

Usage:
  py scripts/resolve_lineup.py                    # Full resolution (all bands)
  py scripts/resolve_lineup.py --test             # Test run (first 10 bands)
  py scripts/resolve_lineup.py --resume-from-band 50  # Resume from band 50
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import date
from typing import Optional

# Add parent directory to path so wacken_playlist can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from wacken_playlist.services.spotify import SpotifyClient


RATE_LIMIT_DELAY = 1.5  # seconds between Spotify calls
MAX_TRACKS = 10
DATA_FILE = Path("wacken_playlist/data/lineups/wacken_2026.json")
UNRESOLVED_FILE = Path("wacken_playlist/data/lineups/unresolved_bands.json")


def resolve_band(client: SpotifyClient, band_name: str, current_delay: float):
    """
    Resolves up to MAX_TRACKS track URIs for a given band name.
    Returns (resolved_data, updated_delay) where updated_delay may have increased due to 429s.
    """
    try:
        # Step 1: find artist ID
        artist = client.search_artist(band_name)
        if not artist:
            return {"spotify_id": None, "tracks": [], "track_count": 0, "unresolved": True}, current_delay

        time.sleep(current_delay)

        # Step 2: search tracks with pagination until MAX_TRACKS collected or pages exhausted
        collected = []
        offset = 0
        delay = current_delay

        while len(collected) < MAX_TRACKS:
            try:
                results = client.search_tracks_by_artist(band_name, limit=10, offset=offset)

                # Only keep tracks where this band is the primary (first) artist
                filtered = [
                    {"uri": t["uri"], "name": t["name"]}
                    for t in results
                    if t.get("artists") and len(t["artists"]) > 0 and t["artists"][0].get("name", "").lower() == band_name.lower()
                ]
                collected.extend(filtered)

                if len(results) < 10:
                    break  # no more pages available

                offset += 10
                time.sleep(delay)

            except Exception as e:
                # If we get a 429, the client should have retried once.
                # If we still get an error, log it and continue with partial results.
                if "429" in str(e) or "rate" in str(e).lower():
                    delay = min(delay * 1.5, 30)  # increase delay up to 30s, cap it
                    print(f"  ! Rate limit detected; increasing delay to {delay:.1f}s")
                    continue
                else:
                    raise

        tracks = collected[:MAX_TRACKS]
        return {
            "spotify_id": artist["id"],
            "tracks": tracks,
            "track_count": len(tracks),
        }, delay

    except Exception as e:
        print(f"  X Error resolving {band_name}: {e}")
        return {"spotify_id": None, "tracks": [], "track_count": 0, "unresolved": True}, current_delay


def build_bands_from_json(data: dict) -> list[str]:
    """Extract band names from JSON, handling both old (list) and new (object) formats."""
    bands = data.get("bands", [])
    if not bands:
        return []
    if isinstance(bands[0], str):
        # Old format: ["Band Name", "Band Name", ...]
        return bands
    elif isinstance(bands[0], dict):
        # New format: [{"name": "Band Name", ...}, ...]
        return [b.get("name", "") for b in bands if b.get("name")]
    return []


def run(test_mode: bool = False, resume_from_band: Optional[int] = None):
    """Main resolution loop."""
    import os
    from dotenv import load_dotenv

    # Load .env file
    load_dotenv()

    with DATA_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    client = SpotifyClient(
        client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", ""),
    )

    band_names = build_bands_from_json(data)
    if not band_names:
        print("❌ No bands found in JSON")
        return

    # If test mode, only use first 10
    if test_mode:
        band_names = band_names[:10]
        print(f"[TEST] Test mode: resolving first {len(band_names)} bands\n")
    else:
        print(f"[FULL] Full resolution mode: {len(band_names)} bands\n")

    # If resuming, start from the specified band
    start_idx = 0
    if resume_from_band is not None:
        start_idx = max(0, resume_from_band - 1)  # 1-indexed to 0-indexed
        print(f"[RESUME] Resuming from band {resume_from_band} (index {start_idx})\n")

    resolved_bands = []
    unresolved_bands = []
    current_delay = RATE_LIMIT_DELAY

    for i, name in enumerate(band_names, 1):
        if i <= start_idx:
            continue  # Skip already-resolved bands

        print(f"[{i}/{len(band_names)}] Resolving: {name}")

        result, current_delay = resolve_band(client, name, current_delay)
        result["name"] = name
        result["resolved_at"] = date.today().isoformat()

        if result.get("unresolved"):
            print(f"  ! Not found on Spotify")
            unresolved_bands.append({"name": name, "reason": "Not found on Spotify", "attempted_at": date.today().isoformat()})
        elif result["track_count"] == 0:
            print(f"  ! Zero tracks found (artist exists but no matching tracks)")
            unresolved_bands.append({"name": name, "reason": "Zero tracks found on Spotify", "attempted_at": date.today().isoformat()})
        elif result["track_count"] < 5:
            print(f"  ! Only {result['track_count']} track(s) found (below threshold)")
            unresolved_bands.append({"name": name, "reason": f"Below threshold: {result['track_count']} tracks", "attempted_at": date.today().isoformat()})
        else:
            print(f"  + {result['track_count']} tracks resolved")

        resolved_bands.append(result)

    # If resuming, merge with previously resolved bands
    if resume_from_band is not None:
        with DATA_FILE.open(encoding="utf-8") as f:
            existing = json.load(f)
        existing_bands = existing.get("bands", [])
        # Reconstruct: keep old format for non-object bands, append new resolved ones
        if existing_bands and isinstance(existing_bands[0], str):
            # Old format: insert resolved objects starting at start_idx
            data["bands"] = [
                {"name": b, "spotify_id": None, "tracks": [], "track_count": 0, "unresolved": True}
                if isinstance(b, str) else b
                for b in existing_bands[:start_idx]
            ] + resolved_bands
        else:
            data["bands"] = existing_bands[:start_idx] + resolved_bands
    else:
        data["bands"] = resolved_bands

    # Write updated JSON
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Write unresolved bands to a separate file for later handling
    if unresolved_bands:
        with UNRESOLVED_FILE.open("w", encoding="utf-8") as f:
            json.dump({"unresolved": unresolved_bands, "updated_at": date.today().isoformat()}, f, ensure_ascii=False, indent=2)
        print(f"\n[!] {len(unresolved_bands)} unresolved bands saved to {UNRESOLVED_FILE.name}")

    # Summary
    resolved_count = sum(1 for b in resolved_bands if not b.get("unresolved"))
    print(f"\n[OK] Resolution complete.")
    print(f"   Resolved: {resolved_count}")
    print(f"   Unresolved: {len(unresolved_bands)}")
    if resume_from_band is not None:
        print(f"   (resumed from band {resume_from_band})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve Spotify tracks for Wacken lineup bands.")
    parser.add_argument("--test", action="store_true", help="Test run: resolve only first 10 bands")
    parser.add_argument("--resume-from-band", type=int, help="Resume from band N (1-indexed)")

    args = parser.parse_args()

    run(test_mode=args.test, resume_from_band=args.resume_from_band)
