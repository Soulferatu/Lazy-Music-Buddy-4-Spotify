import re

import pytest

from wacken_playlist.lineup import LineupNotFoundError, LineupRepository
from wacken_playlist.models import Band


@pytest.fixture
def repo():
    return LineupRepository()


def test_get_bands_returns_band_objects_for_2026(repo):
    bands = repo.get_bands(2026)
    assert len(bands) >= 150
    assert all(isinstance(b, Band) for b in bands)
    assert all(b.year == 2026 for b in bands)


def test_get_band_names_includes_known_headliners(repo):
    names = repo.get_band_names(2026)
    for headliner in ["Def Leppard", "Judas Priest", "Sabaton", "Powerwolf"]:
        assert headliner in names


def test_is_valid_band(repo):
    assert repo.is_valid_band("Powerwolf", 2026) is True
    assert repo.is_valid_band("Not A Real Band", 2026) is False


def test_get_available_years_includes_2026(repo):
    assert 2026 in repo.get_available_years()


def test_get_source_urls_non_empty(repo):
    urls = repo.get_source_urls(2026)
    assert len(urls) > 0
    assert all(u.startswith("http") for u in urls)


def test_unknown_year_raises(repo):
    with pytest.raises(LineupNotFoundError):
        repo.get_bands(1999)


def _normalize(name: str) -> str:
    n = name.lower().strip()
    if n.startswith("the "):
        n = n[4:]
    return re.sub(r"[^a-z0-9]", "", n)


def test_no_exact_duplicates(repo):
    names = repo.get_band_names(2026)
    assert len(names) == len(set(names))


def test_no_normalized_duplicates(repo):
    """Catches near-duplicates like 'Ten56' vs 'Ten56.' that exact-match misses."""
    names = repo.get_band_names(2026)
    normalized = [_normalize(n) for n in names]
    seen: dict[str, str] = {}
    collisions = []
    for original, norm in zip(names, normalized):
        if norm in seen:
            collisions.append((seen[norm], original))
        else:
            seen[norm] = original
    assert collisions == [], f"Near-duplicate band names: {collisions}"
