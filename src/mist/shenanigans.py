from typing import Callable

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

options_item_ids: dict = {
    "extract_flat": True,
    "quiet": True,
    "playlist": True,
    "skip_download": True,
    "logger": BaseLogger(),
}

def get_playlist_title(url: str) -> str:
    try:
        with YoutubeDL(options_playlist_title) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        print(e)

    assert info["_type"] == "playlist"
    return info["title"]

def get_item_ids(url: str, progress: Callable[[str], None] = None) -> list[str]:
    opts = dict(options_item_ids)

    if progress:
        opts["logger"] = PageProgressLogger(progress)

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        print(e)

    return [entry["id"] for entry in info["entries"]]

def get_item(url: str, progress: Callable) -> str:
    raise NotImplementedError
