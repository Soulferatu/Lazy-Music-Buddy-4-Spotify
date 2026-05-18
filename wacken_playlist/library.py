"""LibraryRepository — read-only view onto data/library/*.json.

Part of the library refactor (Phase 1+2). At this phase nothing else in
the app consumes this class; it exists so the upcoming dual-path
LineupRepository (Phase 3) and the rewritten resolver (Phase 5+6) have a
single typed entry point to the normalized library files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import ArtistRecord, Track


class ArtistNotFoundError(LookupError):
    """Raised when a Spotify artist ID has no entry in artists.json."""


class LibraryRepository:
    """Reads the normalized library files under data/library/."""

    ARTISTS_FILE = "artists.json"
    TRACKS_FILE = "spotify_tracks.json"
    UNRESOLVED_FILE = "unresolved.json"
    SETLISTS_FILE = "setlists.json"

    def __init__(self, data_dir: Path | None = None):
        self._data_dir = data_dir or Path(__file__).parent / "data" / "library"
        self._artists: Optional[dict] = None
        self._tracks: Optional[dict] = None
        self._unresolved: Optional[dict] = None

    def _load(self, filename: str) -> dict:
        with (self._data_dir / filename).open(encoding="utf-8") as f:
            return json.load(f)

    def _artists_doc(self) -> dict:
        if self._artists is None:
            self._artists = self._load(self.ARTISTS_FILE)
        return self._artists

    def _tracks_doc(self) -> dict:
        if self._tracks is None:
            self._tracks = self._load(self.TRACKS_FILE)
        return self._tracks

    def _unresolved_doc(self) -> dict:
        if self._unresolved is None:
            self._unresolved = self._load(self.UNRESOLVED_FILE)
        return self._unresolved

    def get_artist(self, spotify_id: str) -> ArtistRecord:
        entry = self._artists_doc()["artists"].get(spotify_id)
        if entry is None:
            raise ArtistNotFoundError(spotify_id)
        return ArtistRecord(
            spotify_id=spotify_id,
            name=entry["name"],
            aliases=tuple(entry.get("aliases", [])),
            mbid=entry.get("mbid"),
            override_source=entry.get("override_source"),
            notes=entry.get("notes"),
        )

    def has_artist(self, spotify_id: str) -> bool:
        return spotify_id in self._artists_doc()["artists"]

    def get_tracks(self, spotify_id: str) -> list[Track]:
        entry = self._tracks_doc()["artists"].get(spotify_id)
        if entry is None:
            return []
        return [Track(uri=t["uri"], name=t["name"]) for t in entry.get("tracks", [])]

    def get_track_count(self, spotify_id: str) -> int:
        entry = self._tracks_doc()["artists"].get(spotify_id)
        if entry is None:
            return 0
        return int(entry.get("track_count", len(entry.get("tracks", []))))

    def is_permanently_unresolved(self, spotify_id: str) -> bool:
        entry = self._tracks_doc()["artists"].get(spotify_id)
        return bool(entry and entry.get("permanently_unresolved"))

    def iter_artist_ids(self):
        return iter(self._artists_doc()["artists"].keys())

    def unresolved_names(self) -> list[str]:
        """Names of bands with no Spotify presence at all."""
        return [e["name"] for e in self._unresolved_doc().get("entries", [])]
