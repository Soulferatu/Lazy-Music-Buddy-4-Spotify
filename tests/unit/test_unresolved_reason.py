"""Tests for the permanently-unresolved UX (badge + warning copy).

Covers the data path (spotify_tracks.json → LibraryRepository →
LineupRepository → Band) and the per-reason consistency rules.
"""

from __future__ import annotations

import json
from pathlib import Path

from wacken_playlist.library import LibraryRepository
from wacken_playlist.lineup import LineupRepository

ROOT = Path(__file__).resolve().parents[2]
TRACKS_FILE = ROOT / "wacken_playlist" / "data" / "library" / "spotify_tracks.json"

VALID_REASONS = {"wacken_local_or_tribute", "thin_catalog"}


def _load_tracks() -> dict:
    with TRACKS_FILE.open(encoding="utf-8") as f:
        return json.load(f)["artists"]


def test_every_permanently_unresolved_entry_has_a_reason():
    """No silent flagging — every permanently_unresolved entry must
    declare *why* so the UI can render the right warning copy."""
    tracks = _load_tracks()
    for sid, entry in tracks.items():
        if entry.get("permanently_unresolved"):
            assert entry.get("unresolved_reason") in VALID_REASONS, (
                f"{sid}: permanently_unresolved without a valid unresolved_reason "
                f"(got {entry.get('unresolved_reason')!r})"
            )


def test_reasons_are_only_set_when_permanently_unresolved():
    tracks = _load_tracks()
    for sid, entry in tracks.items():
        if entry.get("unresolved_reason") is not None:
            assert entry.get("permanently_unresolved"), (
                f"{sid}: has unresolved_reason but isn't flagged permanently_unresolved"
            )


def test_library_repository_returns_reason():
    library = LibraryRepository()
    # Wacken Firefighters — Wacken-local act
    assert library.is_permanently_unresolved("064R2a2ptevrnJHc5Tao56")
    assert library.unresolved_reason("064R2a2ptevrnJHc5Tao56") == "wacken_local_or_tribute"
    # Heavysaurus — thin catalog
    assert library.is_permanently_unresolved("6uyCfgv8FWIc2mifriVXqw")
    assert library.unresolved_reason("6uyCfgv8FWIc2mifriVXqw") == "thin_catalog"


def test_library_reason_none_for_normal_artists():
    library = LibraryRepository()
    # Powerwolf — fully resolved, 10 tracks
    assert not library.is_permanently_unresolved("5HFkc3t0HYETL4JeEbDB1v")
    assert library.unresolved_reason("5HFkc3t0HYETL4JeEbDB1v") is None


def test_band_objects_carry_reason_through_lineup():
    repo = LineupRepository()
    bands = {b.name: b for b in repo.get_bands(2026)}

    firefighters = bands["Wacken Firefighters"]
    assert firefighters.permanently_unresolved
    assert firefighters.unresolved_reason == "wacken_local_or_tribute"

    heavysaurus = bands["Heavysaurus"]
    assert heavysaurus.permanently_unresolved
    assert heavysaurus.unresolved_reason == "thin_catalog"

    powerwolf = bands["Powerwolf"]
    assert not powerwolf.permanently_unresolved
    assert powerwolf.unresolved_reason is None


def test_i18n_keys_present_in_both_languages():
    i18n_dir = ROOT / "wacken_playlist" / "i18n"
    required_keys = {
        "band_badge_local_or_tribute",
        "band_badge_thin_catalog",
        "limited_presence_heading",
        "limited_presence_local_or_tribute_explanation",
        "limited_presence_thin_catalog_explanation",
    }
    for lang in ("en.json", "pt-BR.json"):
        with (i18n_dir / lang).open(encoding="utf-8") as f:
            data = json.load(f)
        missing = required_keys - set(data.keys())
        assert not missing, f"{lang}: missing i18n keys {missing}"
