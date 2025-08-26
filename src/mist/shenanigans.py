import os
from pprint import pprint
from typing import Callable, Any

from yt_dlp import YoutubeDL

from .log import log_verbose
from . import name_purifier
from .utils import sanitize_filename

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

def shrimplify_name(entry):
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

    with YoutubeDL(options) as ytdl:
        data = ytdl.extract_info(url, download=False)
    assert data["_type"] == "playlist"

    return data["title"]

def get_remote_ids(url, start: int = None, end: int = None):
    options = dict(playlist_options)
    if start is not None: options["playliststart"] = start
    if end is not None: options["playlistend"] = end

    log_verbose("downloading list...")

    with YoutubeDL(options) as ytdl:
        data = ytdl.extract_info(url, download=False)
    assert data["_type"] == "playlist"

    return [e["id"] for e in data["entries"]]

def get_local_ids(directory):
    log_verbose("reading local ids...")
    ids = []
    for f in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, f)):
            if len(parts := f.split('.')) > 2:
                ids.append(parts[-2])

    return ids

def get_entry_title(idntifier):
    raise NotImplementedError

def process_entry(idntifier, output_directory,
                  progress_hook: Callable = None):
    with YoutubeDL(video_info_options) as ytdl:
        data = ytdl.extract_info('http://www.youtube.com/watch?v=' + idntifier, download=False)

    options = dict(video_options)

    if progress_hook is not None: options["progress_hooks"] = [progress_hook]

    #if MAX_DURATION is not None and entry['duration'] > MAX_DURATION:
    #    log_verbose(f"skipping '{entry['id']}' (duration restriction)")
    #    return

    name = shrimplify_name(data)

    log_verbose(f"downloading '{data['id']}' {name}")

    options['outtmpl'] = os.path.join(output_directory, sanitize_filename(name) + '.' + data['id'] + '.%(ext)s')

    with YoutubeDL(options) as ytdl:
        data = ytdl.download('http://www.youtube.com/watch?v=' + data['id'])
