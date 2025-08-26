import os

from . import shenanigans
from .errors import *
from .log import notify_target, log_error
from .utils import url_strip_utm, url_strip_share_identifier, sanitize_filename, print_progress_bar, format_bytes
from .core import *

def debug_print_call(func):
    """debug thingy"""
    def wrapper(*args, **kwargs):
        log_debug(func.__name__)
        return func(*args, **kwargs)
    return wrapper

### init

@debug_print_call
def init():
    if is_project():
        raise InitializationError("already initialized")

    project_config_template(project_config)

    save_project_config()

### clone

@debug_print_call
def clone(url, output=None, origin=None):
    dirname = output
    if output is None:
        dirname = sanitize_filename(shenanigans.get_remote_title(url))

    assert not os.path.exists(dirname), "path exists"

    os.makedirs(dirname)
    prev_dir = os.getcwd()
    os.chdir(dirname)

    init()
    remote_name = origin or DEFAULT_ORIGIN_NAME
    remote_add(remote_name, url)
    checkout(remote_name)

    # begin download
    pull()

    os.chdir(prev_dir)

### remote

from .commands.remote import *

### fetch

@debug_print_call
def fetch(remote=None, all=False, set_upstream=False):
    load_project_config()

    if set_upstream:
        checkout(remote)

    if remote is None:
        remote = get_current_remote()

    remote_data = ensure_remote(remote)

    remote_ids = shenanigans.get_remote_ids(remote_data["url"])

    filepath = os.path.join(PROJECT_DIRECTORY_ENTRIES, remote)
    os.makedirs(PROJECT_DIRECTORY_ENTRIES, exist_ok=True)
    with open(filepath, "w") as file:
        for id in remote_ids:
            file.write(f"{id}\n")

### merge

@debug_print_call
def merge(remote):
    load_project_config()

    directory = "."
    local_ids = set(shenanigans.get_local_ids(directory))
    remote_ids = set(get_remote_entries(remote))


    entries = remote_ids - local_ids
    if len(entries) == 0:
        print("up to date")
        return
    entries_length = len(entries)
    i = 0
    try:
        for e in entries:
            bar_template = f"({i}/{entries_length}) {e} $prefix |$bar| $percent %"
            print_progress_bar(0, 100, prefix="Preparing...", template=bar_template)
            def progress_hook(d):
                match d["status"]:
                    case "downloading":
                        downloaded = d["downloaded_bytes"]
                        total = d["total_bytes"]
                        percent = downloaded / total * 100
                        speed = d["speed"]
                        eta = d["eta"]
                        msg = f"{format_bytes(total)} at {format_bytes(speed)}/s"
                        print_progress_bar(percent, 100, prefix=f"Downloading ({msg})", template=bar_template, finish=False)
                    case "finished":
                        print_progress_bar(100, 100, prefix=f"Finished", template=bar_template, finish=True)
                    case _:
                        assert False, "unknown status"

            try:
                shenanigans.process_entry(e, output_directory=directory,
                                          progress_hook=progress_hook)
            except Exception as e:
                print_progress_bar(0, 100, prefix=f"Failed", template=bar_template, finish=True, empty='x')
                log_error(repr(e))

            i += 1
    except KeyboardInterrupt:
        print("stopped")
    else:
        notify_target()

### pull

@debug_print_call
def pull(remote=None, set_upstream=False):
    load_project_config()

    if set_upstream:
        checkout(remote)

    if remote is None:
        remote = get_current_remote()

    fetch(remote=remote)
    merge(remote=remote)

### status

@debug_print_call
def status():
    load_project_config()

    current_remote = get_current_remote()
    remote_ids = get_remote_entries(current_remote)
    local_ids = shenanigans.get_local_ids(".")

    remote_ids_set = set(remote_ids)
    local_ids_set = set(local_ids)
    missing = remote_ids_set - local_ids_set
    leftovers = local_ids_set - remote_ids_set
    print(f"remote: {current_remote}")
    print()
    print("missing:")
    print("\n".join([f"    {i}" for i in missing]))
    print()
    print("leftovers:")
    print("\n".join([f"    {i}" for i in leftovers]))
    print()

    duplicates_local = utils.find_duplicates(remote_ids)
    if duplicates_local:
        print("local duplicates:")
        print("\n".join([f"    {i}" for i in duplicates_local]))
        print()
    duplicates_remote = utils.find_duplicates(remote_ids)
    if duplicates_remote:
        print("remote duplicates:")
        print("\n".join([f"    {i}" for i in duplicates_remote]))
        print()

### checkout

@debug_print_call
def checkout(remote):
    load_project_config()

    ensure_remote(remote)
    set_current_remote(remote)

### list

@debug_print_call
def list_entries(remote=None, verbose=NotImplementedError()):
    if remote is None:
        print("\n".join(shenanigans.get_local_ids(".")))
        return

    load_project_config()
    print("\n".join(get_remote_entries(remote)))

### config

from .commands.config import *