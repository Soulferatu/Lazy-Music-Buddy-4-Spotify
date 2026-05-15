"""setlist.fm API client stub. Implementation lands in Stage 6."""
from __future__ import annotations


class SetlistFmClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_latest_setlist(self, artist_name: str) -> list[str] | None:
        raise NotImplementedError("setlist.fm lookup lands in Stage 6.")
