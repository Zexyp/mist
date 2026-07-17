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

def local_save(file, entries: list[Entry]):
    reader = ConfigReader(path=file)
    for e in entries:
        assert e.id is not None
        section_name = f"entry.{e.id}"
        reader.set(f"{section_name}.title", e.title or "")
        reader.set(f"{section_name}.name", e.name or "")
        reader.set(f"{section_name}.genra", e.genre or "")
        if e.tags:
            reader.set(f"{section_name}.tags", json.dumps(list(set(e.tags))))
        if e.artist_name:
            reader.set(f"{section_name}.artwork", e.artwork)
        if e.artist_name:
            reader.set(f"{section_name}.artist_name", e.artist_name)
        #reader.set(f"{section_name}.visited", json.dumps(list(set(e.visited or []))))

    reader.save()

    logger.debug(f"saved {len(entries)} entries")


def local_load(file) -> list[Entry]:
    reader = ConfigReader(path=file)
    reader.load()
    output = []
    for k in reader.keys("entry."):
        e = Entry(id=k)
        section_name = f"entry.{k}"
        e.title = reader.get(f"{section_name}.title")
        e.name = reader.get(f"{section_name}.name")
        e.tags = json.loads(reader.get(f"{section_name}.tags", "[]"))
        e.genre = reader.get(f"{section_name}.genra")
        e.artwork = reader.get(f"{section_name}.artwork")
        e.artist_name = reader.get(f"{section_name}.artist_name")
        #e.visited = json.loads(reader.get(f"{section_name}.visited", "[]"))
        output.append(e)
    logger.debug(f"loaded {len(output)} entries")
    return output