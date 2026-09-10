import json
import logging
from dataclasses import dataclass

from .. import ConfigReader, Entry

"""
[artist "id"]
title = 
name = 
tags = 
links = 
[track "id"]
tags = 
name = 
title = 
genre = 
artist = 
"""

logger = logging.getLogger(__name__)

def _read_entry(file: str) -> Entry:

    reader = ConfigReader(path=file)
    reader.load()
    e = Entry()

    e.id = reader.get("id")
    assert e.id

    e.title = reader.get("title")
    e.name = reader.get("name")
    e.tags = json.loads(reader.get("tags", "[]"))
    e.genre = reader.get("genra")
    e.artwork = reader.get("artwork")
    e.artist_name = reader.get("artist_name")
    # e.visited = json.loads(reader.get("visited", "[]"))
    return e

def _write_entry(file: str, e: Entry):
    assert e.id is not None

    reader = ConfigReader(path=file)

    reader.set("id", e.id)

    reader.set("title", e.title or "")
    reader.set("name", e.name or "")
    reader.set("genra", e.genre or "")
    if e.tags:
        reader.set("tags", json.dumps(list(set(e.tags))))
    if e.artwork:
        reader.set("artwork", e.artwork)
    if e.artist_name:
        reader.set("artist_name", e.artist_name)
    # reader.set("{section_name}.visited", json.dumps(list(set(e.visited or []))))

    reader.save()
