import concurrent.futures
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlsplit

from yt_dlp import YoutubeDL, DownloadError
from pprint import pprint, pformat
import re

from .log import spawn_logger
from .metadata import Source
from .utils import strip_ansi
from . import Entry
from . import log

_DUMP_DATA = False

logger = spawn_logger(__name__)

# TODO: suppress ytdlp warning

class BaseLogger:
    _PREFIX: str = "[ytdlp] "

    def debug(self, msg):
        msg = strip_ansi(msg)
        if msg.startswith("[debug] "):
            logger.debug(f"{self._PREFIX}{msg}")
        else:
            self.info(msg)

    def info(self, msg):
        msg = strip_ansi(msg)
        logger.debug(f"{self._PREFIX}[info] {msg}")

    def warning(self, msg):
        msg = strip_ansi(msg)
        logger.warning(f"{self._PREFIX}{msg}")

    def error(self, msg):
        msg = strip_ansi(msg)
        logger.error(f"{self._PREFIX}{msg}")

def _emtpy_hook(d: dict):
    pass
    #d["status"]: {downloading, finished}
    #d["_percent_str"]:
    #d["_speed_str"]:
    #d["_eta_str"]:
    #d["_elapsed_str"]:

    #d["total_bytes"]:
    #d["downloaded_bytes"]:
    #d["filename"]:
    #d["tmpfilename"]:
    #d["fragment_index"]:
    #d["fragment_count"]:
    #d["total_bytes_estimate"]:
    #d["elapsed"]:
    #d["eta"]:
    #d["speed"]:

class YtPageProgressLogger(BaseLogger):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback

    def info(self, msg):
        super().info(msg)

        msg = strip_ansi(msg)

        # TODO: only yt supported rn
        # TODO: this is ass
        if msg.startswith("[youtube:tab] ") and (m := re.search(r"page (\d+):", msg)):
            self.callback(f"Page {m.group(1)}")

        # TODO: "Downloading 1429 items of 1429"

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

options_download: dict = {
    "quiet": True,
    "logger": BaseLogger(),
    "extract_audio": True,
    "format": "bestaudio",

    "outtmpl": "%(title)s.%(id)s.%(ext)s",
}

def get_playlist_title(url: str) -> str:
    try:
        with YoutubeDL(options_playlist_title) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        print(e)

    assert info["_type"] == "playlist"
    return info["title"]

def get_entries(url: str, progress: Callable[[str], None] = None, max_concurrency: int | None = None) -> list[Entry]:
    if max_concurrency is not None:
        logger.debug(f"concurrency: {max_concurrency}")

    entries = get_entries_fast(url, progress=progress)

    def metadata_collection(e: Entry):
        from . import metadata
        oe = metadata.obtain(metadata.detect_source(url), e.id)
        oe.id = e.id
        return oe

    output = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures = [executor.submit(metadata_collection, e) for e in entries]

        for future in concurrent.futures.as_completed(futures):
            try:
                output.append(future.result())
            except concurrent.futures.TimeoutError:
                logger.error("this took too long...")

    return output

def get_entries_fast(url: str, progress: Callable[[str], None] = None) -> list[Entry]:
    opts = dict(options_entries_flat)
    if progress:
        logger.debug("progress callback will be used")
        opts["logger"] = YtPageProgressLogger(progress)


    opts["progress_hooks"] = [_emtpy_hook],

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        print(e)

    assert info["_type"] == "playlist"
    if _DUMP_DATA:
        logger.debug(pformat(info))
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

def download_entries(platform: Source, entries: list[Entry], max_concurrency: int | None = None):
    if max_concurrency is not None:
        logger.debug(f"concurrency: {max_concurrency}")

    opts = dict(options_download)

    def download_item(item: Entry):
        lopts = dict(opts)

        # use fixed name if available
        if item.title:
            lopts["outtmpl"] = f"{item.title}.%(id)s.%(ext)s"

        from . import metadata
        url = metadata.url_source(platform, item.id)

        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
        except DownloadError as e:
            log.error(f"filed to download entry '{item.id}': {e}")
            log.exception(e)


        # TODO: tag

    output = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures = [executor.submit(download_item, e) for e in entries]

        for future in concurrent.futures.as_completed(futures):
            try:
                output.append(future.result())
            except concurrent.futures.TimeoutError:
                logger.error("this took too long...")

    return output