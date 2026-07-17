import logging
import os
from email.mime import image

import mutagen
from mutagen.id3 import ID3, TCON, Encoding, APIC, TIT2, TCOP, TMOO, TCOM

from .. import Entry
from . import imaging

logger = logging.getLogger(__name__)
# TODO: progressive, optimize, compress_level
# TODO: format, image.size {<width>x<height>}, image.format {
# # G = L, GA = LA, Idx = P, IdxA = PA
# {jpg, jpeg, jfif}[@[<quality>%][;{G, RGB}][;{4:4:4, 4:2:2, 4:2:0}]]
# # {jpg, jpeg, jfif}[@[<quality>%][;{G8, RGB8, YCbCr8}][;{4:4:4, 4:2:2, 4:2:0}]]
# png[@{Idx, IdxA, G, GA, RGB, RGBA}]
# # png[@{Idx1, Idx2, Idx4, Idx8, IdxA1, IdxA2, IdxA4, IdxA8, G1, G2, G4, G8, G16, GA8, GA16, RGB8, RGB16, RGBA8, RGBA16}]
# }, image.adjustment {zoom, pad, crop, stretch}

def _apply_tags_mp3(tags):
    pass
def _apply_tags_ogg(tags):
    pass
def _apply_tags_opus(tags):
    pass
def _apply_tags_flac(tags):
    pass

def _apply_image_mp3(tags):
    pass
def _apply_image_opus(tags):
    pass
def _apply_image_ogg(tags):
    pass
def _apply_image_flac(tags):
    pass

def _apply_tags(tags, entry: Entry):
    tags["TCON"] = TCON(encoding=Encoding.UTF16, text=entry.genre)
    tags["TIT2"] = TIT2(encoding=Encoding.UTF16, text=entry.title)
    if entry.tags:
        tags["TMOO"] = TMOO(encoding=Encoding.UTF16, text=", ".join(entry.tags))
    if entry.artist_name:
        tags["TCOM"] = TCOM(encoding=Encoding.UTF16, text=entry.artist_name)
    # TALB
    # TPOS
    # TRCK
    # TOWN
    # TS - TSOA, TSOT
    # fuck itunes-specific frames in particular
    tags["TCOP"] = TCOP(text="Don't care")

def _apply_image(tags, url: str, options: dict = None):
    mime, data = imaging.process(url, options or {})
    tags["APIC"] = APIC(encoding=Encoding.UTF16,
                        type=3,  # front cover
                        mime=mime,
                        data=data.read())

def apply(file: str, data: Entry, image_options: dict = None):
    logger.debug("applying mp3 metadata")

    assert os.path.isfile(file), f"not a file '{file}'"
    try:
        tags = ID3(file)
    except Exception as e:
        logger.debug(e, exc_info=True)
        raise

    tags.clear()

    _apply_tags(tags, entry=data)

    skip_image = image_options and image_options.get("format") == "none"
    if data.artwork and not skip_image:
        _apply_image(tags, data.artwork, options=image_options)

    tags.save(file)
