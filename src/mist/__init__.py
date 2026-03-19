import json
import os
import concurrent.futures

from . import shenanigans, metadata
from .errors import *
from .log import notify_target, log_error
from .utils import url_strip_utm, url_strip_share_identifier, sanitize_filename, print_progress_bar, format_bytes
from .core import *
from .platform import run_concurrently

def command_print_call(func):
    """debug thingy"""
    def wrapper(*args, **kwargs):
        log_debug(f"command: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

### init

@command_print_call
def init():
    if is_project():
        raise InitializationError("already initialized")

    project_config_template(project_config)

    save_project_config()

### clone

@command_print_call
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

from .commands.fetch import *

### merge

@command_print_call
def merge(remote):
    load_project_config()

    directory = "."
    local_ids = set(metadata.local.get_entries(directory))
    remote_ids = set(core.remote.get_entries(remote))
    error_ids = set(core.remote.get_errors(remote) or [])
    if error_ids:
        log_verbose("errors will be skipped")

    entries = remote_ids - local_ids - error_ids
    if len(entries) == 0:
        print("up to date")
        return

    remote_data = core.remote.ensure(remote)
    pltf = metadata.detect_platform(remote_data["url"])

    metadata_cache_file = core.remote.get_cache_path(remote)
    metadata.load_cache(metadata_cache_file)

    entries_length = len(entries)
    i = 0
    failed = []

    def progress_hook(d):
        nonlocal i

        match d["status"]:
            case "downloading":
                downloaded = d["downloaded_bytes"]
                total = d.get("total_bytes", 0)
                percent = downloaded / total * 100 if total else 0
                speed = d["speed"]
                eta = d["eta"]
                msg = f"{format_bytes(total)} at {format_bytes(speed)}/s"
                print_progress_bar(i + percent / 100, entries_length, prefix=f"Downloading {d['id']} ({d['title']}) [{msg}]", finish=False)
            case "finished":
                i += 1
                print_progress_bar(i, entries_length, prefix=f"Finished {d['id']} ({d['title']})", finish=False)
            case _:
                assert False, "unknown status"

    def handle_entry(entry):
        try:
            shenanigans.process_entry(pltf, entry, output_directory=directory,
                                      progress_hook=progress_hook)
        except shenanigans.ShenanigansError as e:
            failed.append(entry)
            log_error(repr(e))

    print_progress_bar(0, entries_length, prefix="Preparing...")

    try:
        run_concurrently(handle_entry, entries)
    except KeyboardInterrupt:
        print("stopped")
    else:
        notify_target()
        print_progress_bar(i, entries_length, prefix="Done", finish=True)

    metadata.save_cache(metadata_cache_file)

    if len(failed) > 0:
        error_cache_file = core.remote.get_cache_path(remote, CACHE_TYPE_ERRORS)
        os.makedirs(os.path.dirname(error_cache_file), exist_ok=True)
        with open(error_cache_file, "w") as file:
            for item in {*failed, *error_ids}:
                file.write(f"{item}\n")
        log_verbose("new errors recorded")

### pull

@command_print_call
def pull(remote=None, set_upstream=False):
    load_project_config()

    if set_upstream:
        checkout(remote)

    if remote is None:
        remote = core.remote.get_current()

    fetch(remote=remote)
    merge(remote=remote)

### status

from .commands.status import *

### checkout

@command_print_call
def checkout(remote):
    load_project_config()

    core.remote.ensure(remote)
    core.remote.set_current(remote)

### list

@command_print_call
def list_entries(remote=None, verbose=False):
    metadata_cache_dir = None
    directory = "."
    if remote:
        load_project_config()
        remote_url = core.remote.ensure(remote)["url"]

        listidlo = core.remote.get_entries(remote)
        title_getter = lambda x: metadata.get_full_title(metadata.detect_platform(remote_url), x)

        metadata_cache_dir = core.remote.get_cache_path(remote)
    else:
        listidlo = metadata.local.get_entries(directory)
        title_getter = lambda x: metadata.local.get_entry_title(directory, x)

    if verbose:
        if metadata_cache_dir:
            metadata.load_cache(metadata_cache_dir)

        def append_title(i):
            listidlo[i] = f"{listidlo[i]}  {title_getter(listidlo[i])}"

        try:
            run_concurrently(append_title, range(len(listidlo)))
        except KeyboardInterrupt:
            print("stopped")

        if metadata_cache_dir:
            metadata.save_cache(metadata_cache_dir)

    print("\n".join(listidlo))

### config

from .commands.config import *

### tag

def tag():
    load_project_config()

    directory = "."
    remote_name = core.remote.get_current()
    metadata_cache_dir = core.remote.get_cache_path(remote_name)
    if not os.path.isfile(core.remote.get_cache_path(remote_name, CACHE_TYPE_METADATA)):
        raise NoDataFileError("mby fetch *tags* first")

    entries = metadata.local.get_entries(directory)
    remote_entries = core.remote.get_entries(remote_name)
    entries = [x for x in entries if x in remote_entries]

    metadata.load_cache(metadata_cache_dir)
    pltf = metadata.detect_platform(core.remote.ensure(remote_name)["url"])

    for i in range(len(entries)):
        entries[i] = f"{entries[i]}  {metadata.get_tags(pltf, entries[i])}"

    metadata.save_cache(metadata_cache_dir)

    print("\n".join(entries))
