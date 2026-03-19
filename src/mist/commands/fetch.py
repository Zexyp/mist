import os

from .. import command_print_call, shenanigans, metadata, core
from .. import *

def _fetch_entries(remote_name, remote_data):
    remote_ids = shenanigans.get_remote_ids(remote_data["url"])

    filepath = core.remote.get_cache_path(remote_name, core.CACHE_TYPE_ENTRIES)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as file:
        for id in remote_ids:
            file.write(f"{id}\n")

def _fetch_tags(remote_name):
    remote_url = core.remote.ensure(remote_name)["url"]

    metadata_cache_dir = core.remote.get_cache_path(remote_name)

    pltf = metadata.detect_platform(remote_url)
    metadata.load_cache(metadata_cache_dir)

    entries = core.remote.get_entries(remote_name)

    def download_tags(i):
        entries[i] = f"{entries[i]}  {metadata.get_tags(pltf, entries[i])}"

    try:
        run_concurrently(download_tags, range(len(entries)))
    except KeyboardInterrupt:
        print("stopped")

    metadata.save_cache(metadata_cache_dir)

@command_print_call
def fetch(remote=None, all=False, set_upstream=False, tags=False):
    if all:
        raise NotImplementedError("fetching all remotes is not yet implemented")

    load_project_config()

    if set_upstream:
        checkout(remote)

    if remote is None:
        remote = core.remote.get_current()

    remote_data = core.remote.ensure(remote)

    if tags:
        _fetch_tags(remote)
        return

    _fetch_entries(remote, remote_data)
