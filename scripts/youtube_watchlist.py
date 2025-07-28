#!/usr/bin/env python3
"""Monitor YouTube channels and auto-download new videos.

Reads channel identifiers from ``channels.txt``. Each day, checks for
videos uploaded in the last 24 hours and downloads them using ``yt-dlp``
in 360p. Previously downloaded videos are skipped using a local cache
file. Channel identifiers may be the channel ID (``UC...``), a legacy
username, or a handle prefixed with ``@``.
"""

import datetime as _dt
import re as _re
import subprocess as _sp
import xml.etree.ElementTree as _ET
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import sys
import logging
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
CHANNELS_FILE = SCRIPT_DIR / "channels.txt"
CACHE_FILE = SCRIPT_DIR / "downloaded_videos.txt"
DOWNLOAD_DIR = Path.home() / "yt-watchlist"
LOG_FILE = SCRIPT_DIR / "youtube_watchlist.log"
TANZIMAT_ENV_FILE = SCRIPT_DIR / "tanzimat.env"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Load environment variables
if TANZIMAT_ENV_FILE.is_file():
    load_dotenv(dotenv_path=TANZIMAT_ENV_FILE)
    logging.info(f"Loaded environment variables from {TANZIMAT_ENV_FILE}")
else:
    logging.info(f"Environment file not found at {TANZIMAT_ENV_FILE}, skipping.")

def _read_channels(path: Path) -> list[str]:
    logging.info(f"Reading channels from {path}")
    if not path.exists():
        logging.error(f"Channel list not found: {path}")
        return []
    with path.open() as f:
        channels = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        logging.info(f"Found {len(channels)} channels.")
        return channels


def _load_cache(path: Path) -> set[str]:
    logging.info(f"Loading cache from {path}")
    if not path.exists():
        logging.warning(f"Cache file not found: {path}")
        return set()
    with path.open() as f:
        cache = {ln.strip() for ln in f if ln.strip()}
        logging.info(f"Loaded {len(cache)} video IDs from cache.")
        return cache


def _append_cache(path: Path, video_id: str) -> None:
    logging.info(f"Appending video ID {video_id} to cache file {path}")
    with path.open("a") as f:
        f.write(video_id + "\n")



def _resolve_handle(handle: str) -> str:
    """Return the channel ID for a YouTube handle."""
    logging.info(f"Resolving handle: @{handle}")
    url = f"https://www.youtube.com/@{handle}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    match = _re.search(r'"channelId":"(UC[^"]+)"', html)
    if not match:
        logging.error(f"Could not resolve handle @{handle}")
        raise ValueError(f"Could not resolve handle @{handle}")
    channel_id = match.group(1)
    logging.info(f"Resolved @{handle} to {channel_id}")
    return channel_id


def _fetch_feed(channel: str) -> bytes:
    logging.info(f"Fetching feed for channel: {channel}")
    if channel.startswith("UC"):
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
        logging.info(f"Fetching feed from URL: {url}")
        with urlopen(url) as resp:
            return resp.read()

    if channel.startswith("@"):
        try:
            channel_id = _resolve_handle(channel[1:])
        except Exception as exc:
            logging.error(f"Error resolving handle {channel}: {exc}")
            raise HTTPError(None, 404, str(exc), None, None)
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        logging.info(f"Fetching feed from URL: {url}")
        with urlopen(url) as resp:
            return resp.read()

    url = f"https://www.youtube.com/feeds/videos.xml?user={channel}"
    logging.info(f"Fetching feed from URL: {url}")
    with urlopen(url) as resp:
        return resp.read()


def _parse_feed(xml_data: bytes) -> list[tuple[str, str]]:
    logging.info("Parsing XML feed.")
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
    logging.info(f"Found {len(results)} videos in feed.")
    return results


def _is_recent(published: str, *, hours: int = 72) -> bool:
    logging.debug(f"Checking if video published at {published} is recent (within {hours} hours).")
    try:
        ts = _dt.datetime.fromisoformat(published.rstrip("Z"))
    except ValueError:
        logging.warning(f"Could not parse timestamp: {published}")
        return False
    is_recent = _dt.datetime.now(_dt.UTC) - ts < _dt.timedelta(hours=hours)
    logging.debug(f"Video published at {published} is {'recent' if is_recent else 'not recent'}.")
    return is_recent


def _get_video_duration(file_path: Path) -> float:
    """Return the duration of a video in seconds."""
    logging.info(f"Getting duration for video: {file_path}")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(file_path),
    ]
    try:
        result = _sp.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout)
        logging.info(f"Duration of {file_path} is {duration} seconds.")
        return duration
    except (_sp.CalledProcessError, ValueError) as e:
        logging.error(f"Error getting duration for {file_path}: {e}")
        return 0.0


def _download(video_id: str) -> Path | None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_tpl = DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"
    cmd = ["yt-dlp", "-f", "18", url, "-o", str(out_tpl)]
    logging.info(f"Attempting to download video: {video_id}")
    proc = _sp.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        logging.error(f"yt-dlp failed for {video_id}: {proc.stderr}")
        return None

    # Find the downloaded file
    for line in proc.stdout.splitlines():
        if "Destination:" in line:
            filepath_str = line.split("Destination:", 1)[1].strip()
            return Path(filepath_str)
        if "has already been downloaded" in line:
            match = _re.search(r"Destination: (.+)", proc.stdout)
            if match:
                return Path(match.group(1))
    return None


def main() -> None:
    logging.info("YouTube watchlist script started.")
    _sp.run(["notify-send", "YouTube Watchlist", "Scraping started..."], check=False)
    channels = _read_channels(CHANNELS_FILE)
    if not channels:
        logging.info("No channels found in channels.txt. Exiting.")
        _sp.run(["notify-send", "YouTube Watchlist", "Finished: No channels found."], check=False)
        return
    print("Channels loaded")
    cache = _load_cache(CACHE_FILE)
    print("Loaded cache")
    for ch in channels:
        logging.info(f"Processing channel: {ch}")
        try:
            feed = _fetch_feed(ch)
            logging.info(f"Successfully fetched feed for {ch}.")
        except Exception as exc:  # network errors
            logging.error(f"Failed fetching feed for {ch}: {exc}")
            continue
        videos = _parse_feed(feed)
        logging.info(f"Found {len(videos)} videos in the feed for channel {ch}.")
        for vid, published in videos:
            if vid in cache:
                logging.info(f"Video {vid} already in cache. Skipping.")
                continue
            if not _is_recent(published):
                logging.info(f"Video {vid} is not recent. Skipping.")
                continue
            logging.info(f"Found new recent video: {vid}")
            downloaded_file = _download(vid)
            if downloaded_file:
                duration = _get_video_duration(downloaded_file)
                if duration < 60:
                    logging.info(
                        f"Video {vid} is shorter than 1 minute ({duration}s), deleting."
                    )
                    downloaded_file.unlink()
                    logging.info(f"Deleted video file: {downloaded_file}")
                else:
                    _append_cache(CACHE_FILE, vid)
                    cache.add(vid)
                    logging.info(f"Added video {vid} to cache.")
    logging.info("Script finished.")
    _sp.run(["notify-send", "YouTube Watchlist", "Scraping finished."], check=False)


if __name__ == "__main__":
    main()
