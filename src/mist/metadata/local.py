from dataclasses import dataclass

from .. import ConfigReader
from . import MetadataConnector, Source, Track

"""
[artist "id"]
title = 
name = 
tags = 
links = 
[track "id"]
tags = 
name = 
genre = 
artist = 
"""

class LocalConnector(MetadataConnector):
    source = Source.SOUNDCLOUD
