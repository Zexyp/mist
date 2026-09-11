import logging
import os
import warnings

from .. import FileEntry

logger = logging.getLogger(__name__)

def worktree_load(directory: str) -> list[FileEntry]:
    logger.debug("loading working tree")

    output = []
    for file in os.listdir(directory):
        if not os.path.isfile(file):
            continue

        entry = FileEntry()
        #filename = os.fsdecode(file)
        parts = file.rsplit(".", maxsplit=2)
        if len(parts) != 3:
            logger.debug(f"skipping file '{file}'")
            continue

        entry.id = parts[1]
        entry.title = parts[0]
        entry.file = file

        warnings.warn("TODO: extract tags here")

        output.append(entry)

    logger.debug(f"loaded {len(output)} entries")
    return output
