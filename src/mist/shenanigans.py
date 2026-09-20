import concurrent.futures
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlsplit

from yt_dlp import YoutubeDL, DownloadError
from pprint import pprint, pformat
import re

from yt_dlp.postprocessor import PostProcessor

from .metadata import Source
from .utils import strip_ansi, sanitize_filename
from . import Entry

class ShenanigansError(Exception):
    pass

_DUMP_DATA = False

logger = logging.getLogger(__name__)

# TODO: suppress ytdlp warning

class RateLimiter:
    def __init__(self, interval):
        self.interval = interval
        self.lock = threading.Lock()
        self.next_allowed = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()

            # Reserve the next available execution time
            start_time = max(now, self.next_allowed)
            self.next_allowed = start_time + self.interval

        # Sleep outside the lock so other threads can reserve their slots
        delay = start_time - now
        if delay > 0:
            logger.debug(f"limiter: sleeping for {delay} seconds")
            time.sleep(delay)

class MetadataPostProcessor(PostProcessor):
    def __init__(self, data: Entry, image_options: dict = None):
        super().__init__()
        self.data = data
        self.image_options = image_options

    def run(self, information):
        from . import tags
        tags.apply(information["filepath"], self.data, image_options=self.image_options)
        return [], information

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

def _empty_hook(d: dict):
    #pprint(d)
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

class YtLogger(BaseLogger):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        raise NotImplementedError

    def info(self, msg):
        super().info(msg)

        msg = strip_ansi(msg)

        # TODO: only yt supported rn
        # TODO: this is ass
        if msg.startswith("[youtube:tab] ") and (m := re.search(r"page (\d+):", msg)):
            self.callback(f"Page {m.group(1)}")

        # TODO: "Downloading 1429 items of 1429"

class CallbackLogger(BaseLogger):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback

    def info(self, msg):
        super().info(msg)

        msg = strip_ansi(msg)

        self.callback(msg)


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
    "js_runtimes": {"node": {}},
    "outtmpl": "%(title)s.%(id)s.%(ext)s",
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
}

def get_playlist_title(url: str) -> str:
    try:
        info = None
        with YoutubeDL(options_playlist_title) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        raise ShenanigansError(e)

    assert info["_type"] == "playlist"
    return info["title"]

def get_entries(url: str,
                progress: Callable[[dict], None] = None,
                max_concurrency: int | None = None,
                metadata_retries: int = 0,
                metadata_retry_delay: int = 0,
                metadata_wait: int = 0,
                start: int | None = None,
                end: int | None = None,) -> list[Entry]:
    if max_concurrency is not None:
        logger.debug(f"concurrency: {max_concurrency}")

    entries = get_entries_fast(url, progress=progress,
                               start=start,
                               end=end)

    if metadata_wait:
        metadata_limiter = RateLimiter(metadata_wait)

    def metadata_collection(e: Entry):
        if metadata_limiter: metadata_limiter.wait()

        from . import metadata
        oe = metadata.obtain(metadata.detect_source(url), e.id,
                             retries=metadata_retries,
                             delay=metadata_retry_delay)
        oe.id = e.id
        return oe

    output = []
    if progress:
        progress("starting")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures = [executor.submit(metadata_collection, e) for e in entries]

        for future in concurrent.futures.as_completed(futures):
            try:
                output.append(future.result())
            except concurrent.futures.TimeoutError:
                logger.error("this took too long...")
    if progress:
        progress("finished")
    return output

def get_entries_fast(url: str, progress: Callable[[dict], None] = None,
                     start: int | None = None,
                     end: int | None = None) -> list[Entry]:
    opts = dict(options_entries_flat)
    if progress:
        logger.debug("progress callback will be used")
        opts["logger"] = CallbackLogger(lambda x: progress({"message": x}))
        opts["progress_hooks"] = [progress]

    if start is not None:
        opts["playliststart"] = start
    if end is not None:
        opts["playlistend"] = end

    try:
        info = None
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        raise ShenanigansError(e)

    if not info or 'entries' not in info:
        raise ShenanigansError("unable to use entries")

    assert info["_type"] == "playlist"
    if _DUMP_DATA:
        logger.debug(pformat(info))
    output = []
    for e in info["entries"]:
        output.append(extract_flat_entry(e))
    return output

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

def download_entries(platform: Source, entries: list[Entry], destination_dir: str,
                     progress: Callable[[dict], None] = None,
                     max_concurrency: int | None = None,
                     image_options: dict = None):
    logger.debug(f"destination: {destination_dir}")
    if max_concurrency is not None:
        logger.debug(f"concurrency: {max_concurrency}")

    opts = dict(options_download)
    if progress:
        logger.debug("progress callback will be used")
        opts["logger"] = CallbackLogger(lambda x: progress({"message": x}))
        opts["progress_hooks"] = [progress]

    def download_item(item: Entry):
        lopts = dict(opts)

        # use fixed name if available
        if item.title:
            lopts["outtmpl"] = f"{sanitize_filename(item.title)}.%(id)s.%(ext)s"
        lopts["outtmpl"] = os.path.join(destination_dir, lopts["outtmpl"])

        from . import metadata
        url = metadata.url_source(platform, item.id)

        try:
            with YoutubeDL(lopts) as ydl:
                ydl.add_post_processor(MetadataPostProcessor(item, image_options=image_options))
                ydl.download([url])
        except DownloadError as e:
            logger.error(f"filed to process entry '{item.id}': {e}")
            logger.debug(e, exc_info=True)
            # TODO: raise

    output = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures = [executor.submit(download_item, e) for e in entries]

        for future in concurrent.futures.as_completed(futures):
            try:
                output.append(future.result())
            except concurrent.futures.TimeoutError:
                logger.error("this took too long...")

    return output