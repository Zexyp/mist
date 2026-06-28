from enum import Enum, auto
from typing import Generic, TypeVar
from urllib.parse import urlparse
from abc import ABC, abstractmethod

import requests

TTrack = TypeVar('TTrack')
TArtist = TypeVar('TArtist')

class MetadataConnector(Generic[TTrack, TArtist], ABC):

    # region track

    @abstractmethod
    def get_track_name(self, track: TTrack) -> str:
        pass

    @abstractmethod
    def get_track_title(self, track: TTrack) -> str:
        pass

    @abstractmethod
    def get_track_tags(self, track: TTrack) -> list[str]:
        pass

    @abstractmethod
    def get_track_genre(self, track: TTrack) -> str:
        pass

    @abstractmethod
    def get_artist(self, track: TTrack) -> TArtist:
        pass

    # endregion

    # region artist

    @abstractmethod
    def get_artist_name(self, artist: TArtist) -> str:
        pass

    @abstractmethod
    def get_artist_links(self, artist: TArtist) -> list[str]:
        pass

    @abstractmethod
    def get_artist_tags(self, artist: TArtist) -> list[str]:
        pass

    # endregion

    # region search

    def search_artist(self, query: str) -> list[TArtist]:
        raise NotImplemented

    def search_track(self, query: str) -> list[TTrack]:
        raise NotImplemented

    # endregion

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

def urlappend(url: str, path: str) -> str:
    return url.rstrip("/") + "/" + path
