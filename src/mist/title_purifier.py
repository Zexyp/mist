from http.client import RemoteDisconnected
from time import sleep

import requests

from .log import log_error
from .utils import RateLimiter, assert_status_code

URL_HOST_YOUTUBE = "https://www.youtube.com"
URL_HOST_YOUTUBE_MUSIC = "https://music.youtube.com"

URL_POST_YOUTUBE_LINKS = URL_HOST_YOUTUBE + "/youtubei/v1/browse"
URL_POST_YOUTUBE_MUSIC_TITLE = URL_HOST_YOUTUBE_MUSIC + "/youtubei/v1/player"

limiter = RateLimiter(max_calls=10, period_seconds=20)

class RateLimitHitError(Exception):
    pass

# TODO: lang
def purify(videoId):
    limiter.acquire()

    json_data = {
        "videoId": videoId,
        "context": {
            "client": {
                "clientName": "WEB_REMIX",
                "clientVersion": "1.20240617.01.00-canary_control_1.20240624.01.00",
            },
        },
    }

    try:
        response = requests.post(URL_POST_YOUTUBE_MUSIC_TITLE, json=json_data)
    except RemoteDisconnected:
        log_error("getting throttled")
        raise RateLimitHitError
    assert_status_code(response)

    response_data = response.json()

    if "videoDetails" not in response_data:
        log_error("getting throttled, i guess?")
        raise RateLimitHitError

    details = response_data["videoDetails"]
    microformat = response_data["microformat"]

    owner = microformat["microformatDataRenderer"]["pageOwnerDetails"]["name"]

    # TODO: seems redundant
    owner = owner.removesuffix(" - Topic") # fuck topics

    if details["author"] not in details["title"]:
        name = f"""{details["author"]} - {details["title"]}"""
    else:
        name = details["title"]

    if details["author"] != owner:
        name += f" [{owner}]"
    
    return name

def _unused():
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
        "continuation": ""
    }
    pass
