from .. import command_print_call, shenanigans
from .. import *
from ..core import *
from ..shenanigans import title_cache


def _fetch_entries(remote_name, remote_data):
    remote_ids = shenanigans.get_remote_ids(remote_data["url"])

    filepath = get_cache_path_for_remote(remote_name, CACHE_TYPE_ENTRIES)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as file:
        for id in remote_ids:
            file.write(f"{id}\n")

def _fetch_tags(remote_name):
    directory = "."
    tag_cache_file = get_cache_path_for_remote(remote_name, CACHE_TYPE_TAGS)
    genrefier.tag_cache.load_file(tag_cache_file)
    title_cache_file = get_cache_path_for_remote(remote_name, CACHE_TYPE_TITLES)
    shenanigans.title_cache.load_file(title_cache_file)

    entries = get_remote_entries(remote_name)

    def download_tags(i):
        entries[
            i] = f"{entries[i]}  {genrefier.find_tags(entries[i], shenanigans.get_remote_entry_title(entries[i]))}"

    try:
        run_concurrently(download_tags, range(len(entries)))
    except KeyboardInterrupt:
        print("stopped")

    genrefier.tag_cache.save_file(tag_cache_file)
    shenanigans.title_cache.save_file(title_cache_file)

@command_print_call
def fetch(remote=None, all=False, set_upstream=False, tags=False):
    if all:
        raise NotImplementedError("fetching all remotes is not yet implemented")

    load_project_config()

    if set_upstream:
        checkout(remote)

    if remote is None:
        remote = get_current_remote()

    remote_data = ensure_remote(remote)

    if tags:
        _fetch_tags(remote)
        return

    _fetch_entries(remote, remote_data)
