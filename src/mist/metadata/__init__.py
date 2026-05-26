from enum import Enum, auto
from urllib.parse import urlparse


class Platform(Enum):
    YOUTUBE = auto()
    SOUNDCLOUD = auto()

def detect_platform(url) -> Platform:
    parsed_url = urlparse(url)
    match parsed_url.netloc:
        case "youtube.com" | "www.youtube.com" | "music.youtube.com":
            return Platform.YOUTUBE
        case "soundcloud.com":
            return Platform.SOUNDCLOUD
        case _:
            assert False, f"unknown platform for '{parsed_url.netloc}'"
