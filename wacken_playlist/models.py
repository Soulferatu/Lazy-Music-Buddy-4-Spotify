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


@dataclass
class PlaylistPreview:
    """Represents a preview of the playlist before creation."""
    playlist_name: str
    bands: list[Band]
    track_count: int


@dataclass
class PlaylistResult:
    """Represents the final result of playlist creation."""
    playlist_name: str
    spotify_url: str
    track_count: int
    skipped_bands: list[str] = field(default_factory=list)
