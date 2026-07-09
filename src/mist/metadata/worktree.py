import os

from .. import Entry
from ..log import spawn_logger

logger = spawn_logger(__name__)

def worktree_load(directory: str) -> list[Entry]:
    logger.debug("loading working tree")

    output = []
    for file in os.listdir(directory):
        if not os.path.isfile(file):
            continue

        entry = Entry()
        #filename = os.fsdecode(file)
        parts = file.rsplit(".", maxsplit=2)
        if len(parts) != 3:
            logger.debug(f"skipping file '{file}'")
            continue

        entry.id = parts[1]
        entry.title = parts[0]

        # TODO: extract tags here

        output.append(entry)

    return output
