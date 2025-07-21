#!/usr/bin/env python3
"""Monitor YouTube channels and auto-download new videos.

Reads channel identifiers from channels.txt. Each day, checks for videos
uploaded in the last 24 hours and downloads them using ``yt-dlp`` in 360p.
Previously downloaded videos are skipped using a local cache file.
"""

import datetime as _dt
import subprocess as _sp
import xml.etree.ElementTree as _ET
from pathlib import Path
from urllib.request import urlopen
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
CHANNELS_FILE = SCRIPT_DIR / "channels.txt"
CACHE_FILE = SCRIPT_DIR / "downloaded_videos.txt"
DOWNLOAD_DIR = Path.home() / "yt-watchlist"


def _read_channels(path: Path) -> list[str]:
    if not path.exists():
        print(f"Channel list not found: {path}", file=sys.stderr)
        return []
    with path.open() as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


def _load_cache(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open() as f:
        return {ln.strip() for ln in f if ln.strip()}


def _append_cache(path: Path, video_id: str) -> None:
    with path.open("a") as f:
        f.write(video_id + "\n")


def _fetch_feed(channel: str) -> bytes:
    if channel.startswith("UC"):
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
    else:
        url = f"https://www.youtube.com/feeds/videos.xml?user={channel}"
    with urlopen(url) as resp:
        return resp.read()


def _parse_feed(xml_data: bytes) -> list[tuple[str, str]]:
    root = _ET.fromstring(xml_data)
    ns = {
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "atom": "http://www.w3.org/2005/Atom",
    }
    results = []
    for entry in root.findall("atom:entry", ns):
        vid = entry.findtext("yt:videoId", namespaces=ns)
        published = entry.findtext("atom:published", namespaces=ns)
        if vid and published:
            results.append((vid, published))
    return results


def _is_recent(published: str, *, hours: int = 24) -> bool:
    try:
        ts = _dt.datetime.fromisoformat(published.rstrip("Z"))
    except ValueError:
        return False
    return _dt.datetime.utcnow() - ts < _dt.timedelta(hours=hours)


def _download(video_id: str) -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_tpl = str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s")
    cmd = ["yt-dlp", "-f", "18", url, "-o", out_tpl]
    _sp.run(cmd, check=False)


def main() -> None:
    channels = _read_channels(CHANNELS_FILE)
    if not channels:
        return
    cache = _load_cache(CACHE_FILE)
    for ch in channels:
        try:
            feed = _fetch_feed(ch)
        except Exception as exc:  # network errors
            print(f"Failed fetching feed for {ch}: {exc}", file=sys.stderr)
            continue
        for vid, published in _parse_feed(feed):
            if vid in cache or not _is_recent(published):
                continue
            _download(vid)
            _append_cache(CACHE_FILE, vid)
            cache.add(vid)


if __name__ == "__main__":
    main()
