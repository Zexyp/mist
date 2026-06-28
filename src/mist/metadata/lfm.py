import json
from urllib.parse import urljoin

import requests
from lxml import etree
import yt_dlp

from . import assert_status_code, urlappend, MetadataConnector
from .. import log

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

logger = log.spawn_logger(__name__)

def get_track_tags(lfm_track_url: str) -> list[str]:
    pass

def get_artist(lfm_track_url: str) -> str:
    response = requests.get(lfm_track_url)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    return tree.xpath("//span[@interop='']/../ul/li/a/@href")

def get_artist_links(lfm_artist_url: str) -> list[str]:
    response = requests.get(lfm_artist_url)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    return tree.xpath("//h3[text()='External Links']/../ul/li/a/@href")

def extract_tags(lfm_url: str) -> list[str]:
    url = urlappend(lfm_url, URL_TAGS_ENDPOINT)

    response = requests.get(url)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    tags = tree.xpath("//h3/a[starts-with(@href, '/tag/')]/text()")

    return tags

# get track
def match_track(yt_ident: str, title: str) -> str | None:
    search_params = {
        "q": title,
    }

    response = requests.get(URL_GET_SEARCH_TRACKS, params=search_params)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    tracks = tree.xpath(f"//tr[.//a[@href='https://www.youtube.com/watch?v={yt_ident}']]/td[4]/a/@href")

    assert len(tracks) <= 1
    if not tracks:
        logger.debug("no track for genre lookup found")
        return None

    return urljoin(URL_HOST, tracks[0])

def _extract_tags_basic(url) -> list[str]:
    response = requests.get(url)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    tags = tree.xpath("//a[starts-with(@href, '/tag/')]/text()")

    return tags

# ezyzee

LastFmTrackUrl = str
LastFmArtistUrl = str

class LastFmConnector(MetadataConnector[LastFmTrackUrl, LastFmArtistUrl]):
    pass
