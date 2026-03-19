import os
from pprint import pprint
from typing import Callable, Any
import glob

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from .log import log_verbose, log_debug
from .utils import sanitize_filename, FileCache
from . import metadata
from .metadata.scrape_utils import RateLimitHitError

class ShenanigansError(Exception):
    pass

YAPPING = False

playlist_options: dict = {
    "extract_flat": True,
    # "ignore_no_formats_error": True,
    "quiet": not YAPPING,
    "playlist": True,
}

video_info_options: dict = {
    "quiet": not YAPPING,
    "playlist": False,
}

video_options: dict = {
    "format": "bestaudio",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
    }],
    "quiet": not YAPPING,
    "playlist": False,
}

def get_remote_title(url):
    options = dict(playlist_options)
    # FIXME: why are we download video info?
    # don't care about all videos
    options["playliststart"] = 1
    options["playlistend"] = 1

    log_verbose("downloading remote title...")
    try:
        with YoutubeDL(options) as ytdl:
            data = ytdl.extract_info(url, download=False)
    except DownloadError as e:
        raise ShenanigansError(e)
    assert data["_type"] == "playlist"

    return data["title"]

def get_remote_ids(url, start: int = None, end: int = None):
    options = dict(playlist_options)
    if start is not None: options["playliststart"] = start
    if end is not None: options["playlistend"] = end

    log_verbose("downloading list...")
    try:
        with YoutubeDL(options) as ytdl:
            data = ytdl.extract_info(url, download=False)
    except DownloadError as e:
        raise ShenanigansError(e)
    assert data["_type"] == "playlist"

    return [e["id"] for e in data["entries"]]

def process_entry(pltf: metadata.Platform, identifier, output_directory,
                  progress_hook: Callable = None):
    try:
        name = sanitize_filename(metadata.get_full_title(pltf, identifier))
    except RateLimitHitError as e:
        name = "%(title)s"

    def progress_wrapper(*args, **kwargs):
        args[0]["title"] = name
        args[0]["id"] = identifier
        return progress_hook(*args, **kwargs)

    options = dict(video_options)
    if progress_hook is not None: options["progress_hooks"] = [progress_wrapper]

    #if MAX_DURATION is not None and entry['duration'] > MAX_DURATION:
    #    log_verbose(f"skipping '{entry['id']}' (duration restriction)")
    #    return

    options['outtmpl'] = os.path.join(output_directory, name + '.' + identifier + '.%(ext)s')

    log_verbose("downloading entry...")
    try:
        with YoutubeDL(options) as ytdl:
            data = ytdl.download(metadata.get_url_template(pltf).format(identifier=identifier))
    except DownloadError as e:
        raise ShenanigansError(e)
