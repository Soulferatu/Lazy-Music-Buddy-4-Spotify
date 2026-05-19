from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

from .library import LibraryRepository
from .models import Band, Track


class LineupNotFoundError(LookupError):
    """Raised when a requested lineup year has no data file."""


class LineupRepository:
    """Reads festival lineups from JSON files under data/lineups/.

    Both lineup shapes are accepted on a per-item basis so the dual-path
    survives across the refactor and into tests that exercise either form:

    * **Thin** — ``bands`` is a list of Spotify artist ID strings. Names and
      track data are joined in from :class:`LibraryRepository`. This is the
      shape on disk in production after the Phase 4 cutover.
    * **Fat** — ``bands`` is a list of dicts with embedded tracks. Kept
      working through Phase 4 so test fixtures and the archived
      ``raw/wacken_2026.fat.json`` remain readable. Removed in Phase 5+6.

    The ``use_thin`` flag is retained from Phase 3 but no longer drives the
    filename — both shapes live in ``wacken_YYYY.json`` after cutover. The
    flag will be deleted in Phase 6.
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        library: LibraryRepository | None = None,
        use_thin: bool = False,
    ):
        self._data_dir = data_dir or Path(__file__).parent / "data" / "lineups"
        if library is None:
            library_dir = self._data_dir.parent / "library"
            library = LibraryRepository(data_dir=library_dir)
        self._library = library
        self._use_thin = use_thin
        self._cache: dict[int, dict] = {}

    def _path_for(self, year: int) -> Path:
        return self._data_dir / f"wacken_{year}.json"

    def _load(self, year: int) -> dict:
        if year in self._cache:
            return self._cache[year]
        path = self._path_for(year)
        if not path.exists():
            raise LineupNotFoundError(f"No lineup data for year {year}")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        self._cache[year] = data
        return data

    def _band_from_library(self, spotify_id: str, year: int) -> Band:
        artist = self._library.get_artist(spotify_id)
        tracks = self._library.get_tracks(spotify_id)
        track_count = self._library.get_track_count(spotify_id)
        return Band(
            name=artist.name,
            year=year,
            spotify_id=spotify_id,
            tracks=tuple(tracks),
            track_count=track_count,
            unresolved=False,
        )

    def get_bands(self, year: int) -> list[Band]:
        data = self._load(year)
        bands_data = data.get("bands", [])
        result: list[Band] = []

        for item in bands_data:
            if isinstance(item, str):
                result.append(self._band_from_library(item, year))
            elif isinstance(item, dict):
                result.append(Band(
                    name=item.get("name", ""),
                    year=year,
                    spotify_id=item.get("spotify_id"),
                    tracks=tuple(
                        Track(uri=t["uri"], name=t["name"])
                        for t in item.get("tracks", [])
                    ),
                    track_count=item.get("track_count", 0),
                    unresolved=item.get("unresolved", False),
                ))

        return result

    def get_band_names(self, year: int) -> list[str]:
        data = self._load(year)
        bands_data = data.get("bands", [])
        result: list[str] = []

        if bands_data and isinstance(bands_data[0], str):
            for sid in bands_data:
                if self._library.has_artist(sid):
                    result.append(self._library.get_artist(sid).name)
            return result

        for item in bands_data:
            if isinstance(item, str):
                # Legacy plain-string format (pre-resolution). Treated as a name.
                result.append(item)
            elif isinstance(item, dict):
                name = item.get("name", "")
                if name:
                    result.append(name)

        return result

    def get_available_years(self) -> list[int]:
        if not self._data_dir.exists():
            return []
        years: list[int] = []
        for path in self._data_dir.glob("wacken_*.json"):
            stem = path.stem.removeprefix("wacken_")
            if stem.isdigit():
                years.append(int(stem))
        return sorted(years)

    def get_source_urls(self, year: int) -> list[str]:
        return list(self._load(year).get("source_urls", []))

    def is_valid_band(self, name: str, year: int) -> bool:
        return name in self.get_band_names(year)
