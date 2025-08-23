import os

from yt_dlp import YoutubeDL

from .log import *


def get_remote_ids(url, start: int = None, end: int = None):
    list_options = {
        "extract_flat": True,
        "download": False,
        # "ignore_no_formats_error": True,
        "quiet": True,
    }
    if start is not None: list_options["playliststart"] = start
    if end is not None: list_options["playlistend"] = end

    log_verbose("downloading list...")

    with YoutubeDL(list_options) as ytdl:
        data = ytdl.extract_info(url)

    return [e["id"] for e in data["entries"]]

def get_local_ids(directory):
    print("reading local ids...")

    return [f.split('.')[-2] for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
