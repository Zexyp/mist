from http.client import RemoteDisconnected
from time import sleep

import requests

from .log import log_error
from .utils import RateLimiter

limiter = RateLimiter(max_calls=10, period_seconds=20)
session = requests.Session()
# TODO: lang
def purify(videoId):
    limiter.acquire()

    json_data = {
        'videoId': videoId,
        'context': {
            'client': {
                'clientName': 'WEB_REMIX',
                'clientVersion': '1.20240617.01.00-canary_control_1.20240624.01.00',
            },
        },
    }

    try:
        response = session.post('https://music.youtube.com/youtubei/v1/player', json=json_data)
    except RemoteDisconnected:
        log_error("getting throttled")
        raise
    assert response.status_code == 200

    response_data = response.json()

    if "videoDetails" not in response_data:
        log_error("getting throttled, i guess?")

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
