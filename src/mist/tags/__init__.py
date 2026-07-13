import logging
import os

import mutagen
import requests
from mutagen.id3 import ID3, TCON, Encoding, APIC

from .. import Entry

logger = logging.getLogger(__name__)

# TODO: preferredFormat, imageSize, imagePreferredFormat

def _apply_tags_mp3(tags):
    pass
def _apply_tags_opus(tags):
    pass
def _apply_tags_flac(tags):
    pass

def _apply_image_mp3(tags):
    pass
def _apply_image_opus(tags):
    pass
def _apply_image_flac(tags):
    pass

def apply_tags(entry: Entry):
    tags["TCON"] = TCON(encoding=Encoding.UTF16, text=entry.genre)

def apply_image(url: str):
    response = requests.get(data.artwork)
    tags["APIC"] = APIC(encoding=Encoding.UTF16, mime='image/jpeg',  # Change to 'image/png' if PNG
                        type=3,  # 3 = Front cover,
                        data=response.content)

def apply(file: str, data: Entry):
    logger.debug("applying mp3 metadata")

    assert os.path.isfile(file), f"not a file '{file}'"
    try:
        tags = ID3(file)
    except Exception as e:
        raise
        logger.debug(e, exc_info=True)

    apply_tags(entry=data)

    if data.artwork:
        apply_image(data.artwork)

    tags.save(file)
