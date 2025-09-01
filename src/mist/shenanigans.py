import os
from pprint import pprint
from typing import Callable, Any
import glob

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from .log import log_verbose, log_debug
from . import title_purifier
from .utils import sanitize_filename, FileCache

class ShenanigansError(Exception):
    pass

YAPPING = False

playlist_options = {
    "extract_flat": True,
    # "ignore_no_formats_error": True,
    "quiet": not YAPPING,
    "playlist": True,
}

video_info_options = {
    "quiet": not YAPPING,
    "playlist": False,
}

video_options = {
    "format": "bestaudio",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
    }],
    "quiet": not YAPPING,
    "playlist": False,
}

title_cache: FileCache = FileCache()

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

def get_local_ids(directory):
    log_debug("reading local ids")
    ids = []
    for f in os.listdir(directory):
        if not os.path.isfile(os.path.join(directory, f)):
            continue
        f = os.path.basename(f)
        if len(parts := f.rsplit('.', 2)) > 2:
            ids.append(parts[-2])

    return ids

def get_local_entry_title(directory, identifier):
    titles = []
    for f in glob.glob(os.path.join(directory, f"*.{identifier}.*")):
        if not os.path.isfile(os.path.join(directory, f)):
            continue
        f = os.path.basename(f)
        if len(parts := f.rsplit('.', 2)) > 2:
            titles.append(parts[0])

    assert len(titles) == 1, "incorrect find"
    return titles[0]

@title_cache.cached
def get_remote_entry_title(identifier):
    log_verbose(f"getting pure title")
    name = title_purifier.purify(identifier)

    return name

def process_entry(identifier, output_directory,
                  progress_hook: Callable = None):
    try:
        title = sanitize_filename(get_remote_entry_title(identifier))
    except title_purifier.RateLimitHitError as e:
        title = "%(title)s"

    def progress_wrapper(*args, **kwargs):
        args[0]["title"] = title
        args[0]["id"] = identifier
        return progress_hook(*args, **kwargs)

    options = dict(video_options)
    if progress_hook is not None: options["progress_hooks"] = [progress_wrapper]

    #if MAX_DURATION is not None and entry['duration'] > MAX_DURATION:
    #    log_verbose(f"skipping '{entry['id']}' (duration restriction)")
    #    return

    options['outtmpl'] = os.path.join(output_directory, title + '.' + identifier + '.%(ext)s')

    log_verbose("downloading entry...")
    try:
        with YoutubeDL(options) as ytdl:
            # https://api.soundcloud.com/tracks/{identifier}
            data = ytdl.download('http://www.youtube.com/watch?v=' + identifier)
    except DownloadError as e:
        raise ShenanigansError(e)
