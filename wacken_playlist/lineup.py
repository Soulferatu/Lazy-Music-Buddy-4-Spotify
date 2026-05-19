from __future__ import annotations

import json
from pathlib import Path

from .library import LibraryRepository
from .models import Band


class LineupNotFoundError(LookupError):
    """Raised when a requested lineup year has no data file."""


class LineupRepository:
    """Reads festival lineups from JSON files under ``data/lineups/``.

    The lineup file is a thin pointer list — ``bands`` holds Spotify artist
    IDs, and per-artist data (name, tracks) is joined in from
    :class:`LibraryRepository`. The fat-shape branch and the
    ``USE_THIN_LINEUPS`` flag were retired in Phase 5+6 of the library
    refactor; see ``wiki/library_refactor.md``.
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        library: LibraryRepository | None = None,
    ):
        self._data_dir = data_dir or Path(__file__).parent / "data" / "lineups"
        if library is None:
            library = LibraryRepository(data_dir=self._data_dir.parent / "library")
        self._library = library
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
        return [self._band_from_library(sid, year) for sid in data.get("bands", [])]

    def get_band_names(self, year: int) -> list[str]:
        data = self._load(year)
        return [
            self._library.get_artist(sid).name
            for sid in data.get("bands", [])
            if self._library.has_artist(sid)
        ]

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
