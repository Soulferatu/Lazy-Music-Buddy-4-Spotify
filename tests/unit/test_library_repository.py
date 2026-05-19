"""Unit tests for LibraryRepository (Phase 1+2 of the library refactor)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wacken_playlist.library import ArtistNotFoundError, LibraryRepository
from wacken_playlist.models import ArtistRecord, Track


@pytest.fixture
def fixture_lib(tmp_path: Path) -> Path:
    artists = {
        "_meta": {"description": "test", "updated_at": "2026-05-18"},
        "artists": {
            "id-real": {
                "name": "Real Band",
                "aliases": ["Real Band Hamburg"],
                "mbid": None,
                "override_source": None,
                "notes": None,
            },
            "id-override": {
                "name": "Generic Name",
                "aliases": [],
                "mbid": None,
                "override_source": "manual_2026-05-17",
                "notes": "Search picks wrong artist without override",
            },
            "id-perm": {
                "name": "Local Act",
                "aliases": [],
                "mbid": None,
                "override_source": None,
                "notes": None,
            },
        },
    }
    tracks = {
        "_meta": {"description": "test", "updated_at": "2026-05-18"},
        "artists": {
            "id-real": {
                "tracks": [
                    {"uri": "spotify:track:1", "name": "Song A"},
                    {"uri": "spotify:track:2", "name": "Song B"},
                ],
                "track_count": 2,
                "resolved_at": "2026-05-18",
            },
            "id-override": {
                "tracks": [{"uri": "spotify:track:3", "name": "Song C"}],
                "track_count": 1,
                "resolved_at": "2026-05-18",
            },
            "id-perm": {
                "tracks": [],
                "track_count": 0,
                "resolved_at": "2026-05-18",
                "permanently_unresolved": True,
                "note": "No Spotify presence",
            },
        },
    }
    unresolved = {
        "_meta": {"description": "test", "updated_at": "2026-05-18"},
        "entries": [],
    }
    setlists = {
        "_meta": {"description": "RESERVED", "updated_at": None},
        "artists": {},
    }

    (tmp_path / "artists.json").write_text(
        json.dumps(artists, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "spotify_tracks.json").write_text(
        json.dumps(tracks, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "unresolved.json").write_text(
        json.dumps(unresolved, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "setlists.json").write_text(
        json.dumps(setlists, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path


def test_get_artist_returns_typed_record(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    record = repo.get_artist("id-real")
    assert isinstance(record, ArtistRecord)
    assert record.spotify_id == "id-real"
    assert record.name == "Real Band"
    assert record.aliases == ("Real Band Hamburg",)
    assert record.override_source is None


def test_get_artist_carries_override_source(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    record = repo.get_artist("id-override")
    assert record.override_source == "manual_2026-05-17"


def test_get_artist_missing_raises(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    with pytest.raises(ArtistNotFoundError):
        repo.get_artist("id-nope")


def test_has_artist(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    assert repo.has_artist("id-real")
    assert not repo.has_artist("id-nope")


def test_get_tracks_returns_track_objects(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    tracks = repo.get_tracks("id-real")
    assert tracks == [
        Track(uri="spotify:track:1", name="Song A"),
        Track(uri="spotify:track:2", name="Song B"),
    ]


def test_get_tracks_empty_for_unknown(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    assert repo.get_tracks("id-nope") == []


def test_get_track_count(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    assert repo.get_track_count("id-real") == 2
    assert repo.get_track_count("id-perm") == 0


def test_is_permanently_unresolved(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    assert repo.is_permanently_unresolved("id-perm")
    assert not repo.is_permanently_unresolved("id-real")
    assert not repo.is_permanently_unresolved("id-nope")


def test_iter_artist_ids(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    ids = list(repo.iter_artist_ids())
    assert set(ids) == {"id-real", "id-override", "id-perm"}


def test_unresolved_names_empty_by_default(fixture_lib: Path):
    repo = LibraryRepository(data_dir=fixture_lib)
    assert repo.unresolved_names() == []


def test_reads_real_library_files():
    """Smoke test: the production library files load without error."""
    repo = LibraryRepository()
    ids = list(repo.iter_artist_ids())
    assert len(ids) > 0
    for sid in ids[:3]:
        record = repo.get_artist(sid)
        assert record.name
