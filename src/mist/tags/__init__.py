import os

import mutagen
import requests
from mutagen.id3 import ID3, TCON, Encoding, APIC

from .. import Entry
from ..log import spawn_logger

logger = spawn_logger(__name__)

# TODO: preferredFormat, imageSize, imagePreferredFormat

def apply_metadata_mp3(file: str, data: Entry):
    logger.debug("applying mp3 metadata")

    assert os.path.isfile(file), f"not a file '{file}'"
    try:
        tags = ID3(file)
    except Exception as e:
        logger.debug(e, exc_info=True)
        tags = ID3()

    tags["TCON"] = TCON(encoding=Encoding.UTF16, text=data.genre)

    assert data.artwork
    response = requests.get(data.artwork)
    tags["APIC"] = APIC(encoding=Encoding.UTF16, mime='image/jpeg', # Change to 'image/png' if PNG
                        type=3,  # 3 = Front cover,
                        data=response.content)

    tags.save(file)
