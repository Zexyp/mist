import json
import logging
from pprint import pprint
from urllib.parse import urljoin

import microdata
import requests
from lxml import etree

from . import MetadataConnector, Source, NotSupported
from .scrape_utils import assert_status_code, urlappend, assert_single

class Autism(BaseException):
    pass

# https://schema.org/MusicGroup
# vs_i_gs_i
# vs.i.gs.i.e.hvdi.do.d@gmail.com
# vs.i.gs.i.e.hvdi.do.d@gmail.com0
# 128bbea5f91e9a85ab1de0e63c773ce0
# 780fb2343613416ce58cd11047544215
# vs_i_gs_i

URL_HOST = "https://www.last.fm"
# URL_GET_DIRECT_TEMPLATE = URL_HOST + "/music/{artist}/_/{title}/+tags"
# URL_HOST + "/music/{artist}/{title}/+tags" # no underscore is for albums, can be linked to using "Featured On"
URL_GET_AUTHOR = URL_HOST + "/music/{artist}"
URL_GET_SEARCH_TRACKS = URL_HOST + "/search/tracks"
URL_TAGS_ENDPOINT = "+tags"
URL_IMAGES_ENDPOINT = "+images"

logger = logging.getLogger(__name__)

def _detect_server_autism(response):
    if response.status_code == 600:
        raise Autism
    assert_status_code(response)

def retry_on_autism(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Autism:
                logger.debug("autism detected")
    return wrapper

# get track
def match_track(yt_ident: str, title: str) -> str | None:
    search_params = {
        "q": title,
    }

    response = requests.get(URL_GET_SEARCH_TRACKS, params=search_params)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    tracks = tree.xpath(f"//tr[.//a[@href='https://www.youtube.com/watch?v={yt_ident}']]/td[4]/a/@href")

    if not tracks:
        logger.debug("no matching track")
        return None

    return urljoin(URL_HOST, tracks[0])

def _extract_tags_basic(url) -> list[str]:
    response = requests.get(url)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    tags = tree.xpath("//a[starts-with(@href, '/tag/')]/text()")

    return tags

@retry_on_autism
def _extract_tags(lfm_url) -> list[str]:
    url = urlappend(lfm_url, URL_TAGS_ENDPOINT)

    response = requests.get(url)
    _detect_server_autism(response)

    tree = etree.HTML(response.content)
    tags = tree.xpath("//h3/a[starts-with(@href, '/tag/')]/text()")

    return tags

@retry_on_autism
def _extract_images(lfm_url) -> list[str]:
    url = urlappend(lfm_url, URL_IMAGES_ENDPOINT)

    response = requests.get(url)
    _detect_server_autism(response)

    tree = etree.HTML(response.content)
    images = tree.xpath("//*[contains(@class, 'image-list')]//img/@src")
    output = []
    for i in images:
        prts = i.rsplit("/", 2)
        # remove middle part like "avatar170s" and remove extension
        output.append(prts[0] + "/" + prts[2].rsplit(".", 1)[0])
    return output

# ezyzee

LastFmTrackUrl = str
LastFmArtistUrl = str

class LastFmConnector(MetadataConnector[LastFmTrackUrl, LastFmArtistUrl]):
    source = Source.LASTFM

    def get_track_name(self, track: LastFmTrackUrl) -> str:
        response = requests.get(track)
        assert_status_code(response)

        items = microdata.get_items(response.content)
        recording = [i for i in items if repr(i.itemtype[0]) == "http://schema.org/MusicRecording"][0]
        return recording.name

    def get_track_title(self, track: LastFmTrackUrl) -> str:
        response = requests.get(track)
        assert_status_code(response)

        items = microdata.get_items(response.content)
        recording = [i for i in items if repr(i.itemtype[0]) == "http://schema.org/MusicRecording"][0]
        return f"{recording.byArtist.name} - {recording.name}"

    def get_track_tags(self, track: LastFmTrackUrl) -> list[str]:
        return _extract_tags(track)

    def get_track_genre(self, track: LastFmTrackUrl) -> str:
        raise NotSupported

    def get_artist(self, track: LastFmTrackUrl) -> LastFmArtistUrl:
        response = requests.get(track)
        assert_status_code(response)

        items = microdata.get_items(response.content)
        # microdata are ass, i really mean it
        recording = [i for i in items if repr(i.itemtype[0]) == "http://schema.org/MusicRecording"][0]
        return urljoin(URL_HOST, repr(recording.byArtist.url))

    def get_track_artwork(self, track: LastFmTrackUrl) -> str:
        images = _extract_images(track)
        return images[0] if len(images) > 0 else None

    def get_artist_name(self, artist: LastFmArtistUrl) -> str:
        response = requests.get(artist)
        assert_status_code(response)

        items = microdata.get_items(response.content)
        # microdata are ass
        group = [i for i in items if repr(i.itemtype[0]) == "http://schema.org/MusicGroup"][0]
        return group.name

    def get_artist_links(self, artist: LastFmArtistUrl) -> list[str]:
        response = requests.get(artist)
        assert_status_code(response)

        tree = etree.HTML(response.content)
        links = tree.xpath("//h3[text()='External Links']/../ul/li/a/@href")
        return links

    def get_artist_tags(self, artist: LastFmArtistUrl) -> list[str]:
        return _extract_tags(artist)
