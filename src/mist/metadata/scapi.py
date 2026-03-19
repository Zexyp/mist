import functools
from pprint import pprint
import json
import re
from typing import Callable

import requests
from lxml import etree

from .scrape_utils import extract_script_data, json_dict_of_key
from ..utils import assert_status_code

# todo: locale

URL_HOST = "https://soundcloud.com"
URL_HOST_API = "https://api.soundcloud.com"
URL_HOST_API2 = "https://api-v2.soundcloud.com"
URL_HOST_CDN = "https://a-v2.sndcdn.com"

URL_API_GET_TRACKS = URL_HOST_API2 + "/tracks/{track_id}"
# user urn could be used
URL_API_GET_USERS = URL_HOST_API2 + "/users/{user_id}"
# user urn must be used
URL_API_GET_USERS_PROFILES = URL_HOST_API2 + "/users/soundcloud:users:{user_id}/web-profiles"
# limit is 300
# fixme: max batch is 300
URL_API_GET_SEARCH_USERS = URL_HOST_API2 + "/search/users?q={query}&limit={limit}&offset=0"
URL_API_GET_SEARCH_TRACKS = URL_HOST_API2 + "/search/tracks?q={query}&limit={limit}&offset=0"

URL_GET_USER_ID = URL_HOST + "/{canonical_id}"
client_id_resources = [
    URL_HOST_CDN + "/assets/0-e749f414.js",
    URL_HOST_CDN + "/assets/52-bb10f8b9.js",
    URL_HOST_CDN + "/assets/51-c65d6649.js",
]
URL_GET_CLIENT_ID = client_id_resources[0]

URL_GET_SEARCH = URL_HOST + "/search?q={query}"
URL_GET_SEARCH_PEOPLE = URL_HOST + "/search/people?q={query}"
URL_GET_SEARCH_SOUNDS = URL_HOST + "/search/sounds?q={query}"
URL_GET_SEARCH_ALBUMS = URL_HOST + "/search/albums?q={query}"
URL_GET_SEARCH_SETS = URL_HOST + "/search/sets?q={query}"

@functools.lru_cache
def _prepare_client_id():
    response = requests.get(URL_GET_CLIENT_ID)
    assert_status_code(response)

    # sanity check included xd
    key_regex = r"[A-Za-z0-9]{32}"
    var_regex = "client_id"
    matches = re.finditer(rf'\"{var_regex}=({key_regex})\"|{var_regex}:\"({key_regex})\"', response.text)
    ids = []
    for m in matches:
        ids.append(m.group(1) or m.group(2))

    assert all(x == ids[0] for x in ids)

    return ids[0]

def _wrap_request_with_client_id(url):
    params = {
        "client_id": _prepare_client_id(),
    }

    # rate limited without this
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    }

    response = requests.get(url, params=params, headers=headers)
    assert_status_code(response)

    return response

def _search_wrapper(url, query: str, limit: int | None, item_callback: Callable):
    if limit is None:
        response = _wrap_request_with_client_id(url.format(query=query, limit=0))
        response_data = response.json()
        limit = response_data["total_results"]

    # fixme: next_href contains next page query

    response = _wrap_request_with_client_id(url.format(query=query, limit=limit))
    response_data = response.json()

    for r in response_data["collection"]:
        item_callback(r)

def search_users(query: str, limit: int | None = None):
    _search_wrapper(URL_API_GET_SEARCH_USERS, query, limit, lambda r: print(r["id"], r["username"], r["permalink"]))

def search_tracks(query: str, limit: int | None = None):
    _search_wrapper(URL_API_GET_SEARCH_TRACKS, query, limit, lambda r: print(r["id"], r["title"], r["genre"], r["tag_list"]))


def get_user_id(canonical_id: str) -> str:
    response = requests.get(URL_GET_USER_ID.format(canonical_id=canonical_id))
    assert_status_code(response)
    tree = etree.HTML(response.content)
    response_data = extract_script_data(tree, "window.__sc_hydration = ")
    return json_dict_of_key(response_data, "data")["id"]

def get_links(user_id) -> dict[str, str]:
    response = _wrap_request_with_client_id(URL_API_GET_USERS_PROFILES.format(user_id=user_id))
    response_data = response.json()
    return {profile["title"]: profile["url"] for profile in response_data}

def get_tags(track_id):
    response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track_id))
    response_data = response.json()
    tag_list = response_data["tag_list"]
    return tag_list.split(" ") if tag_list and not tag_list.isspace() else []

def get_genra(track_id):
    response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track_id))
    response_data = response.json()
    return response_data["genre"]

def get_title(track_id):
    response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track_id))
    response_data = response.json()
    return response_data["user"]["username"]

def get_author(track_id):
    response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track_id))
    response_data = response.json()
    return response_data["title"]

def get_full_title(track_id):
    response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track_id))
    response_data = response.json()
    label = response_data["title"]
    author = response_data["user"]["username"]
    if author not in label:
        label = f"{author} - {label}"
    return label
