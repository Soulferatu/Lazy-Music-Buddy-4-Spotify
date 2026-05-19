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

    During the library refactor this class accepts two file shapes per year:

    * **Fat** ``wacken_YYYY.json`` — ``bands`` is a list of dicts with embedded
      tracks. Read directly without consulting the library. This is the
      pre-refactor format and remains the source of truth until Phase 4.
    * **Thin** ``wacken_YYYY.thin.json`` — ``bands`` is a list of Spotify artist
      ID strings; the lineup file only describes membership. Names and track
      data are joined in from :class:`LibraryRepository`. Read only when
      ``use_thin`` is True (driven by the ``USE_THIN_LINEUPS`` config flag).
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        library: LibraryRepository | None = None,
        use_thin: bool = False,
    ):
        self._data_dir = data_dir or Path(__file__).parent / "data" / "lineups"
        self._library = library
        self._use_thin = use_thin
        self._cache: dict[int, dict] = {}

    def _path_for(self, year: int) -> Path:
        if self._use_thin:
            return self._data_dir / f"wacken_{year}.thin.json"
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

    def _library_or_raise(self) -> LibraryRepository:
        if self._library is None:
            raise RuntimeError(
                "LineupRepository is in thin mode but no LibraryRepository "
                "was supplied. Pass one to __init__."
            )
        return self._library

    @staticmethod
    def _is_thin_shape(data: dict) -> bool:
        bands = data.get("bands", [])
        if not bands:
            # Empty list: assume the file shape matches the configured mode.
            return False
        return isinstance(bands[0], str)

    def _band_from_library(self, spotify_id: str, year: int) -> Band:
        library = self._library_or_raise()
        artist = library.get_artist(spotify_id)
        tracks = library.get_tracks(spotify_id)
        track_count = library.get_track_count(spotify_id)
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
            library = self._library_or_raise()
            for sid in bands_data:
                if library.has_artist(sid):
                    result.append(library.get_artist(sid).name)
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
        suffix = ".thin.json" if self._use_thin else ".json"
        years: list[int] = []
        for path in self._data_dir.glob("wacken_*.json"):
            is_thin_file = path.name.endswith(".thin.json")
            if self._use_thin != is_thin_file:
                continue
            stem = path.name[len("wacken_"):-len(suffix)]
            if stem.isdigit():
                years.append(int(stem))
        return sorted(years)

    def get_source_urls(self, year: int) -> list[str]:
        return list(self._load(year).get("source_urls", []))

    def is_valid_band(self, name: str, year: int) -> bool:
        return name in self.get_band_names(year)
