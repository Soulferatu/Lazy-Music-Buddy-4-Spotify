from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Track:
    """Represents a Spotify track."""
    uri: str
    name: str


@dataclass(frozen=True)
class ArtistRecord:
    """Canonical artist registry entry from data/library/artists.json."""
    spotify_id: str
    name: str
    aliases: tuple[str, ...] = ()
    mbid: Optional[str] = None
    override_source: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class Band:
    """Represents a band playing at Wacken Open Air."""
    name: str
    year: int
    spotify_id: Optional[str] = None
    tracks: tuple[Track, ...] = field(default_factory=tuple)
    track_count: int = 0
    unresolved: bool = False
    # `permanently_unresolved` + `unresolved_reason` mirror the
    # spotify_tracks.json fields. The reason is one of:
    #   - "wacken_local_or_tribute": Wacken house act or tribute band
    #     with no real Spotify presence.
    #   - "thin_catalog": real artist whose entire Spotify catalog is
    #     just a handful of tracks (e.g. Heavysaurus, 2 unique songs).
    # Both are surfaced in the UI so users know what to expect before
    # building a playlist.
    permanently_unresolved: bool = False
    unresolved_reason: Optional[str] = None


@dataclass
class PlaylistRequest:
    """Represents a user's request to build a playlist."""
    playlist_name: str
    bands: list[Band]
    language: str = "en"
    song_source: str = "spotify_top"
    excluded_uris: list[str] = field(default_factory=list)


@dataclass
class MatchedBand:
    """A band that resolved to a Spotify artist plus its preview tracks."""
    band: Band
    artist_id: str
    artist_name: str
    tracks: list[dict] = field(default_factory=list)


@dataclass
class PlaylistPreview:
    """Represents a preview of the playlist before creation."""
    playlist_name: str
    bands: list[Band]
    track_count: int
    matched: list[MatchedBand] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)


@dataclass
class PlaylistResult:
    """Represents the final result of playlist creation."""
    playlist_name: str
    spotify_url: str
    track_count: int
    skipped_bands: list[str] = field(default_factory=list)
