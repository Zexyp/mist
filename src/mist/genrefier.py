import json
from urllib.parse import urljoin

import requests
from lxml import etree

from .log import log_verbose, log_debug
from .utils import FileCache, assert_status_code

URL_HOST = "https://www.last.fm"
URL_GET_DIRECT_TEMPLATE = "https://www.last.fm/music/{artist}/_/{title}/+tags"
URL_GET_SEARCH_TRACKS = "https://www.last.fm/search/tracks"

tag_cache: FileCache = FileCache(serialize=lambda v: json.dumps(v), deserialize=lambda v: json.loads(v))

# wtf is this piece of shit
def get_tags_direct(artist: str, title: str) -> list[str]:
    return _extrac_tags(URL_GET_DIRECT_TEMPLATE.format(artist=artist, title=title))

def _extrac_tags(track_url):
    log_verbose(f"getting tags")
    response = requests.get(track_url)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    tags = tree.xpath("//a[starts-with(@href, '/tag/')]/text()")
    log_debug("found tags: " + ", ".join([repr(t) for t in tags]))
    return tags

@tag_cache.cached(key=lambda i, t: i)
def find_tags(ident: str, title: str) -> list[str] | None:
    search_params = {
        "q": title,
    }

    response = requests.get(URL_GET_SEARCH_TRACKS, params=search_params)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    tracks = tree.xpath(f"//tr[.//a[@href='https://www.youtube.com/watch?v={ident}']]/td[4]/a/@href")
    assert len(tracks) <= 1
    if not tracks:
        log_verbose("no track for genre lookup found")
        return None

    return _extrac_tags(urljoin(URL_HOST, tracks[0]))

# ezyzee
