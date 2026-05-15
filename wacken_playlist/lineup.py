from __future__ import annotations

import json
from pathlib import Path

from .models import Band


class LineupNotFoundError(LookupError):
    """Raised when a requested lineup year has no data file."""


class LineupRepository:
    """Reads festival lineups from JSON files under data/lineups/."""

    def __init__(self, data_dir: Path | None = None):
        self._data_dir = data_dir or Path(__file__).parent / "data" / "lineups"
        self._cache: dict[int, dict] = {}

    def _load(self, year: int) -> dict:
        if year in self._cache:
            return self._cache[year]
        path = self._data_dir / f"wacken_{year}.json"
        if not path.exists():
            raise LineupNotFoundError(f"No lineup data for year {year}")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        self._cache[year] = data
        return data

    def get_bands(self, year: int) -> list[Band]:
        data = self._load(year)
        return [Band(name=name, year=year) for name in data["bands"]]

    def get_band_names(self, year: int) -> list[str]:
        return list(self._load(year)["bands"])

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
        return name in self._load(year)["bands"]
