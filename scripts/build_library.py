#!/usr/bin/env python3
"""
Build the normalized `data/library/` files from existing lineup data.

Part of the library refactor (Phase 1+2). Read-only with respect to the
sources; idempotent — re-running with no input change produces identical
output bytes. Nothing in the app reads these files yet; this script exists
so the parity test and the upcoming LibraryRepository have a target to read.

Sources:
  wacken_playlist/data/lineups/wacken_2026.json
  wacken_playlist/data/lineups/artist_overrides.json
  wacken_playlist/data/lineups/unresolved_bands.json

Outputs:
  wacken_playlist/data/library/artists.json
  wacken_playlist/data/library/spotify_tracks.json
  wacken_playlist/data/library/unresolved.json
  wacken_playlist/data/library/setlists.json (RESERVED — Stage 6)
  wacken_playlist/data/lineups/wacken_2026.thin.json (Phase 3: thin variant
      consumed when USE_THIN_LINEUPS is on; the fat wacken_2026.json
      remains the source of truth until Phase 4 cutover).

Usage:
  py scripts/build_library.py
  py scripts/build_library.py --check    # exit non-zero if output would change
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LINEUP_DIR = ROOT / "wacken_playlist" / "data" / "lineups"
LIBRARY_DIR = ROOT / "wacken_playlist" / "data" / "library"

WACKEN_FILE = LINEUP_DIR / "wacken_2026.json"
OVERRIDES_FILE = LINEUP_DIR / "artist_overrides.json"
UNRESOLVED_FILE = LINEUP_DIR / "unresolved_bands.json"

BUILD_DATE = "2026-05-18"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _dump_json(path: Path, data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _aliases_for(name: str, dedup: list[dict]) -> list[str]:
    aliases = []
    for entry in dedup:
        if entry.get("kept") == name and entry.get("removed"):
            aliases.append(entry["removed"])
    return aliases


def _override_names_to_ids(overrides_raw: dict, name_to_id: dict[str, str]) -> set[str]:
    """Return the set of Spotify IDs sourced from artist_overrides.json."""
    override_ids: set[str] = set()
    for name, _override_id in overrides_raw.get("overrides", {}).items():
        sid = name_to_id.get(name)
        if sid:
            override_ids.add(sid)
    return override_ids


def build_library() -> dict[str, dict]:
    wacken = _load_json(WACKEN_FILE)
    overrides = _load_json(OVERRIDES_FILE)
    unresolved = _load_json(UNRESOLVED_FILE)

    bands = wacken["bands"]
    dedup = wacken.get("notes", {}).get("dedup_decisions", [])

    name_to_id = {b["name"]: b["spotify_id"] for b in bands}
    override_ids = _override_names_to_ids(overrides, name_to_id)

    # unresolved_bands.json keyed by name → entry; flag carries to spotify_tracks
    unresolved_by_name = {e["name"]: e for e in unresolved.get("unresolved", [])}

    # ---- artists.json ----------------------------------------------------
    artists_entries: dict[str, dict] = {}
    for band in sorted(bands, key=lambda b: b["name"].lower()):
        sid = band["spotify_id"]
        artists_entries[sid] = {
            "name": band["name"],
            "aliases": _aliases_for(band["name"], dedup),
            "mbid": None,
            "override_source": "manual_2026-05-17" if sid in override_ids else None,
            "notes": None,
        }

    artists_doc = {
        "_meta": {
            "description": "Canonical artist registry. Keyed by Spotify artist ID.",
            "updated_at": BUILD_DATE,
        },
        "artists": artists_entries,
    }

    # ---- spotify_tracks.json --------------------------------------------
    tracks_entries: dict[str, dict] = {}
    for band in sorted(bands, key=lambda b: b["name"].lower()):
        sid = band["spotify_id"]
        entry: dict = {
            "tracks": band.get("tracks", []),
            "track_count": band.get("track_count", len(band.get("tracks", []))),
            "resolved_at": band.get("resolved_at"),
        }
        u = unresolved_by_name.get(band["name"])
        if u and u.get("permanently_unresolved"):
            entry["permanently_unresolved"] = True
            if u.get("note"):
                entry["note"] = u["note"]
        tracks_entries[sid] = entry

    tracks_doc = {
        "_meta": {
            "description": "Per-artist Spotify track cache. Keyed by Spotify artist ID.",
            "updated_at": BUILD_DATE,
        },
        "artists": tracks_entries,
    }

    # ---- unresolved.json -------------------------------------------------
    # Truly Spotify-less bands (no entry in wacken_2026.json). Today this set
    # is empty — every act in unresolved_bands.json has a Spotify ID. The
    # schema exists for future years.
    unresolved_doc = {
        "_meta": {
            "description": (
                "Bands with no Spotify presence at all. Bands that have an "
                "ID but no usable tracks live in spotify_tracks.json with "
                "permanently_unresolved=true."
            ),
            "updated_at": BUILD_DATE,
        },
        "entries": [],
    }

    # ---- setlists.json (reserved) ---------------------------------------
    setlists_doc = {
        "_meta": {
            "description": "RESERVED — populated in Stage 6 (setlist.fm).",
            "updated_at": None,
        },
        "artists": {},
    }

    # ---- thin lineup: wacken_2026.thin.json -----------------------------
    # Bands become a sorted array of Spotify IDs (alphabetical by canonical
    # name, case-insensitive — the same order used for artists.json /
    # spotify_tracks.json so the three files diff cleanly together).
    # Editorial entries from notes.dedup_decisions with kept=null move into
    # dedicated sections; alias entries (kept != null) live in artists.json.
    sorted_bands = sorted(bands, key=lambda b: b["name"].lower())
    withdrawals: list[dict] = []
    non_band_entries: list[dict] = []
    for entry in dedup:
        if entry.get("kept") is not None:
            continue
        name = entry.get("removed")
        reason = entry.get("reason", "")
        if not name:
            continue
        item = {"name": name, "reason": reason}
        if "withdrew" in reason.lower() or "withdrawal" in reason.lower():
            withdrawals.append(item)
        else:
            non_band_entries.append(item)

    thin_lineup = {
        "year": wacken.get("year"),
        "source_urls": list(wacken.get("source_urls", [])),
        "notes": {
            "withdrawals": withdrawals,
            "non_band_entries": non_band_entries,
        },
        "bands": [b["spotify_id"] for b in sorted_bands],
        "unresolved_names": [],
    }

    return {
        "artists.json": (LIBRARY_DIR, artists_doc),
        "spotify_tracks.json": (LIBRARY_DIR, tracks_doc),
        "unresolved.json": (LIBRARY_DIR, unresolved_doc),
        "setlists.json": (LIBRARY_DIR, setlists_doc),
        "wacken_2026.thin.json": (LINEUP_DIR, thin_lineup),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if regenerating the library would change any file.",
    )
    args = parser.parse_args()

    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    LINEUP_DIR.mkdir(parents=True, exist_ok=True)

    files = build_library()
    drift = False
    for name, (target_dir, doc) in files.items():
        path = target_dir / name
        new_bytes = _dump_json(path, doc)
        old_bytes = path.read_bytes() if path.exists() else None
        if old_bytes == new_bytes:
            print(f"  unchanged  {name}")
            continue
        drift = True
        if args.check:
            print(f"  WOULD WRITE  {name}")
        else:
            path.write_bytes(new_bytes)
            print(f"  wrote      {name}")

    if args.check and drift:
        print("Library files would change. Re-run without --check to update.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
