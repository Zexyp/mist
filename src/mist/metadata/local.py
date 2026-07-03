import json
from dataclasses import dataclass

from .. import ConfigReader, Entry
from .. import log

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

def save(file, entries: list[Entry]):
    log.debug(f"saving {len(entries)} entries")
    reader = ConfigReader(path=file)
    for e in entries:
        section_name = f"entry.{e.id}"
        reader.set(f"{section_name}.title", e.title or "")
        reader.set(f"{section_name}.name", e.name or "")
        reader.set(f"{section_name}.tags", json.dumps(e.tags or []))
        reader.set(f"{section_name}.genra", e.genre or "")
    reader.save()

def load(file) -> list[Entry]:
    reader = ConfigReader(path=file)
    reader.load()
    output = []
    for k in reader.keys("entry."):
        e = Entry()
        section_name = f"entry.{k}"
        e.title = reader.get(f"{section_name}.title")
        e.name = reader.get(f"{section_name}.name")
        e.tags = json.loads(reader.get(f"{section_name}.tags"))
        e.genre = reader.get(f"{section_name}.genra")
        output.append(e)
    log.debug(f"loaded {len(output)} entries")
    return output