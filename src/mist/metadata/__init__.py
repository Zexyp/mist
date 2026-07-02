import os
from enum import Enum, auto
from pprint import pprint
from typing import Generic, TypeVar, Callable, Optional, Any
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
import inspect

from ..log import spawn_logger

"""
@dataclass
class Artist:
    id: str = None
    name: str = None
    tags: list[str] = None
    links: dict[str, str] = None
"""

@dataclass
class Track:
    id: str = None
    name: str = None
    title: str = None
    tags: list[str] = None
    artist: str = None
    artist_name: str = None
    genre: str = None

log = spawn_logger(__name__)

class Source(Enum):
    LOCAL = auto()
    YOUTUBE = auto()
    SOUNDCLOUD = auto()
    LASTFM = auto()

def detect_source(url) -> Source:
    parsed_url = urlparse(url)

    if parsed_url.scheme == "file":
        return Source.LOCAL

    match parsed_url.netloc:
        case "youtube.com" | "www.youtube.com" | "music.youtube.com":
            return Source.YOUTUBE
        case "soundcloud.com":
            return Source.SOUNDCLOUD
        case _:
            assert False, f"unknown source for '{parsed_url.netloc}'"

TTrack = TypeVar('TTrack')
TArtist = TypeVar('TArtist')

class MetadataConnector(Generic[TTrack, TArtist], ABC):
    source: Source

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
    def get_artist_links(self, artist: TArtist) -> dict[str, str]:
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

@dataclass
class Data:
    yt_video_id: str = None
    yt_title: str = None
    lfm_track_url: str = None
    lfm_artist_links: dict[str, str] = None
    lfm_title: str = None

@dataclass
class ConnectorLink:
    from_connector: MetadataConnector
    to_connector: MetadataConnector
    matcher: Callable[[Data], str]

class MetadataConnectorRegistry:

    def __init__(self):
        self.nodes: dict[Source, MetadataConnector] = {}
        self.links: list[ConnectorLink] = []

    def register(self, connector: MetadataConnector):
        self.nodes[connector.source] = connector

    def add_link(self, link: ConnectorLink):
        self.links.append(link)

    def get_connector(self, source: Source) -> Optional[MetadataConnector]:
        return self.nodes.get(source)

    def get_links(self, source: Source) -> list[ConnectorLink]:
        return [link for link in self.links if link.from_connector.source == source]

connectors = MetadataConnectorRegistry()

def _build_registry():
    from . import lfm
    from . import yt
    from . import sc
    from . import local

    youtube = yt.YouTubeConnector()
    soundcloud = sc.SoundCloudConnector()
    lastfm = lfm.LastFmConnector()
    #local = local.LocalConnector()

    connectors.register(youtube)
    connectors.register(soundcloud)
    connectors.register(lastfm)
    #connectors.register(local)

    def youtube_to_lastfm_matcher(data: Data):
        return lfm.match_track(data.yt_video_id, data.yt_title)

    def lastfm_to_soundcloud_matcher(data: Data):
        # this line is fucking with my PyCharm 2025.2.1.1
        user_id = sc.get_user_id(os.path.basename(data.lfm_artist_links["SoundCloud"]))
        candidates = [i for i in sc.search_tracks(data.lfm_title or data.yt_title) if i["user"]["id"] == user_id]
        if len(candidates) > 1:
            log.debug(f"multiple candidates: {candidates}")

        return candidates[0]["id"] if candidates else None

    connectors.add_link(ConnectorLink(youtube, lastfm, youtube_to_lastfm_matcher))
    connectors.add_link(ConnectorLink(lastfm, soundcloud, lastfm_to_soundcloud_matcher))

_build_registry()

def enrich(data: Data, track: Track, item,  using_connector: MetadataConnector) -> Data:
    assert using_connector

    def try_enrich(lmbd: Callable[[], Any]):
        try:
            return lmbd()
        except Exception as e:
            log.error(f"{str(inspect.getsourcelines(lmbd)[0][0]).strip()}\n{type(e).__name__}: {e}")
            return None

    track_name = try_enrich(lambda: using_connector.get_track_name(item))
    track_title =  try_enrich(lambda: using_connector.get_track_title(item))
    track_tags = try_enrich(lambda: using_connector.get_track_tags(item))
    track_genre = try_enrich(lambda: using_connector.get_track_genre(item))

    artist = try_enrich(lambda: using_connector.get_artist(item))
    artist_name = None
    artist_links = None
    if artist:
        artist_name = try_enrich(lambda: using_connector.get_artist_name(artist))
        artist_links = try_enrich(lambda: using_connector.get_artist_links(artist))

    match using_connector.source:
        case Source.YOUTUBE:
            data.yt_video_id = item
            data.yt_title = track_title
        case Source.LASTFM:
            data.lfm_track_url = item
            data.lfm_artist_links = artist_links
            data.lfm_title = track_title

    track.name = track.name or track_name
    track.title = track.title or track_title
    track.genre = track.genre or track_genre
    if track_tags:
        if track.tags:
            track.tags.extend(track_tags)
        else:
            track.tags = track_tags

    track.artist_name = track.artist_name or artist_name

    return data

def obtain(source: Source, entry: str):
    visited: set[Source] = set()

    track = Track()
    data = Data()
    queue = [(source, entry)]

    while queue:
        source, item = queue.pop(0)

        visited.add(source)

        connector = connectors.get_connector(source)
        data = enrich(data, track, item, connector)

        for link in connectors.get_links(source):
            if link.to_connector.source not in visited: # don't add added
                matched = link.matcher(data)
                if matched:
                    queue.append((link.to_connector.source, matched))

    return track
