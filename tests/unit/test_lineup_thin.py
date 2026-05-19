"""Phase 3 + 4 tests: LineupRepository against the thin-shape lineup file.

These exercise the read path in LineupRepository against the real
``wacken_2026.json`` (thin, post Phase 4 cutover) + the library produced
by build_library.py. After Phase 4 there is only one shape on disk;
the ``use_thin`` flag is vestigial and will be removed in Phase 6.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wacken_playlist.library import LibraryRepository
from wacken_playlist.lineup import LineupNotFoundError, LineupRepository
from wacken_playlist.models import Band


@pytest.fixture
def default_repo() -> LineupRepository:
    """Repository with the implicit auto-created LibraryRepository."""
    return LineupRepository()


@pytest.fixture
def thin_repo() -> LineupRepository:
    """Repository with explicit library + flag, as wired in production."""
    return LineupRepository(library=LibraryRepository(), use_thin=True)


def _bands_by_id(bands: list[Band]) -> dict[str, Band]:
    return {b.spotify_id: b for b in bands if b.spotify_id}


def test_thin_get_bands_matches_default_set(default_repo, thin_repo):
    fat = _bands_by_id(default_repo.get_bands(2026))
    thin = _bands_by_id(thin_repo.get_bands(2026))
    assert set(fat.keys()) == set(thin.keys())
    assert len(thin) == len(fat) == 169


def test_thin_band_matches_default_per_band(default_repo, thin_repo):
    fat = _bands_by_id(default_repo.get_bands(2026))
    thin = _bands_by_id(thin_repo.get_bands(2026))
    for sid, fat_band in fat.items():
        thin_band = thin[sid]
        assert thin_band.name == fat_band.name
        assert thin_band.year == fat_band.year == 2026
        assert thin_band.track_count == fat_band.track_count
        assert thin_band.tracks == fat_band.tracks


def test_thin_get_bands_is_alphabetical(thin_repo):
    bands = thin_repo.get_bands(2026)
    names = [b.name for b in bands]
    assert names == sorted(names, key=str.lower)


def test_thin_get_band_names_matches_default(default_repo, thin_repo):
    assert set(default_repo.get_band_names(2026)) == set(thin_repo.get_band_names(2026))


def test_thin_is_valid_band(thin_repo):
    assert thin_repo.is_valid_band("Powerwolf", 2026)
    assert thin_repo.is_valid_band("Judas Priest", 2026)
    assert not thin_repo.is_valid_band("Not A Real Band", 2026)


def test_thin_source_urls_preserved(default_repo, thin_repo):
    assert thin_repo.get_source_urls(2026) == default_repo.get_source_urls(2026)


def test_thin_get_available_years(thin_repo):
    years = thin_repo.get_available_years()
    assert 2026 in years
    # Fat .json files must not bleed in when use_thin=True.
    assert all(isinstance(y, int) for y in years)


def test_unknown_year_in_thin_mode_raises(thin_repo):
    with pytest.raises(LineupNotFoundError):
        thin_repo.get_bands(1999)


def test_thin_read_with_missing_library_raises_cleanly(tmp_path: Path):
    """A thin file with no library available raises ArtistNotFoundError or
    FileNotFoundError — never a silent miss."""
    from wacken_playlist.library import ArtistNotFoundError

    (tmp_path / "wacken_2099.json").write_text(
        json.dumps({"year": 2099, "bands": ["nope_id"], "source_urls": []}),
        encoding="utf-8",
    )
    # No library files written under tmp_path.parent / "library", so the
    # auto-created LibraryRepository will fail loudly on first lookup.
    repo = LineupRepository(data_dir=tmp_path)
    with pytest.raises((ArtistNotFoundError, FileNotFoundError)):
        repo.get_bands(2099)


def test_thin_notes_section_carries_withdrawals_and_non_band_entries():
    """The thin file retains editorial notes split per the locked schema."""
    path = Path("wacken_playlist/data/lineups/wacken_2026.json")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    notes = data["notes"]
    assert "withdrawals" in notes
    assert "non_band_entries" in notes
    withdrawal_names = [w["name"] for w in notes["withdrawals"]]
    assert "Nita Strauss" in withdrawal_names
    non_band_names = [n["name"] for n in notes["non_band_entries"]]
    assert "Maschine's Late Night Show" in non_band_names
