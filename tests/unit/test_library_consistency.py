"""Internal consistency tests for the library files (Phase 5+6).

After Phase 5+6 the resolver writes directly to ``library/spotify_tracks.json``
and the historic fat snapshot is gone. The library files are now the source
of truth — these tests are the guardrail against accidental drift between
the lineup pointer list and the per-source library files.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINEUP_DIR = ROOT / "wacken_playlist" / "data" / "lineups"
LIBRARY_DIR = ROOT / "wacken_playlist" / "data" / "library"


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def test_every_lineup_id_has_artist_entry():
    lineup = _load(LINEUP_DIR / "wacken_2026.json")
    artists = _load(LIBRARY_DIR / "artists.json")["artists"]
    for sid in lineup["bands"]:
        assert sid in artists, f"lineup ID {sid} missing from artists.json"


def test_every_lineup_id_has_tracks_entry():
    lineup = _load(LINEUP_DIR / "wacken_2026.json")
    tracks = _load(LIBRARY_DIR / "spotify_tracks.json")["artists"]
    for sid in lineup["bands"]:
        assert sid in tracks, f"lineup ID {sid} missing from spotify_tracks.json"


def test_no_orphan_artists_outside_lineup():
    """Every artist entry should correspond to a band in some lineup year."""
    artists = _load(LIBRARY_DIR / "artists.json")["artists"]
    lineup_ids: set[str] = set()
    for path in LINEUP_DIR.glob("wacken_*.json"):
        lineup_ids.update(_load(path).get("bands", []))
    orphans = set(artists.keys()) - lineup_ids
    assert not orphans, f"artists.json has IDs not referenced by any lineup: {sorted(orphans)}"


def test_no_orphan_tracks_outside_artists():
    """Every spotify_tracks entry must correspond to an artists.json entry."""
    artists = _load(LIBRARY_DIR / "artists.json")["artists"]
    tracks = _load(LIBRARY_DIR / "spotify_tracks.json")["artists"]
    orphans = set(tracks.keys()) - set(artists.keys())
    assert not orphans, f"spotify_tracks.json has IDs not in artists.json: {sorted(orphans)}"


def test_tracks_entries_have_required_shape():
    tracks = _load(LIBRARY_DIR / "spotify_tracks.json")["artists"]
    for sid, entry in tracks.items():
        assert isinstance(entry.get("tracks"), list), f"{sid}: tracks must be a list"
        assert entry.get("track_count") == len(entry["tracks"]), (
            f"{sid}: track_count {entry.get('track_count')} != len(tracks) {len(entry['tracks'])}"
        )
        for t in entry["tracks"]:
            assert "uri" in t and "name" in t, f"{sid}: track missing uri/name"


def test_setlists_reserved_and_empty():
    setlists = _load(LIBRARY_DIR / "setlists.json")
    assert setlists["artists"] == {}


def test_unresolved_entries_have_no_spotify_id_in_lineup():
    """library/unresolved.json holds only truly Spotify-less bands."""
    unresolved = _load(LIBRARY_DIR / "unresolved.json")
    artists = _load(LIBRARY_DIR / "artists.json")["artists"]
    artist_names = {entry["name"] for entry in artists.values()}
    for entry in unresolved.get("entries", []):
        assert entry["name"] not in artist_names, (
            f"{entry['name']} has a Spotify ID; belongs in spotify_tracks.json"
        )
