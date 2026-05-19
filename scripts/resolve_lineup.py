#!/usr/bin/env python3
"""
Resolve Spotify tracks for Wacken Open Air lineup bands.

Phase 5+6 of the library refactor: this script is now the **canonical writer**
for ``wacken_playlist/data/library/spotify_tracks.json``. The lineup file
(``wacken_playlist/data/lineups/wacken_YYYY.json``) is read-only — it gives
us the set of Spotify artist IDs we should keep tracks for. Canonical
artist names come from ``wacken_playlist/data/library/artists.json``.

Outputs are written to ``library/spotify_tracks.json``. Bands with a known
``permanently_unresolved=True`` flag are skipped by every retry mode so
known-Spotify-thin artists (Heavysaurus, Wacken Firefighters, …) don't churn.

Usage:
  py scripts/resolve_lineup.py                          # Full resolution (all artists in lineup)
  py scripts/resolve_lineup.py --test                   # Test run (first 10 artists)
  py scripts/resolve_lineup.py --resume-from-band 50    # Resume from band N (1-indexed, alphabetical order)
  py scripts/resolve_lineup.py --retry-unresolved       # Re-resolve any artist with < 5 tracks (excluding permanently_unresolved)
  py scripts/resolve_lineup.py --retry-unresolved --below-threshold-only
                                                        # Same, but skip zero-track artists too (only 1-4 retries)
  py scripts/resolve_lineup.py --retry-low-count 5      # Re-resolve only artists at exactly N tracks (idempotent)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from wacken_playlist.services.spotify import SpotifyClient


RATE_LIMIT_DELAY = 1.5
MAX_TRACKS = 10
MAX_PAGES_ARTIST = 5
MAX_PAGES_PLAIN = 5

# Release-variant tokens that follow a " - " separator on Spotify track
# titles. Examples that collapse to the same song:
#   "Hysteria"  ==  "Hysteria - Remastered 2017"
#   "Mdma"      ==  "Mdma - Radio Edit"
_VARIANT_TOKENS = (
    "remaster", "remastered",
    "remix",
    "live",
    "acoustic",
    "version",
    "edit",
    "mix",
    "single",
    "radio",
    "extended",
    "demo",
    "instrumental",
    "mono",
    "stereo",
)
_VARIANT_DASH_RE = re.compile(
    r"\s*-\s*(?:" + "|".join(_VARIANT_TOKENS) + r")\b.*$",
    re.IGNORECASE,
)
_TRAILING_YEAR_RE = re.compile(r"\s+\d{4}\s*$")


def _normalize_title(name: str) -> str:
    """Collapse release-variant titles down to a stable dedup key.

    Examples:
        "The Final Countdown"            -> "the final countdown"
        "The Final Countdown 2025"       -> "the final countdown"
        "Hysteria - Remastered 2017"     -> "hysteria"
        "Hocus Pocus (Extended Version)" -> "hocus pocus"
        "Loving the Dead (Radio Edit)"   -> "loving the dead"
        "Asi mit Niwoh (Live)"           -> "asi mit niwoh"

    Two distinct songs that happen to share a base title (rare) will
    collide and the second one loses — this is the same trade-off as
    the original case-insensitive dedup, documented in
    wiki/band_track_resolution.md.
    """
    n = name.lower()
    # Strip parenthetical / bracketed suffixes (multiple passes for nested).
    while True:
        new = re.sub(r"\s*\([^)]*\)", "", n)
        new = re.sub(r"\s*\[[^\]]*\]", "", new)
        if new == n:
            break
        n = new
    # Strip "- Remaster/Remix/Live/..." trailing suffixes.
    n = _VARIANT_DASH_RE.sub("", n)
    # Strip a trailing standalone year (e.g. "Song 2025").
    n = _TRAILING_YEAR_RE.sub("", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n

ROOT = Path(__file__).parent.parent
LINEUP_FILE = ROOT / "wacken_playlist" / "data" / "lineups" / "wacken_2026.json"
ARTISTS_FILE = ROOT / "wacken_playlist" / "data" / "library" / "artists.json"
TRACKS_FILE = ROOT / "wacken_playlist" / "data" / "library" / "spotify_tracks.json"


# ─────────────────────────────────────────────────────────────────────
# Spotify track collection (artist-ID-filtered, two-strategy)
# ─────────────────────────────────────────────────────────────────────


def _collect_tracks_for_artist(
    client: SpotifyClient,
    search_query: str,
    artist_id: str,
    delay: float,
) -> tuple[list[dict], float]:
    """Run two search strategies and return up to MAX_TRACKS tracks filtered
    by artist ID.

    Strategy 1: ``artist:"NAME"`` qualifier (up to MAX_PAGES_ARTIST pages).
    Strategy 2: plain-text ``NAME`` query (up to MAX_PAGES_PLAIN pages).

    Dedup is by URI and case-insensitive title — Spotify often returns
    multiple URIs for the same song (single / album / compilation /
    remaster); keeping the first per title avoids back-to-back duplicates.
    """
    seen_uris: set[str] = set()
    seen_titles: set[str] = set()
    collected: list[dict] = []

    def _accept(track: dict) -> bool:
        artists = track.get("artists") or []
        if not any(a.get("id") == artist_id for a in artists):
            return False
        uri = track.get("uri", "")
        if not uri or uri in seen_uris:
            return False
        title_key = _normalize_title(track.get("name", "") or "")
        if title_key and title_key in seen_titles:
            return False
        seen_uris.add(uri)
        if title_key:
            seen_titles.add(title_key)
        return True

    for page in range(MAX_PAGES_ARTIST):
        if len(collected) >= MAX_TRACKS:
            break
        results = client.search_tracks_by_artist(search_query, limit=10, offset=page * 10)
        page_hits = 0
        for track in results:
            if _accept(track):
                collected.append({"uri": track["uri"], "name": track.get("name", "")})
                page_hits += 1
                if len(collected) >= MAX_TRACKS:
                    break
        time.sleep(delay)
        if len(results) < 10 and page_hits == 0:
            break

    for page in range(MAX_PAGES_PLAIN):
        if len(collected) >= MAX_TRACKS:
            break
        results = client.search_tracks_plain(search_query, limit=10, offset=page * 10)
        page_hits = 0
        for track in results:
            if _accept(track):
                collected.append({"uri": track["uri"], "name": track.get("name", "")})
                page_hits += 1
                if len(collected) >= MAX_TRACKS:
                    break
        time.sleep(delay)
        if not results:
            break

    return collected[:MAX_TRACKS], delay


def _collect_tracks_via_albums(
    client: SpotifyClient,
    artist_id: str,
    delay: float,
) -> tuple[list[dict], float]:
    """Fallback for artists whose Spotify-side name doesn't match the
    project's canonical name (so search returns nothing tagged to them).

    Walks ``/v1/artists/{id}/albums`` (album + single groups) and
    ``/v1/albums/{id}/tracks`` for each. Dedups by URI and case-insensitive
    title, capped at MAX_TRACKS. Stays artist-ID-filtered: a track is only
    accepted if the target artist appears on it.

    Used when the search path returns zero tracks. Examples: 9mm Headshot
    (Spotify name "9MM") and any future case where the project name and
    the Spotify display name diverge.
    """
    token = client.get_client_credentials_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Walk albums (album+single only; skip compilations/appears_on to avoid
    # tribute/cover noise).
    albums: list[dict] = []
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?include_groups=album,single"
    while url:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            print(f"  ! albums fetch failed: HTTP {r.status_code}")
            break
        d = r.json()
        albums.extend(d.get("items", []))
        url = d.get("next")
        time.sleep(delay)

    seen_uris: set[str] = set()
    seen_titles: set[str] = set()
    collected: list[dict] = []

    for album in albums:
        if len(collected) >= MAX_TRACKS:
            break
        r = requests.get(
            f"https://api.spotify.com/v1/albums/{album['id']}/tracks",
            headers=headers,
            timeout=10,
        )
        if r.status_code != 200:
            print(f"  ! album {album['id']} tracks fetch failed: HTTP {r.status_code}")
            continue
        for t in r.json().get("items", []):
            if len(collected) >= MAX_TRACKS:
                break
            if not any(a.get("id") == artist_id for a in t.get("artists", [])):
                continue
            uri = t.get("uri", "")
            title = (t.get("name") or "").strip()
            title_key = _normalize_title(title)
            if not uri or uri in seen_uris:
                continue
            if title_key in seen_titles:
                continue
            seen_uris.add(uri)
            if title_key:
                seen_titles.add(title_key)
            collected.append({"uri": uri, "name": title})
        time.sleep(delay)

    return collected[:MAX_TRACKS], delay


def _resolve_one(
    client: SpotifyClient,
    artist_id: str,
    search_query: str,
    current_delay: float,
) -> tuple[list[dict], float]:
    """Resolve up to MAX_TRACKS for one artist. Returns (tracks, updated_delay).

    Tries search first (artist-qualifier + plain text). If search yields
    zero tracks tagged to the artist, falls back to walking the artist's
    albums via ``/v1/artists/{id}/albums`` — handles cases where the
    project name diverges from the Spotify display name (e.g. 9mm Headshot
    vs Spotify's "9MM").

    On rate-limit errors, backs off the inter-band delay; on other errors,
    returns an empty list and the unchanged delay so the caller can keep
    the existing entry.
    """
    try:
        tracks, delay = _collect_tracks_for_artist(
            client, search_query, artist_id, current_delay
        )
        if tracks:
            return tracks, delay
        # Search couldn't surface anything for this artist ID. Fall back to
        # the albums walk before declaring the artist unresolvable.
        print(f"  ~ search returned 0; trying /artists/{{id}}/albums fallback")
        return _collect_tracks_via_albums(client, artist_id, delay)
    except Exception as e:
        if "429" in str(e) or "rate" in str(e).lower():
            new_delay = min(current_delay * 1.5, 30)
            print(f"  ! Rate limit; increasing delay to {new_delay:.1f}s")
            return [], new_delay
        print(f"  X Error resolving {search_query}: {e}")
        return [], current_delay


# ─────────────────────────────────────────────────────────────────────
# Library file I/O
# ─────────────────────────────────────────────────────────────────────


def _load_lineup_ids() -> list[str]:
    """Return Spotify artist IDs from the thin lineup file."""
    with LINEUP_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get("bands", []))


def _load_artists() -> dict[str, dict]:
    """Return the artists registry: spotify_id → entry."""
    with ARTISTS_FILE.open(encoding="utf-8") as f:
        return json.load(f)["artists"]


def _load_tracks_doc() -> dict:
    """Return the full spotify_tracks.json document (with _meta)."""
    with TRACKS_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def _save_tracks_doc(doc: dict) -> None:
    """Write spotify_tracks.json with stable formatting."""
    doc["_meta"]["updated_at"] = date.today().isoformat()
    with TRACKS_FILE.open("w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _spotify_client() -> SpotifyClient:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return SpotifyClient(
        client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", ""),
    )


def _probe_spotify(client: SpotifyClient) -> bool:
    """Single benign Spotify call to check for rate-limit / shadow-ban
    before a batch run. Returns True if reachable, False otherwise.
    Memory rule: always probe before a batch retry."""
    try:
        artist = client.search_artist("Iron Maiden")
        ok = bool(artist and artist.get("id"))
        print(f"[PROBE] Spotify reachable: {ok} ({artist.get('name') if artist else 'no result'})")
        return ok
    except Exception as e:
        print(f"[PROBE] Spotify probe FAILED: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────
# Resolution modes
# ─────────────────────────────────────────────────────────────────────


def _resolve_ids(
    target_ids: list[str],
    artists: dict[str, dict],
    tracks_doc: dict,
    *,
    label: str,
    require_improvement: bool = False,
) -> None:
    """Resolve a list of artist IDs and update tracks_doc in-place.

    If ``require_improvement`` is True, an entry is only overwritten when
    the new pass returns strictly more tracks than the previous count.
    """
    client = _spotify_client()
    if not _probe_spotify(client):
        print("Aborting: Spotify probe failed. Retry once the rate-limit clears.")
        sys.exit(2)

    tracks = tracks_doc["artists"]
    today = date.today().isoformat()
    current_delay = RATE_LIMIT_DELAY
    improved: list[tuple[str, int, int]] = []
    unchanged: list[tuple[str, int]] = []
    skipped_perm: list[str] = []

    print(f"\n[{label}] Processing {len(target_ids)} artists\n")

    for i, sid in enumerate(target_ids, 1):
        artist_meta = artists.get(sid)
        if artist_meta is None:
            print(f"[{i}/{len(target_ids)}] {sid} — not in artists.json, skipping")
            continue

        name = artist_meta["name"]
        prev_entry = tracks.get(sid, {})
        prev_count = prev_entry.get("track_count", 0)

        if prev_entry.get("permanently_unresolved"):
            print(f"[{i}/{len(target_ids)}] {name} — permanently_unresolved, skipping")
            skipped_perm.append(name)
            continue

        print(f"[{i}/{len(target_ids)}] {name}  (was {prev_count})")
        new_tracks, current_delay = _resolve_one(client, sid, name, current_delay)
        new_count = len(new_tracks)

        # Safety: never overwrite a nonzero entry with zero. If the new
        # pass returned nothing, the artist may be transiently unreachable
        # (rate limit, 502, timeout) and the previous data is still good.
        # Only clear an entry that was already empty.
        if new_count == 0 and prev_count > 0:
            print(f"  ~ 0 tracks returned (likely transient) — keeping previous {prev_count}")
            unchanged.append((name, prev_count))
            time.sleep(current_delay)
            continue

        if require_improvement and new_count <= prev_count:
            print(f"  ~ {new_count} tracks (no improvement) — keeping previous entry")
            unchanged.append((name, prev_count))
            time.sleep(current_delay)
            continue

        # Preserve permanently_unresolved + note if they happen to be set.
        new_entry = dict(prev_entry)
        new_entry["tracks"] = new_tracks
        new_entry["track_count"] = new_count
        new_entry["resolved_at"] = today
        tracks[sid] = new_entry

        if new_count > prev_count:
            print(f"  + {new_count} tracks")
            improved.append((name, prev_count, new_count))
        else:
            print(f"  = {new_count} tracks (rewritten)")
            unchanged.append((name, prev_count))

        time.sleep(current_delay)

    _save_tracks_doc(tracks_doc)

    print(f"\n[OK] {label} complete.")
    print(f"  Improved: {len(improved)}")
    for name, old, new in improved:
        print(f"    {name}: {old} -> {new}")
    print(f"  Unchanged / no improvement: {len(unchanged)}")
    if skipped_perm:
        print(f"  Skipped (permanently_unresolved): {len(skipped_perm)}")


def run_full(test_mode: bool = False, resume_from_band: Optional[int] = None) -> None:
    """Full resolution: walk every artist ID in the lineup and refresh tracks."""
    artists = _load_artists()
    tracks_doc = _load_tracks_doc()
    lineup_ids = _load_lineup_ids()

    # Walk in alphabetical-by-name order (matches the on-disk lineup file).
    ordered_ids = sorted(lineup_ids, key=lambda sid: artists.get(sid, {}).get("name", "").lower())

    if test_mode:
        ordered_ids = ordered_ids[:10]
        print(f"[TEST] First {len(ordered_ids)} artists only")
    if resume_from_band is not None:
        ordered_ids = ordered_ids[max(0, resume_from_band - 1):]
        print(f"[RESUME] Starting from band {resume_from_band}")

    _resolve_ids(ordered_ids, artists, tracks_doc, label="FULL")


def retry_unresolved(below_threshold_only: bool = False) -> None:
    """Re-resolve artists currently below the 5-track threshold.

    ``below_threshold_only`` skips zero-track artists (likely genuinely
    absent from Spotify under their current ID).
    """
    artists = _load_artists()
    tracks_doc = _load_tracks_doc()

    candidates: list[str] = []
    for sid, entry in tracks_doc["artists"].items():
        if entry.get("permanently_unresolved"):
            continue
        count = entry.get("track_count", 0)
        if count >= 5:
            continue
        if below_threshold_only and count == 0:
            continue
        candidates.append(sid)

    if not candidates:
        print("No retryable below-threshold artists found.")
        return

    label = "RETRY (below-threshold only)" if below_threshold_only else "RETRY (all < 5)"
    _resolve_ids(candidates, artists, tracks_doc, label=label, require_improvement=True)


def retry_low_count(target_count: int) -> None:
    """Re-resolve artists at exactly ``target_count`` tracks. Idempotent —
    keeps the previous entry if the pass returns the same or fewer."""
    if target_count < 0 or target_count >= MAX_TRACKS:
        print(f"--retry-low-count must be between 0 and {MAX_TRACKS - 1} (got {target_count}).")
        return

    artists = _load_artists()
    tracks_doc = _load_tracks_doc()

    candidates = [
        sid for sid, entry in tracks_doc["artists"].items()
        if entry.get("track_count") == target_count
        and not entry.get("permanently_unresolved")
    ]

    if not candidates:
        print(f"No artists at track_count == {target_count}.")
        return

    _resolve_ids(
        candidates,
        artists,
        tracks_doc,
        label=f"RETRY-LOW {target_count}",
        require_improvement=True,
    )


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve Spotify tracks for Wacken lineup bands.")
    parser.add_argument("--test", action="store_true", help="Test run: resolve only first 10 artists")
    parser.add_argument("--resume-from-band", type=int, help="Resume from band N (1-indexed, alphabetical)")
    parser.add_argument(
        "--retry-unresolved",
        action="store_true",
        help="Re-resolve every artist currently below the 5-track threshold (excluding permanently_unresolved)",
    )
    parser.add_argument(
        "--below-threshold-only",
        action="store_true",
        help="With --retry-unresolved: only retry artists at 1-4 tracks (skip zero-track artists)",
    )
    parser.add_argument(
        "--retry-low-count",
        type=int,
        metavar="N",
        help=f"Re-resolve artists at track_count == N (0 <= N < {MAX_TRACKS}). Idempotent.",
    )

    args = parser.parse_args()

    if args.retry_unresolved:
        retry_unresolved(below_threshold_only=args.below_threshold_only)
    elif args.retry_low_count is not None:
        retry_low_count(args.retry_low_count)
    else:
        run_full(test_mode=args.test, resume_from_band=args.resume_from_band)
