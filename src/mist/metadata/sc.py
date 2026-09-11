import functools
import logging
import os
import shlex
from pprint import pprint
import json
import re
from typing import Callable

import requests
from lxml import etree

from . import MetadataConnector, Source, NotSupported
from .scrape_utils import extract_script_data, json_dict_of_key, assert_status_code, assert_single

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

URL_GET_SEARCH = URL_HOST + "/search?q={query}"
URL_GET_SEARCH_PEOPLE = URL_HOST + "/search/people?q={query}"
URL_GET_SEARCH_SOUNDS = URL_HOST + "/search/sounds?q={query}"
URL_GET_SEARCH_ALBUMS = URL_HOST + "/search/albums?q={query}"
URL_GET_SEARCH_SETS = URL_HOST + "/search/sets?q={query}"

logger = logging.getLogger(__name__)

@functools.cache
def _prepare_client_id():
    response = requests.get(URL_HOST)
    assert_status_code(response)

    tree = etree.HTML(response.content)
    response_data = extract_script_data(tree, "window.__sc_hydration = ")

    client_data = assert_single([i for i in response_data if i["hydratable"] == "apiClient"])["data"]
    return client_data["id"]

@functools.cache
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

def _search_wrapper(url, query: str, limit: int | None):
    if limit is None:
        response = _wrap_request_with_client_id(url.format(query=query, limit=0))
        response_data = response.json()
        limit = response_data["total_results"]

    # fixme: next_href contains next page query

    response = _wrap_request_with_client_id(url.format(query=query, limit=limit))
    response_data = response.json()

    return response_data["collection"]

def search_users(query: str, limit: int | None = None):
    # lambda r: print(r["id"], r["username"], r["permalink"])
    return _search_wrapper(URL_API_GET_SEARCH_USERS, query, limit)

def search_tracks(query: str, limit: int | None = None):
    # lambda r: print(r["id"], r["title"], r["genre"], r["tag_list"])
    return _search_wrapper(URL_API_GET_SEARCH_TRACKS, query, limit)

def get_user_id(canonical_id: str):
    response = requests.get(URL_GET_USER_ID.format(canonical_id=canonical_id))
    if response.status_code == 404:
        return None
    assert_status_code(response)
    tree = etree.HTML(response.content)
    response_data = extract_script_data(tree, "window.__sc_hydration = ")
    user_data = assert_single([i for i in response_data if i["hydratable"] == "user"])["data"]
    return user_data["id"]

def match_track_by_artist(title: str, user_url: str):
    user_id = get_user_id(os.path.basename(user_url))
    if user_id is None:
        return None
    tracks = search_tracks(title)
    candidates = [i for i in tracks if user_id == i["user"]["id"] and title.lower() == i["title"].lower()]
    if len(candidates) > 1:
        logger.debug(f"multiple candidates: {candidates}")

    return candidates[0]["id"] if candidates else None

SoundCloudTrackId = str
SoundCloudUserId = str

class SoundCloudConnector(MetadataConnector[SoundCloudTrackId, SoundCloudUserId]):
    source = Source.SOUNDCLOUD

    def get_track_name(self, track: SoundCloudTrackId) -> str:
        response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track))
        response_data = response.json()
        return response_data["title"]

    def get_track_title(self, track: SoundCloudTrackId) -> str:
        response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track))
        response_data = response.json()
        label = response_data["title"]
        author = response_data["user"]["username"]
        if author not in label:
            label = f"{author} - {label}"
        return label

    def get_track_tags(self, track: SoundCloudTrackId) -> list[str]:
        response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track))
        response_data = response.json()
        tag_list = response_data["tag_list"]
        #logger.debug(f"fucky wucky tag_list: '{tag_list}'")
        tags = None

        if tag_list is None:
            tags = None
        elif not tag_list or tag_list.isspace():
            tags = []
        elif " " in tag_list:
            tags = shlex.split(tag_list)
        else:
            tags = tag_list.split(",")
        return tags

    def get_track_genre(self, track: SoundCloudTrackId) -> str:
        response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track))
        response_data = response.json()
        return response_data["genre"]

    def get_artist(self, track: SoundCloudTrackId) -> SoundCloudUserId:
        raise NotSupported

    def get_track_artwork(self, track: SoundCloudTrackId) -> str:
        response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=track))
        response_data = response.json()
        return response_data["artwork_url"]

    def get_artist_name(self, artist: SoundCloudUserId) -> str:
        response = _wrap_request_with_client_id(URL_API_GET_TRACKS.format(track_id=artist))
        response_data = response.json()
        return response_data["user"]["username"]

    def get_artist_links(self, artist: SoundCloudUserId) -> list[str]:
        response = _wrap_request_with_client_id(URL_API_GET_USERS_PROFILES.format(user_id=artist))
        response_data = response.json()
        return [profile["url"] for profile in response_data]

    def get_artist_tags(self, artist: SoundCloudUserId) -> list[str]:
        pass
