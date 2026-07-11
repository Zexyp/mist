import functools
import os.path
from http.client import responses
from urllib.parse import urlsplit, urljoin

import requests

from lxml import etree

from . import MetadataConnector, NotSupported, Source
from .scrape_utils import assert_status_code, assert_single
from .. import Entry
from ..log import spawn_logger

logger = spawn_logger(__name__)

URL_HOST = "https://bandcamp.com"

URL_GET_SEARCH = URL_HOST + "/search"
URL_GET_SEARCH_QUERY = URL_GET_SEARCH + "?q={query}&item_type={item_type}"
MAGIC = "_fs-ch-1T1wmsGaOgGaSxcX"
URL_POST_POSTBACK = URL_HOST + f"/{MAGIC}/fst-post-back"
"""
item types:
None - all
b - artists & labels
a - albums
t - tracks
f - fans
"""

search_session = requests.Session()

@functools.cache
def _ensure_cookies():
    raise NotImplementedError

    search_session.get(URL_GET_SEARCH)
    search_session.post(URL_GET_SEARCH_QUERY)
    print(search_session.cookies.items())

def _search_wrapper(query, item_type: str) -> list[str]:
    _ensure_cookies()

    url = URL_GET_SEARCH.format(query=query, item_type=item_type)
    response = search_session.get(url)
    assert_status_code(response)
    print(response.text)

    tree = etree.HTML(response.content)
    links = tree.xpath("//*[contains(@class, 'results')]/ul/li/a/@href")
    return [urlsplit(l)._replace(query='', fragment='').geturl() for l in links]

def search_artists(query: str) -> list[str]:
    return _search_wrapper(query, "a")

def search_tracks(query: str) -> list[str]:
    return _search_wrapper(query, "t")

def match_artist(artist_name: str, artist_links):
    # we might be able to eyeball the url :thinking:
    url_name = "".join(a for a in artist_name if a.isalpha()).lower()
    split_host = urlsplit(URL_HOST)
    # koukněte, co mit to vyrostlo u prdele
    url = split_host._replace(netloc=f"{url_name}.{split_host.netloc}").geturl()

    links = BandcampConnector.get_artist_links(None, url)

    # TODO: canonize
    if any(l in artist_links for l in links):
        return url
    return None

def get_artist_tracks(artist_url: str):
    response = requests.get(artist_url)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    tracks = tree.xpath("//ol[@id='music-grid']/li/a")
    return [Entry(url=urljoin(artist_url, i.attrib["href"]),
                  name=assert_single(i.xpath("./p[@class='title']")).text.strip(),
                  artist=artist_url) for i in tracks]

def match_track_by_artist(track_name: str, artist_name: str, artist_links):
    raise NotImplementedError
    artist = match_artist(artist_name, artist_links)
    if not artist:
        return None
    tracks = get_artist_tracks(artist)
    if not tracks:
        return None
    candidates = [i for i in tracks if i.name.lower() == track_name.lower()]

    if len(candidates) > 1:
        logger.debug(f"multiple candidates: {candidates}")

    return candidates[0]["id"] if candidates else None


BandcampTrackUrl = str
BandcampArtistUrl = str

class BandcampConnector(MetadataConnector[BandcampTrackUrl, BandcampArtistUrl]):
    source = Source.BANDCAMP

    def get_track_name(self, track: BandcampTrackUrl) -> str:
        raise NotSupported

    def get_track_title(self, track: BandcampTrackUrl) -> str:
        raise NotSupported

    def get_track_tags(self, track: BandcampTrackUrl) -> list[str]:
        response = requests.get(track)
        assert_status_code(response)

        tree = etree.HTML(response.content)
        tags = tree.xpath("//h3/span[text()='Tags']/../../a/text()")
        return [t.strip() for t in tags]

    def get_track_genre(self, track: BandcampTrackUrl) -> str:
        raise NotSupported

    def get_artist(self, track: BandcampTrackUrl) -> BandcampArtistUrl:
        raise NotSupported

    def get_track_artwork(self, track: BandcampTrackUrl) -> str:
        responses = requests.get(track)
        assert_status_code(responses)

        tree = etree.HTML(responses.content)
        src = assert_single(tree.xpath("//*[@id='tralbumArt']//img/@src"))
        splt = src.rsplit(".", maxsplit=1)
        src = splt[0].rsplit("_", 1)[0] + "_0." + splt[1] # set lod to 0
        return src

    def get_artist_name(self, artist: BandcampArtistUrl) -> str:
        raise NotSupported

    def get_artist_links(self, artist: BandcampArtistUrl) -> list[str]:
        response = requests.get(artist)
        assert_status_code(response)

        tree = etree.HTML(response.content)
        links = tree.xpath("//ol[@id='band-links']/li/a/@href")
        return links

    def get_artist_tags(self, artist: BandcampArtistUrl) -> list[str]:
        raise NotSupported
