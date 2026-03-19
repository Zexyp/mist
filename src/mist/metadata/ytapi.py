import json
from http.client import RemoteDisconnected
from typing import Any

import requests
from lxml import etree

from ..log import log_error
from ..utils import RateLimiter, assert_status_code
from .scrape_utils import json_dict_of_key, json_path_get, extract_script_data, RateLimitHitError

# todo: locale

URL_HOST_YOUTUBE = "https://www.youtube.com"
URL_HOST_YOUTUBE_MUSIC = "https://music.youtube.com"

URL_POST_YOUTUBE_LINKS = URL_HOST_YOUTUBE + "/youtubei/v1/browse"
URL_GET_YOUTUBE_CHANNEL = URL_HOST_YOUTUBE + "/channel/{channel_id}"

URL_POST_YOUTUBE_MUSIC_TITLE = URL_HOST_YOUTUBE_MUSIC + "/youtubei/v1/player"

limiter = RateLimiter(max_calls=5, period_seconds=5)

def _get_ytm_player_data(ident):
    json_data = {
        "videoId": ident,
        "context": {
            "client": {
                "clientName": "WEB_REMIX",
                "clientVersion": "1.20240617.01.00-canary_control_1.20240624.01.00",
            },
        },
    }

    limiter.acquire()

    try:
        response = requests.post(URL_POST_YOUTUBE_MUSIC_TITLE, json=json_data)
    except RemoteDisconnected:
        log_error("getting throttled")
        raise RateLimitHitError
    assert_status_code(response)

    response_data = response.json()

    return response_data

def _get_yt_channel_data(channel_id):
    limiter.acquire()

    try:
        response = requests.get(URL_GET_YOUTUBE_CHANNEL.format(channel_id=channel_id))
    except RemoteDisconnected:
        log_error("getting throttled")
        raise RateLimitHitError
    assert_status_code(response)

    tree = etree.HTML(response.content)
    response_data = extract_script_data(tree, "var ytInitialData = ")
    return response_data

def _parse_link(link) -> tuple[str, str]:
    vm = link["channelExternalLinkViewModel"]
    return vm["title"]["content"], vm["link"]["content"]

def get_links(channel_id) -> dict[str, str]:
    response_data = _get_yt_channel_data(channel_id)
    section_list_renderer_content = json_path_get(response_data, "header/pageHeaderRenderer/content/pageHeaderViewModel/description/descriptionPreviewViewModel/rendererContext/commandContext/onTap/innertubeCommand/showEngagementPanelEndpoint/engagementPanel/engagementPanelSectionListRenderer/content/sectionListRenderer/contents")
    item_section_renderer = json_dict_of_key(section_list_renderer_content, "itemSectionRenderer")
    continuation_item_renderer = json_dict_of_key(item_section_renderer["contents"], "continuationItemRenderer")
    token = json_path_get(continuation_item_renderer, "continuationEndpoint/continuationCommand/token")

    json_data = {
        "context": {
            "client": {
                "clientFormFactor": "UNKNOWN_FORM_FACTOR",
                "clientName": "WEB",
                "clientVersion": "2.20250828.01.00",
                "gl": "CZ",
                "hl": "en"
            }
        },
        "continuation": token
    }

    limiter.acquire()

    try:
        response = requests.post(URL_POST_YOUTUBE_LINKS, json=json_data)
    except RemoteDisconnected:
        log_error("getting throttled")
        raise RateLimitHitError
    assert_status_code(response)

    response_data = response.json()

    action = json_dict_of_key(response_data["onResponseReceivedEndpoints"], "appendContinuationItemsAction")
    about_renderer = json_dict_of_key(action["continuationItems"], "aboutChannelRenderer")
    links = json_path_get(about_renderer, "metadata/aboutChannelViewModel/links")

    ldict = {}
    for l in links:
        k, v = _parse_link(l)
        assert k not in ldict
        ldict[k] = v
    return ldict

def get_title(video_id):
    raise NotImplementedError

    response_data = _get_ytm_player_data(video_id)

    details = response_data["videoDetails"]
    owner = json_path_get(response_data, "videoDetails/microformat/microformatDataRenderer/pageOwnerDetails/name")

def get_author(video_id):
    raise NotImplementedError


# TODO: lang
def get_full_title(video_id):
    response_data = _get_ytm_player_data(video_id)

    if "videoDetails" not in response_data:
        log_error("getting throttled, i guess?")
        raise RateLimitHitError

    details = response_data["videoDetails"]
    microformat = response_data["microformat"]

    owner = microformat["microformatDataRenderer"]["pageOwnerDetails"]["name"]

    owner = owner.removesuffix(" - Topic")  # fuck topics

    if details["author"] not in details["title"]:
        name = f"""{details["author"]} - {details["title"]}"""
    else:
        name = details["title"]

    if owner not in details["author"]:
        name += f" [{owner}]"

    return name
