import concurrent.futures
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlsplit

from dill.source import outdent
from yt_dlp import YoutubeDL, DownloadError
from pprint import pprint
import re

from . import log

# TODO: suppress ytdlp warning

class BaseLogger:
    _PREFIX: str = "[ytdlp] "

    def debug(self, msg):
        if msg.startswith("[debug] "):
            log.debug(f"{self._PREFIX}{msg}")
        else:
            self.info(msg)

    def info(self, msg):
        log.debug(f"{self._PREFIX}[info] {msg}")

    def warning(self, msg):
        log.warning(f"{self._PREFIX}{msg}")

    def error(self, msg):
        log.error(f"{self._PREFIX}{msg}")

class PageProgressLogger(BaseLogger):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback

    def info(self, msg):
        super().info(msg)

        # TODO: only yt supported rn
        if msg.startswith("[youtube:tab] ") and (m := re.search(r"page (\d+):", msg)):
            self.callback(f"Page {m.group(1)}")
        if "Finished downloading playlist:" in msg:
            self.callback("finished")

options_playlist_title: dict = {
    "extract_flat": True,
    # "ignore_no_formats_error": True,
    "playlist_items": "0",
    "quiet": True,
    "playlist": True,
    "skip_download": True,
    "logger": BaseLogger(),
}

options_entries_flat: dict = {
    "extract_flat": True,
    "quiet": True,
    "playlist": True,
    "skip_download": True,
    "logger": BaseLogger(),
}

# entry can be just a remote snapshot
# or a local file description
# or be full of metadata
@dataclass
class Entry:
    id: str = None
    title: str = None
    url: str = None
    name: str = None
    tags: list[str] = None
    artist: str = None
    artist_name: str = None
    genre: str = None

def get_playlist_title(url: str) -> str:
    try:
        with YoutubeDL(options_playlist_title) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        print(e)

    assert info["_type"] == "playlist"
    return info["title"]

def get_entries(url: str, progress: Callable[[str], None] = None, max_concurrency: int | None = None) -> list[Entry]:
    entries = get_entries_fast(url, progress=progress)
    def metadata_collection(e):
        from . import metadata
        oe = metadata.obtain(metadata.detect_source(url), e.id)
        oe.id = e.id
        return oe

    output = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures = [executor.submit(metadata_collection, e) for e in entries]

        for future in concurrent.futures.as_completed(futures):
            output.append(future.result())

    return output

def get_entries_fast(url: str, progress: Callable[[str], None] = None) -> list[Entry]:
    opts = dict(options_entries_flat)
    if progress:
        opts["logger"] = PageProgressLogger(progress)

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        print(e)

    assert info["_type"] == "playlist"
    output = []
    for e in info["entries"]:
        output.append(extract_flat_entry(e))
    return output

def get_item(url: str, progress: Callable) -> str:
    raise NotImplementedError

def extract_flat_entry(e: dict) -> Entry:
    entry = Entry(id=e["id"], url=e["url"])
    entry.title = ""
    if "title" in e:
        entry.title = e["title"]
    else:
        if "album" in e:
            entry.title = f"{e['album']} - "
        entry.title += urlsplit(e["url"]).path.strip("/")

    return entry
