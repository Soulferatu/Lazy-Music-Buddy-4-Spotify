"""Tests for the resolver's release-variant title normalization.

The hardened dedup keeps the first occurrence of each base title so the
playlist doesn't surface "Hysteria" + "Hysteria - Remastered 2017" as
two separate tracks. The trade-off (two distinct songs that happen to
share a base title collapse) is documented in
wiki/band_track_resolution.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.resolve_lineup import _normalize_title  # noqa: E402


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Hysteria", "hysteria"),
        ("Hysteria - Remastered 2017", "hysteria"),
        ("Hysteria - Remaster 2017", "hysteria"),
        ("Pour Some Sugar On Me", "pour some sugar on me"),
        ("Pour Some Sugar On Me - Remastered 2017", "pour some sugar on me"),
        ("The Final Countdown", "the final countdown"),
        ("The Final Countdown 2025", "the final countdown"),
        ("Hocus Pocus", "hocus pocus"),
        ("Hocus Pocus - Extended Version", "hocus pocus"),
        ("Hocus Pocus (Extended Version)", "hocus pocus"),
        ("Mdma", "mdma"),
        ("Mdma - Radio Edit", "mdma"),
        ("Loving the Dead", "loving the dead"),
        ("Loving the Dead (Radio Edit)", "loving the dead"),
        ("Asi mit Niwoh", "asi mit niwoh"),
        ("Asi mit Niwoh (Live)", "asi mit niwoh"),
        # Bracketed suffixes also strip.
        ("Song Name [Bonus Track]", "song name"),
        # Trailing-year style.
        ("Symphony 1999", "symphony"),
        # Casing + extra whitespace normalize.
        ("  WAR PIGS  ", "war pigs"),
        # Title that's just a remix tag stays distinct.
        ("Remix", "remix"),  # no leading " - "
        # Numbers in middle of title are preserved.
        ("3 Minutes to Midnight", "3 minutes to midnight"),
    ],
)
def test_normalize_collapses_release_variants(raw, expected):
    assert _normalize_title(raw) == expected


def test_normalize_two_known_dupes_collapse_together():
    """The two halves of each historical duplicate pair must share a key."""
    pairs = [
        ("Pour Some Sugar On Me", "Pour Some Sugar On Me - Remastered 2017"),
        ("Love Bites", "Love Bites - Remastered 2017"),
        ("The Final Countdown", "The Final Countdown 2025"),
        ("Hocus Pocus", "Hocus Pocus - Extended Version"),
        ("Mdma", "Mdma - Radio Edit"),
        ("Loving the Dead", "Loving the Dead (Radio Edit)"),
        ("Asi mit Niwoh", "Asi mit Niwoh (Live)"),
    ]
    for a, b in pairs:
        assert _normalize_title(a) == _normalize_title(b), (
            f"expected dedup match: {a!r} vs {b!r} "
            f"(got {_normalize_title(a)!r} vs {_normalize_title(b)!r})"
        )
