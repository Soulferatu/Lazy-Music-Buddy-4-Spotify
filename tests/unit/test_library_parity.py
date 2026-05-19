"""Parity test for the library refactor (Phase 1+2, retained through Phase 4).

Asserts that ``data/library/*.json`` faithfully mirrors the archived
fat-format snapshot at ``raw/wacken_2026.fat.json`` plus
``artist_overrides.json`` and ``unresolved_bands.json``. Pre-cutover this
file lived at ``data/lineups/wacken_2026.json``; Phase 4 moved it. The
parity test will be retired in Phase 5+6 when the resolver writes
directly to ``library/`` and the fat snapshot can be deleted.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINEUP_DIR = ROOT / "wacken_playlist" / "data" / "lineups"
LIBRARY_DIR = ROOT / "wacken_playlist" / "data" / "library"
FAT_SNAPSHOT = ROOT / "raw" / "wacken_2026.fat.json"


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def test_every_band_in_artists_registry():
    wacken = _load(FAT_SNAPSHOT)
    artists = _load(LIBRARY_DIR / "artists.json")["artists"]

    assert len(wacken["bands"]) == len(artists)
    for band in wacken["bands"]:
        sid = band["spotify_id"]
        assert sid in artists, f"missing artist entry for {band['name']} ({sid})"
        assert artists[sid]["name"] == band["name"]


def test_track_lists_match_band_for_band():
    wacken = _load(FAT_SNAPSHOT)
    tracks_by_id = _load(LIBRARY_DIR / "spotify_tracks.json")["artists"]

    for band in wacken["bands"]:
        sid = band["spotify_id"]
        assert sid in tracks_by_id
        entry = tracks_by_id[sid]
        assert entry["tracks"] == band.get("tracks", [])
        assert entry["track_count"] == band.get("track_count")
        assert entry["resolved_at"] == band.get("resolved_at")


def test_override_source_flag_matches_overrides_file():
    wacken = _load(FAT_SNAPSHOT)
    overrides = _load(LINEUP_DIR / "artist_overrides.json")
    artists = _load(LIBRARY_DIR / "artists.json")["artists"]

    name_to_id = {b["name"]: b["spotify_id"] for b in wacken["bands"]}
    expected_override_ids = {
        name_to_id[name]
        for name in overrides["overrides"]
        if name in name_to_id
    }
    actual_override_ids = {
        sid for sid, entry in artists.items() if entry.get("override_source")
    }
    assert expected_override_ids == actual_override_ids


def test_permanently_unresolved_flag_migrated_to_tracks_file():
    unresolved = _load(LINEUP_DIR / "unresolved_bands.json")
    wacken = _load(FAT_SNAPSHOT)
    tracks_by_id = _load(LIBRARY_DIR / "spotify_tracks.json")["artists"]

    name_to_id = {b["name"]: b["spotify_id"] for b in wacken["bands"]}
    expected = {
        name_to_id[e["name"]]
        for e in unresolved["unresolved"]
        if e.get("permanently_unresolved") and e["name"] in name_to_id
    }
    actual = {
        sid for sid, entry in tracks_by_id.items()
        if entry.get("permanently_unresolved")
    }
    assert expected == actual


def test_aliases_pulled_from_dedup_decisions():
    wacken = _load(FAT_SNAPSHOT)
    artists = _load(LIBRARY_DIR / "artists.json")["artists"]

    name_to_id = {b["name"]: b["spotify_id"] for b in wacken["bands"]}
    for entry in wacken.get("notes", {}).get("dedup_decisions", []):
        kept = entry.get("kept")
        removed = entry.get("removed")
        if kept and removed and kept in name_to_id:
            sid = name_to_id[kept]
            assert removed in artists[sid]["aliases"], (
                f"alias {removed!r} not found on {kept!r}"
            )


def test_unresolved_entries_have_no_spotify_id_in_lineup():
    """library/unresolved.json holds only truly Spotify-less bands."""
    wacken = _load(FAT_SNAPSHOT)
    unresolved_lib = _load(LIBRARY_DIR / "unresolved.json")

    band_names = {b["name"] for b in wacken["bands"]}
    for entry in unresolved_lib["entries"]:
        assert entry["name"] not in band_names, (
            f"{entry['name']} has a Spotify ID; belongs in spotify_tracks.json"
        )


def test_setlists_reserved_and_empty():
    setlists = _load(LIBRARY_DIR / "setlists.json")
    assert setlists["artists"] == {}


def test_build_script_is_idempotent():
    """Re-running build_library.py must produce identical bytes."""
    import subprocess
    import sys

    before = {
        p.name: p.read_bytes()
        for p in LIBRARY_DIR.glob("*.json")
    }
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_library.py"), "--check"],
        capture_output=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, (
        f"build_library.py --check reported drift:\n"
        f"stdout: {result.stdout.decode(errors='replace')}\n"
        f"stderr: {result.stderr.decode(errors='replace')}"
    )
    after = {
        p.name: p.read_bytes()
        for p in LIBRARY_DIR.glob("*.json")
    }
    assert before == after
