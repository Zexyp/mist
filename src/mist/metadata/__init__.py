import logging
import os
from enum import Enum, auto
from pprint import pprint, pformat
from typing import Generic, TypeVar, Callable, Optional, Any
from urllib.parse import urlparse, urlsplit
from abc import ABC, abstractmethod
from dataclasses import dataclass
import inspect

from .scrape_utils import assert_single
from .. import Entry
from ..utils import indent_list, MistEnum

logger = logging.getLogger(__name__)

# TODO: match user/artist

class NotSupported(Exception):
    pass

class Source(MistEnum):
    LOCAL = auto()
    YOUTUBE = auto()
    SOUNDCLOUD = auto()
    LASTFM = auto()
    BANDCAMP = auto()

def detect_source(url) -> Source:
    parsed_url = urlsplit(url)

    if parsed_url.scheme == "file":
        return Source.LOCAL

    match parsed_url.hostname:
        case "youtube.com" | "www.youtube.com" | "music.youtube.com":
            return Source.YOUTUBE
        case "soundcloud.com":
            return Source.SOUNDCLOUD
        case u if u.endswith(".bandcamp.com"):
            return Source.BANDCAMP
        case _:
            assert False, f"unknown source for '{parsed_url.netloc}'"

def url_source(source: Source, item: str):
    match source:
        case Source.YOUTUBE:
            return f"https://youtube.com/watch?v={item}"
        case Source.SOUNDCLOUD:
            return f"https://api-v2.soundcloud.com/tracks/{item}"
        case _:
            assert False, f"no template for source {source.name}"

TTrack = TypeVar('TTrack')
TArtist = TypeVar('TArtist')

class MetadataConnector(Generic[TTrack, TArtist], ABC):
    # TODO: album/playlist tags

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

    @abstractmethod
    def get_track_artwork(self, track: TTrack) -> str:
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

@dataclass
class Data:
    yt_video_id: str = None
    yt_title: str = None
    yt_channel_id: str = None
    yt_channel_links: list[str] = None

    lfm_track_url: str = None
    lfm_title: str = None
    lfm_artist_links: list[str] = None

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
        assert connector.source not in self.nodes
        self.nodes[connector.source] = connector

    def add_link(self, link: ConnectorLink):
        self.links.append(link)

    def get_node(self, source: Source) -> Optional[MetadataConnector]:
        return self.nodes.get(source)

    def get_links(self, source: Source) -> list[ConnectorLink]:
        return [link for link in self.links if link.from_connector.source == source]

connectors = MetadataConnectorRegistry()

def _build_registry():
    from . import lfm
    from . import yt
    from . import sc
    from . import bc

    youtube = yt.YouTubeConnector()
    soundcloud = sc.SoundCloudConnector()
    lastfm = lfm.LastFmConnector()
    bandcamp = bc.BandcampConnector()

    connectors.register(youtube)
    connectors.register(soundcloud)
    connectors.register(lastfm)
    connectors.register(bandcamp)

    def youtube_to_lastfm_matcher(data: Data):
        return lfm.match_track(data.yt_video_id, data.yt_title)

    def lastfm_to_soundcloud_matcher(data: Data):
        # lfm links should be set
        found = data.lfm_artist_links and [l for l in data.lfm_artist_links if urlsplit(l).hostname == "soundcloud.com"]
        if not found:
            return None

        # this line is fucking with my PyCharm 2025.2.1.1, erm *was*
        return sc.match_track_by_artist(data.lfm_title, assert_single(found))

    def youtube_to_soundcloud_matcher(data: Data):
        # yt links should be set but yt may have failed
        found = data.yt_channel_links and [l for l in data.yt_channel_links if urlsplit(l).hostname == "soundcloud.com"]
        if not found:
            return None

        assert len(found) == 1, "which sc link do i use (╯°□°）╯︵ ┻━┻"
        return sc.match_track_by_artist(data.yt_title, found[0])

    connectors.add_link(ConnectorLink(youtube, lastfm, youtube_to_lastfm_matcher))
    connectors.add_link(ConnectorLink(lastfm, soundcloud, lastfm_to_soundcloud_matcher))
    connectors.add_link(ConnectorLink(youtube, soundcloud, youtube_to_soundcloud_matcher))

_build_registry()

# TODO: utilize cache

def enrich(data: Data, track: Entry, item,  using_connector: MetadataConnector) -> Data:
    assert using_connector

    clean: bool = True

    def try_enrich(lmbd: Callable[[], Any]):
        nonlocal clean
        try:
            return lmbd()
        except NotSupported:
            return None
        except Exception as e:
            clean = False
            logger.error(f"connector '{type(using_connector).__name__}' failed during:\n{str(inspect.getsourcelines(lmbd)[0][0]).strip()}\n{type(e).__name__}: {e}")
            logger.debug(e, exc_info=True)
            return None

    track_name = try_enrich(lambda: using_connector.get_track_name(item))
    track_title =  try_enrich(lambda: using_connector.get_track_title(item))
    track_tags = try_enrich(lambda: using_connector.get_track_tags(item))
    track_genre = try_enrich(lambda: using_connector.get_track_genre(item))
    track_artwork = try_enrich(lambda: using_connector.get_track_artwork(item))

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
            data.yt_channel_id = artist
            data.yt_channel_links = artist_links
        case Source.LASTFM:
            data.lfm_track_url = item
            data.lfm_title = track_title
            data.lfm_artist_links = artist_links

    track.name = track.name or track_name
    track.title = track.title or track_title
    track.genre = track.genre or track_genre
    if track_tags:
        if track.tags:
            track.tags.extend(track_tags)
        else:
            track.tags = track_tags

    track.artist = track.artist or artist
    track.artist_name = track.artist_name or artist_name
    if artist_links:
        if track.artist_links:
            track.artist_links.extend(artist_links)
        else:
            track.artist_links = artist_links
    track.artwork = track.artwork or track_artwork

    if clean:
        if not track.visited:
            track.visited = set()
        track.visited.add(using_connector.source.name)

    logger.debug(f"enrichment pass:\n{pformat(track)}")

    return data

def obtain(source: Source, entry: str):
    logger.debug(f"collecting metadata for '{entry}'")

    visited: set[tuple[Source, str]] = set()

    track = Entry()
    data = Data()
    queue = [(source, entry)]

    while queue:
        source, item = queue.pop(0)

        if (source, item) in visited:
            continue

        connector = connectors.get_node(source)
        logger.debug(f"visiting {source.name}")

        # some crucial data are generated during this step, so we cannot use Entry.visited to avoid redoing work
        data = enrich(data, track, item, connector)

        visited.add((source, item))

        for link in connectors.get_links(source):
            if link.to_connector.source and link.to_connector.source not in visited: # don't add added
                logger.debug(f"matching {link.from_connector.source.name} => {link.to_connector.source.name}")
                matched = link.matcher(data)
                if matched:
                    queue.append((link.to_connector.source, matched))

    return track
