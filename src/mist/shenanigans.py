# TODO: name fallback

import os
from pprint import pprint
from typing import Callable, Any
import glob

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from .log import log_verbose, log_debug
from . import title_purifier
from .utils import sanitize_filename

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

title_cache: dict[str, str] | None = None

def save_title_cache(file):
    global title_cache

    assert title_cache is not None

    log_debug(f"saving cache '{file}'")

    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "w") as f:
        for k, v in title_cache.items():
            f.write(f"{k}: {v}\n")

    title_cache = None

    log_verbose("cache off")

def load_title_cache(file):
    global title_cache

    assert title_cache is None

    log_verbose("using cache")

    title_cache = {}

    log_debug(f"loading cache '{file}'")
    if os.path.isfile(file):
        with open(file, "r") as f:
            while line := f.readline():
                parts = line.strip().split(": ", 1)
                title_cache[parts[0]] = parts[1]
    else:
        log_debug("cache empty")

def shrimplify_name(entry):
    raise Exception("obsolete")

    if entry["channel"] is None:
        log_verbose(f"channel none at '{entry['id']}'")

    log_verbose("purifying name")
    name = name_purifier.purify(entry["id"])

    return name

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
    log_verbose("reading local ids...")
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

def get_remote_entry_title(identifier):
    if title_cache is not None and identifier in title_cache:
        return title_cache[identifier]

    log_verbose("getting pure name")
    name = title_purifier.purify(identifier)

    if title_cache is not None:
        title_cache[identifier] = name

    return name

def process_entry(identifier, output_directory,
                  progress_hook: Callable = None):
    name = get_remote_entry_title(identifier)

    def wrapper(*args, **kwargs):
        args[0]["title"] = name
        args[0]["id"] = identifier
        return progress_hook(*args, **kwargs)

    options = dict(video_options)
    if progress_hook is not None: options["progress_hooks"] = [wrapper]

    #if MAX_DURATION is not None and entry['duration'] > MAX_DURATION:
    #    log_verbose(f"skipping '{entry['id']}' (duration restriction)")
    #    return

    log_verbose(f"downloading '{identifier}' ({name})...")

    options['outtmpl'] = os.path.join(output_directory, sanitize_filename(name) + '.' + identifier + '.%(ext)s')

    try:
        with YoutubeDL(options) as ytdl:
            data = ytdl.download('http://www.youtube.com/watch?v=' + identifier)
    except DownloadError as e:
        raise ShenanigansError(e)
