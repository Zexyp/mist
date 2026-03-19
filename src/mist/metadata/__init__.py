import json
import os
from enum import Enum, auto
from urllib.parse import urlparse

from . import lfm, scapi, ytapi
from ..utils import FileCache
from . import local

class Platform(Enum):
    YOUTUBE = auto()
    SOUNDCLOUD = auto()

cache: FileCache = FileCache()
cache_tags: FileCache = FileCache(serialize=lambda v: json.dumps(v), deserialize=lambda v: json.loads(v))
cache_labels: FileCache = FileCache()

def load_cache(directory: str):
    assert os.path.isdir(directory)
    cache.load_file(os.path.join(directory, "metadata"))
    cache_tags.load_file(os.path.join(directory, "tags"))
    cache_labels.load_file(os.path.join(directory, "titles"))

def save_cache(directory: str):
    cache.save_file(os.path.join(directory, "metadata"))
    cache_tags.save_file(os.path.join(directory, "tags"))
    cache_labels.save_file(os.path.join(directory, "titles"))

@cache.cached(key=lambda p, i: f"{i}|author")
def get_author(platform, ident) -> str:
    match platform:
        case Platform.YOUTUBE:
            return ytapi.get_author(ident)
        case Platform.SOUNDCLOUD:
            return scapi.get_author(ident)
        case _:
            assert False, f"unknown platform"

@cache.cached(key=lambda p, i: f"{i}|title")
def get_title(platform, ident) -> str:
    match platform:
        case Platform.YOUTUBE:
            return ytapi.get_title(ident)
        case Platform.SOUNDCLOUD:
            return scapi.get_title(ident)
        case _:
            assert False, f"unknown platform"

@cache_labels.cached(key=lambda p, i: i)
def get_full_title(platform, ident) -> str:
    match platform:
        case Platform.YOUTUBE:
            return ytapi.get_full_title(ident)
        case Platform.SOUNDCLOUD:
            return scapi.get_full_title(ident)
        case _:
            assert False, f"unknown platform"

@cache_tags.cached(key=lambda p, i: i)
def get_tags(platform, ident) -> dict[str, list[str]]:
    tags = {}

    if platform == Platform.YOUTUBE:
        tags["lastfm"] = lfm.search_tags(ident, get_full_title(platform, ident))

    if platform == Platform.SOUNDCLOUD:
        tags["soundcloud"] = scapi.get_tags(ident)

    return tags

def get_url_template(platform):
    match platform:
        case Platform.YOUTUBE:
            return "http://www.youtube.com/watch?v={identifier}"
        case Platform.SOUNDCLOUD:
            return "https://api.soundcloud.com/tracks/{identifier}"
        case _:
            assert False, f"unknown platform"

def detect_platform(url):
    parsed_url = urlparse(url)
    match parsed_url.netloc:
        case "youtube.com" | "www.youtube.com" | "music.youtube.com":
            return Platform.YOUTUBE
        case "soundcloud.com":
            return Platform.SOUNDCLOUD
        case _:
            assert False, f"unknown platform for '{parsed_url.netloc}'"
