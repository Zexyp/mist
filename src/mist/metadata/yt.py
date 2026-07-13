import functools
import json
import logging
from http.client import RemoteDisconnected
from pprint import pprint
from typing import Any

import microdata
import requests
from lxml import etree

from . import MetadataConnector, Source, NotSupported
from .scrape_utils import json_dict_of_key, json_path_get, extract_script_data, RateLimitHitError, assert_status_code

# todo: locale

URL_HOST_YOUTUBE = "https://www.youtube.com"
URL_HOST_YOUTUBE_MUSIC = "https://music.youtube.com"

URL_POST_YOUTUBE_LINKS = URL_HOST_YOUTUBE + "/youtubei/v1/browse"
URL_GET_YOUTUBE_CHANNEL = URL_HOST_YOUTUBE + "/channel/{channel_id}"

URL_POST_YOUTUBE_MUSIC_TITLE = URL_HOST_YOUTUBE_MUSIC + "/youtubei/v1/player"

URL_GET_YOUTUBE_VIDEO = URL_HOST_YOUTUBE + "/watch?v={video_id}"
URL_GET_YOUTUBE_MUSIC_VIDEO = URL_HOST_YOUTUBE_MUSIC + "/watch?v={video_id}"

yt_client = {
    "clientFormFactor": "UNKNOWN_FORM_FACTOR",
    "clientName": "WEB",
    "clientVersion": "2.20250828.01.00",
    "gl": "CZ",
    "hl": "en"
}

ytm_client = {
    "clientName": "WEB_REMIX", # holy shit we finally have him here
    #
    #
    #                                                         .
    #              XXX$XX$XXXXXXXX$$XXXXXXXXXXXXXXXXX                               XXxXX+Xxx
    #               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    #               +$$$X$$$$$$$$$X$$$$$$$$$$$$$$$$$$$$                  x;          .
    #  .             $$$$$$$$$$$$$$$$$$$X$$$$$$$$$$$$$$$           .     X xX                  .:  .
    #                 $$$$$$$$$$$$$$$+         $$$$$$$$$+                       .                 . .
    #                  $$$$$$$$$$$$  $ x$$$$$ :. ;$$$$$$$         $X&    + +.        $
    #    .             $$$$$$$$$$$ X $:     x$$x   $$$$$$$      :.     +  :+    x  & +    X
    #         XXX       X$$$$$$$$   $X. ;+ x$$$$$: $$$$$$$      x    .   :.:         X   .   .
    #     .$          + .  $$$.   +;$X xxx  $  $$      $$$$       +; x ;  :        + $ :  .     .
    #    X       ;$X        $$   $$.$          :xX$$ X $$$$     &    x   :+&x    + X $    +   &   .  .
    #    X .x.            x$$$ X$$$$$$:     :  $$$$$ : $$$$X       +      ;      ;     : :;        .
    #     :     $:     .$$$$$$$  $.  $ $ $ $ .$  $ $  +$$$$$    x  x     ;       x   ; :      $x&
    #   .     X$$$$$X     $$$$$ $$$   :+ $x x $X+ Xx$ $$$$$$    x;X$          & +  . ; ;  .  x $
    #                     $$$$$$  $$$$ +$$$$$$$$$$$   $$$$$$    $: :                 ; +  .          .
    #    .                $$$$$$  $$;  XXxxxX$. .$$  $$$$$$$    ::         :$          ;          ;.:
    #                       X$$$$$    x$$$$$$$$;    $$$$:       x    : ;  ;   :    . $  X x          .
    #     .               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$      .XXXX     x x .X ;  .&;               .
    #   X                +$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$    X   .   +  ;+  & :     x  ;   : .   .
    #     $X$$$$$$$$$$$$  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$    : $$$$  X                        . . :
    #     $    X$$$    $  $X   X$$$$    x    xX    +X    $$    +$  $X   X      X     X            : ..
    #   X    X X$$$  $     :X$x     X$$  ;$$   X$$   $$$   x$$x   ;$$$   +X$$$    $$  ;
    #    .   X $$$$  $  X$$  $$$$  .$$$ $$$$   $$$$$$$$$$$$$$$$    $$$     X$$$  $;   $     X  ;
    #   .    X x$$$  ; X$$:  $$$   .$$$x       $$$   $$$$   $$$    $$$  X   X$$$$             & X  ..
    #        X X$$$    $$$$+.    + .$$$  X$$$  $$$   $$$x  .$$$    $$$  $ x  $$$$  .        $.::&. ..;
    #        $ X$$$    $$$X  $     .$$$  $$$$  $$$   $$$+  .$$$    $$$  XX  $ X$$$  .       x     . .
    #      $   X$$$    ;$$$$  :$   ;$$$  $$$$  $$$   $$$x  .$$$    $$$    X$.  $$$$.   X
    #   .  : :..   .:     X$;    X .;    $$$$  .                                       x             .
    #   .   $ :++xx+;;$$$x   X$$$$$; +X$$$$$$$$:$$$$$xXX$  XXXX$X XX$X$x XXX.   XXX.            ..; :
    #   .         .$$+$$$$$$$$$$$$$$$$$$$$$$$$$$$X  $                                :    : x      ..:
    #            .$$$ $$$$$;;;.X$&; ;++ ;x :XX +x x X X;;            :      x      :.       :
    #            $$$$ $$$$$    $ + $&  $ $  x$;.; x $  +X          &  $ ; x      X x+ +      + :
    #   .       $$$$$:$$$$$$$$$$$$$$$$$$$$$$$$$$$$                 & ;X         +X .+:;     +;:+   ..:
    #          $$$$$$$$$$$  . $$ + : x x  x:x$X  Xx:X X.X x        x  &      .  $& .; $   : +   . .
    #          $$$$$$$$$$$& & $  & $ $ $ X  +$  +$  $ $  $           X&            $  : x     X$    .
    #     .   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$        .         & :& +        & x    x
    #         XXxxxx++++:;:::.... $$$$$$$$$$$$$$.                  :             &    :        ;    .
    #                             $$$$$$$$$$$$$$                                   :   .    X$ . .....
    #                             $$$$$$$$$$$ $X X                 $    x x :+  :x     xx   :X     . .
    #   ..                        $$$$$  $ X$:$; X.   X;.X         & .+ + X x  X &        : x$
    #                             $$$$$$$$x$$$$$       .X+            x     x  :      :        +
    #                             $$$$$$$$$$$$$$                                 & +.   . + X.     ..:
    #                             $$$$; x $$$X X                            :.     & ..   + :;    . .
    #   .                         $$$$$ :;   $ $x  .:   x             .   +        &      + X&:;    .$
    # . .                         $$$$x  ; $xx  $ $:$ X x          x               .    :           XX
    #                            .$$$$;     .  X+                  X  X     : :  ;    . ;;         $$$
    #   ..                        $$$$$$$$$$$$$$$                  x  x   +      & &: + .       $$$$$X
    #                             $$$$$$$$$$$$$$$$.                $ +  : ;   XX & &:     $$$$.X $$$$X
    #                             $$$$$$$$$$$$$$$$                 x  . ;          &:     $$$$$  $$$$$
    #                             $$X$$X$$$$X$$$$$X     X   $         $                   x$$;  $.$$$$
    #                             $$$$$$$$$$$$$$$$$   : &&  & :X  x   $ $ x Xx  ; :       $$ :$$  $ $
    #                             $XXXXXXX$$$$$$$XXX  :        $   .                      $$ $$$ +$.
    #             $$X$$$$$$$$$$XX$$$XX$$$$$$X$$$$$XX$                                   +$$$$$$$$
    #              $XX$$XXXXXxxXxXXXXXXXXXXxxXXXXXXXxx                                XXXX$$X
    #
    #
    #
    "clientVersion": "1.20260630.02.00-canary_control_1.20260630.02.00",
}

logger = logging.getLogger(__name__)

_DUMP_UNEXPECTED_DATA = True

def _parse_link(link) -> str:
    vm = link["channelExternalLinkViewModel"]
    #vm["title"]["content"]
    link = vm["link"]["content"]
    return link

@functools.cache
def _get_ytm_player_data(video_id):
    json_data = {
        "videoId": video_id,
        "context": {
            "client": ytm_client,
        },
    }

    try:
        response = requests.post(URL_POST_YOUTUBE_MUSIC_TITLE, json=json_data)
    except RemoteDisconnected:
        logger.error("getting throttled")
        raise RateLimitHitError
    assert_status_code(response)

    response_data = response.json()

    return response_data

@functools.cache
def _get_yt_video_data(video_id):
    try:
        response = requests.get(URL_GET_YOUTUBE_VIDEO.format(video_id=video_id))
    except RemoteDisconnected:
        logger.error("getting throttled")
        raise RateLimitHitError
    assert_status_code(response)

    tree = etree.HTML(response.content)
    response_data = extract_script_data(tree, "window.WIZ_global_data = ")
    return response_data

@functools.cache
def _get_yt_channel_data(channel_id):
    try:
        response = requests.get(URL_GET_YOUTUBE_CHANNEL.format(channel_id=channel_id))
    except RemoteDisconnected:
        logger.error("getting throttled")
        raise RateLimitHitError
    assert_status_code(response)

    tree = etree.HTML(response.content)
    response_data = extract_script_data(tree, "var ytInitialData = ")
    return response_data

def _get_yt_channel_description_data(channel_id):
    response_data = _get_yt_channel_data(channel_id)
    on_tap = json_path_get(response_data, "header/pageHeaderRenderer/content/pageHeaderViewModel/description/descriptionPreviewViewModel/rendererContext/commandContext/onTap")
    innertube_command = json_path_get(on_tap, "innertubeCommand")
    continuation_item_renderer = json_path_get(innertube_command, "showEngagementPanelEndpoint/engagementPanel/engagementPanelSectionListRenderer/content/sectionListRenderer/contents/[0]/itemSectionRenderer/contents/[0]/continuationItemRenderer")
    continuation_command = json_path_get(continuation_item_renderer, "continuationEndpoint/continuationCommand")
    token = json_path_get(continuation_command, "token")

    json_data = {
        "context": {
            "client": yt_client
        },
        "continuation": token
    }

    try:
        response = requests.post(URL_POST_YOUTUBE_LINKS, json=json_data)
    except RemoteDisconnected:
        logger.error("getting throttled")
        raise RateLimitHitError
    assert_status_code(response)

    return response.json()

def _expect_unexpected(response):
    if response.status_code == 429:
        raise RateLimitHitError
    assert_status_code(response)

def canonicalize_channel_id(channel_url) -> str:
    response = requests.get(channel_url)
    assert_status_code(response)

    data = microdata.get_items(response.content)[0]
    # more data can be found in breadcrumbs
    return data.properties.url

YtVideoId = str
YtChannelId = str

class YouTubeConnector(MetadataConnector[YtVideoId, YtChannelId]):
    source = Source.YOUTUBE

    def get_track_name(self, track: YtVideoId) -> str:
        raise NotSupported

    # TODO: lang
    def get_track_title(self, track: YtVideoId) -> str:
        response_data = _get_ytm_player_data(track)

        if "videoDetails" not in response_data:
            logger.error("getting throttled, i guess?")
            if _DUMP_UNEXPECTED_DATA:
                logger.debug(json.dumps(response_data, indent=2))
            raise RateLimitHitError

        details = response_data["videoDetails"]
        microformat = response_data["microformat"]

        owner = microformat["microformatDataRenderer"]["pageOwnerDetails"]["name"]

        if owner.endswith(" - Topic"):
            owner = owner.removesuffix(" - Topic")  # fuck topics
            logger.debug("owner is topic")

        if details["author"] not in details["title"]:
            title = f"""{details["author"]} - {details["title"]}"""
        else:
            title = details["title"]

        if owner not in details["author"]:
            title += f" [{owner}]"

        logger.debug(f"final title is '{title}'")
        return title

    def get_track_tags(self, track: YtVideoId) -> list[str]:
        #raise NotSupported # i don't believe in ass

        response = requests.get(URL_GET_YOUTUBE_VIDEO.format(video_id=track))
        _expect_unexpected(response)

        data = microdata.get_items(response.content)[0]
        return data.keywords.split(",") if data.keywords else None

    def get_track_genre(self, track: YtVideoId) -> str:
        raise NotSupported

    def get_artist(self, track: YtVideoId) -> YtChannelId:
        response = requests.get(URL_GET_YOUTUBE_VIDEO.format(video_id=track))
        _expect_unexpected(response)

        tree = etree.HTML(response.content)
        data = extract_script_data(tree, "var ytInitialPlayerResponse = ")
        return data["videoDetails"]["channelId"]

    def get_track_artwork(self, track: YtVideoId) -> str:
        # fallbacks:
        # https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg
        # .../sddefault.jpg
        # .../mqdefault.jpg
        # .../default.jpg
        response_data = _get_ytm_player_data(track)
        thumbnail = response_data["videoDetails"]["thumbnail"]["thumbnails"][0]
        thumbnail_url = thumbnail["url"].rsplit("=", 1)[0]
        return thumbnail_url

    def get_artist_name(self, artist: YtChannelId) -> str:
        raise NotSupported

    def get_artist_links(self, artist: YtChannelId) -> list[str]:
        response_data = _get_yt_channel_description_data(artist)

        action = json_dict_of_key(response_data["onResponseReceivedEndpoints"], "appendContinuationItemsAction")
        about_renderer = json_dict_of_key(action["continuationItems"], "aboutChannelRenderer")
        about = json_path_get(about_renderer, "metadata/aboutChannelViewModel")

        if "links" not in about:
            return None

        links = about["links"]
        parsed = []
        for l in links:
            p = _parse_link(l)
            if p == "support.google.com/youtube?p=sub_to_oac":
                logger.debug("found garbage link")
                continue
            parsed.append(p)

        return parsed

    def get_artist_tags(self, artist: YtChannelId) -> list[str]:
        raise NotSupported