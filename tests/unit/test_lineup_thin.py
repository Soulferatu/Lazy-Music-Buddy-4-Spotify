"""LineupRepository tests against the thin lineup file + library join."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wacken_playlist.library import ArtistNotFoundError, LibraryRepository
from wacken_playlist.lineup import LineupNotFoundError, LineupRepository
from wacken_playlist.models import Band


@pytest.fixture
def default_repo() -> LineupRepository:
    """Repository with the implicit auto-created LibraryRepository."""
    return LineupRepository()


@pytest.fixture
def explicit_repo() -> LineupRepository:
    """Repository with an explicitly-supplied library, as wired by create_app."""
    return LineupRepository(library=LibraryRepository())


def _bands_by_id(bands: list[Band]) -> dict[str, Band]:
    return {b.spotify_id: b for b in bands if b.spotify_id}


def test_get_bands_matches_across_constructors(default_repo, explicit_repo):
    """Auto-created and explicit-library repos return identical data."""
    a = _bands_by_id(default_repo.get_bands(2026))
    b = _bands_by_id(explicit_repo.get_bands(2026))
    assert set(a.keys()) == set(b.keys())
    assert len(a) == len(b) == 169


def test_band_matches_across_constructors(default_repo, explicit_repo):
    a = _bands_by_id(default_repo.get_bands(2026))
    b = _bands_by_id(explicit_repo.get_bands(2026))
    for sid in a:
        assert b[sid].name == a[sid].name
        assert b[sid].year == a[sid].year == 2026
        assert b[sid].track_count == a[sid].track_count
        assert b[sid].tracks == a[sid].tracks


def test_get_bands_is_alphabetical(explicit_repo):
    bands = explicit_repo.get_bands(2026)
    names = [b.name for b in bands]
    assert names == sorted(names, key=str.lower)


def test_get_band_names_matches_across_constructors(default_repo, explicit_repo):
    assert set(default_repo.get_band_names(2026)) == set(explicit_repo.get_band_names(2026))


def test_is_valid_band(explicit_repo):
    assert explicit_repo.is_valid_band("Powerwolf", 2026)
    assert explicit_repo.is_valid_band("Judas Priest", 2026)
    assert not explicit_repo.is_valid_band("Not A Real Band", 2026)


def test_source_urls_preserved(default_repo, explicit_repo):
    assert explicit_repo.get_source_urls(2026) == default_repo.get_source_urls(2026)


def test_get_available_years(explicit_repo):
    years = explicit_repo.get_available_years()
    assert 2026 in years
    assert all(isinstance(y, int) for y in years)


def test_unknown_year_raises(explicit_repo):
    with pytest.raises(LineupNotFoundError):
        explicit_repo.get_bands(1999)


def test_read_with_missing_library_raises_cleanly(tmp_path: Path):
    """A lineup file with no library available raises clearly — never silent."""
    (tmp_path / "wacken_2099.json").write_text(
        json.dumps({"year": 2099, "bands": ["nope_id"], "source_urls": []}),
        encoding="utf-8",
    )
    repo = LineupRepository(data_dir=tmp_path)
    with pytest.raises((ArtistNotFoundError, FileNotFoundError)):
        repo.get_bands(2099)


def test_notes_section_carries_withdrawals_and_non_band_entries():
    """The lineup file retains editorial notes split per the locked schema."""
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
