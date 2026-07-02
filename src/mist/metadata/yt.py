import json
from http.client import RemoteDisconnected
from pprint import pprint
from typing import Any

import microdata
import requests
from lxml import etree

from . import MetadataConnector, Source, TArtist, TTrack, NotSupported
from .. import log
from .scrape_utils import json_dict_of_key, json_path_get, extract_script_data, RateLimitHitError, assert_status_code

# todo: locale

URL_HOST_YOUTUBE = "https://www.youtube.com"
URL_HOST_YOUTUBE_MUSIC = "https://music.youtube.com"

URL_POST_YOUTUBE_LINKS = URL_HOST_YOUTUBE + "/youtubei/v1/browse"
URL_GET_YOUTUBE_CHANNEL = URL_HOST_YOUTUBE + "/channel/{channel_id}"

URL_POST_YOUTUBE_MUSIC_TITLE = URL_HOST_YOUTUBE_MUSIC + "/youtubei/v1/player"

URL_GET_YOUTUBE_VIDEO = URL_HOST_YOUTUBE + "/watch?v={video_id}"

logger = log.spawn_logger(__name__)

def _parse_link(link) -> tuple[str, str]:
    vm = link["channelExternalLinkViewModel"]
    return vm["title"]["content"], vm["link"]["content"]

def _get_ytm_player_data(ident):
    json_data = {
        "videoId": ident,
        "context": {
            "client": {
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
                "clientVersion": "1.20240617.01.00-canary_control_1.20240624.01.00",
            },
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

    def get_track_tags(self, track: YtVideoId) -> list[str]:
        #raise NotSupported # i don't believe in ass

        response = requests.get(URL_GET_YOUTUBE_VIDEO.format(video_id=track))
        assert_status_code(response)

        data = microdata.get_items(response.content)[0]
        return data.keywords.split(",")

    def get_track_genre(self, track: YtVideoId) -> str:
        raise NotSupported

    def get_artist(self, track: YtVideoId) -> YtChannelId:
        response = requests.get(URL_GET_YOUTUBE_VIDEO.format(video_id=track))
        assert_status_code(response)

        tree = etree.HTML(response.content)
        data = extract_script_data(tree, "var ytInitialPlayerResponse = ")
        return data["videoDetails"]["channelId"]

    def get_artist_name(self, artist: YtChannelId) -> str:
        raise NotSupported

    def get_artist_links(self, artist: YtChannelId) -> dict[str, str]:
        response_data = _get_yt_channel_data(artist)
        section_list_renderer_content = json_path_get(response_data,
                                                      "header/pageHeaderRenderer/content/pageHeaderViewModel/description/descriptionPreviewViewModel/rendererContext/commandContext/onTap/innertubeCommand/showEngagementPanelEndpoint/engagementPanel/engagementPanelSectionListRenderer/content/sectionListRenderer/contents")
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

        try:
            response = requests.post(URL_POST_YOUTUBE_LINKS, json=json_data)
        except RemoteDisconnected:
            logger.error("getting throttled")
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

    def get_artist_tags(self, artist: YtChannelId) -> list[str]:
        raise NotSupported