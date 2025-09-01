import json
import os
import concurrent.futures

from . import shenanigans, genrefier
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
    local_ids = set(shenanigans.get_local_ids(directory))
    remote_ids = set(get_remote_entries(remote))
    error_ids = set(get_remote_errors(remote) or [])
    if error_ids:
        log_verbose("errors will be skipped")

    entries = remote_ids - local_ids - error_ids
    if len(entries) == 0:
        print("up to date")
        return

    title_cache_file = get_cache_path_for_remote(remote, CACHE_TYPE_TITLES)
    shenanigans.title_cache.load_file(title_cache_file)

    entries_length = len(entries)
    i = 0
    failed = []

    def progress_hook(d):
        nonlocal i

        match d["status"]:
            case "downloading":
                downloaded = d["downloaded_bytes"]
                total = d["total_bytes"]
                percent = downloaded / total * 100
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
            shenanigans.process_entry(entry, output_directory=directory,
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

    shenanigans.title_cache.save_file(title_cache_file)

    if len(failed) > 0:
        error_cache_file = get_cache_path_for_remote(remote, CACHE_TYPE_ERRORS)
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
        remote = get_current_remote()

    fetch(remote=remote)
    merge(remote=remote)

### status

@command_print_call
def status():
    load_project_config()

    current_remote = get_current_remote()
    remote_ids = get_remote_entries(current_remote)
    local_ids = shenanigans.get_local_ids(".")
    error_ids_set = set(get_remote_errors(current_remote) or [])

    remote_ids_set = set(remote_ids)
    local_ids_set = set(local_ids)
    missing = remote_ids_set - local_ids_set - error_ids_set
    leftovers = local_ids_set - remote_ids_set
    print(f"remote: {current_remote}")
    print()
    print("missing:")
    print("\n".join([f"    {i}" for i in missing]))
    print()
    print("leftovers:")
    print("\n".join([f"    {i}" for i in leftovers]))
    print()
    if error_ids_set:
        print("errors:")
        print("\n".join([f"    {i}" for i in error_ids_set]))
        print()

    duplicates_local = utils.find_duplicates(local_ids)
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

@command_print_call
def checkout(remote):
    load_project_config()

    ensure_remote(remote)
    set_current_remote(remote)

### list

@command_print_call
def list_entries(remote=None, verbose=False):
    title_cache_file = None
    directory = "."
    if remote:
        load_project_config()
        listidlo = get_remote_entries(remote)
        title_getter = shenanigans.get_remote_entry_title

        title_cache_file = get_cache_path_for_remote(remote, CACHE_TYPE_TITLES)
    else:
        listidlo = shenanigans.get_local_ids(directory)
        title_getter = lambda x: shenanigans.get_local_entry_title(directory, x)

    if verbose:
        if title_cache_file:
            shenanigans.title_cache.load_file(title_cache_file)

        def append_title(i):
            listidlo[i] = f"{listidlo[i]}  {title_getter(listidlo[i])}"

        try:
            run_concurrently(append_title, range(len(listidlo)))
        except KeyboardInterrupt:
            print("stopped")

        if title_cache_file:
            shenanigans.title_cache.save_file(title_cache_file)

    print("\n".join(listidlo))

### config

from .commands.config import *

### tag

def tag():
    load_project_config()

    directory = "."
    tag_cache_file = get_cache_path_for_remote(get_current_remote(), CACHE_TYPE_TAGS)
    if not os.path.isfile(tag_cache_file):
        raise NoDataFileError("mby fetch *tags* first")

    entries = shenanigans.get_local_ids(directory)

    tags_dict = {}
    with open(tag_cache_file, "r") as file:
        while line := file.readline():
            parts = line.split(": ", 1)
            tags_dict[parts[0]] = json.loads(parts[1])
    for i in range(len(entries)):
        if entries[i] in tags_dict:
            entries[i] = f"{entries[i]}  {', '.join([repr(t) for t in tags_dict[entries[i]]])}"

    print("\n".join(entries))
