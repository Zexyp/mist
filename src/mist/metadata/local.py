import os
import glob

from ..log import log_debug

def get_entry_title(directory, identifier):
    file = get_entry_file(directory, identifier)
    parts = file.rsplit('.', 2)
    return parts[0]

def get_entry_file(directory, identifier):
    files = []
    for f in glob.glob(os.path.join(directory, f"*.{identifier}.*")):
        if not os.path.isfile(os.path.join(directory, f)):
            continue

        f = os.path.basename(f)

        if len(parts := f.rsplit('.', 2)) <= 2:
            continue

        files.append(f)

    assert len(files) == 1, "incorrect find"
    return files[0]

def get_entries(directory):
    log_debug("reading local ids")

    ids = []
    for f in os.listdir(directory):
        if not os.path.isfile(os.path.join(directory, f)):
            continue
        f = os.path.basename(f)

        if len(parts := f.rsplit('.', 2)) <= 2:
            continue

        ids.append(parts[-2])

    return ids