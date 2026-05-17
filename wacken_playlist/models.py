from dataclasses import dataclass, field


@dataclass(frozen=True)
class Band:
    """Represents a band playing at Wacken Open Air."""
    name: str
    year: int


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
