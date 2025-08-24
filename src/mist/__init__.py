import configparser
import os
from importlib.metadata import version
from tabnanny import check

from . import shenanigans
from .errors import RemoteNotFoundError
from .utils import url_strip_utm, url_strip_share_identifier, sanitize_filename, print_progress_bar, format_bytes

PROJECT_DIRECTORY = ".mist"
PROJECT_FILEPATH_CONFIG = PROJECT_DIRECTORY + "/config"
PROJECT_FILEPATH_REMOTE = PROJECT_DIRECTORY + "/remote"
PROJECT_DIRECTORY_ENTRIES = PROJECT_DIRECTORY + "/entries"
# TODO: structure multiple remotes
# TODO: submodules will allow for directory structure
# TODO: bracketeer
# TODO: vip check
# TODO: extended mix check

FILENAME_IGNORE = ".mistignore"
FILENAME_CONFIG = ".mistconfig"
FILENAME_MODULES = ".mistmodules"

DEFAULT_ORIGIN_NAME = "origin"

config: configparser.ConfigParser | None = None

def ensure_remote(remote):
    section_name = f"remote \"{remote}\""
    if not section_name in config.sections():
        raise RemoteNotFoundError(f"no such remote '{remote}'")
    return config[section_name]

def set_current_remote(remote):
    assert remote is not None, "no remote specified"
    ensure_remote(remote)

    with open(PROJECT_FILEPATH_REMOTE, "w") as file:
        file.write(remote)

def get_current_remote():
    assert os.path.exists(PROJECT_FILEPATH_REMOTE), "no remote"
    with open(PROJECT_FILEPATH_REMOTE, "r") as file:
        remote = file.readline()
    return remote

def get_remote_entries(remote):
    filepath = os.path.join(PROJECT_DIRECTORY_ENTRIES, remote)
    assert os.path.exists(filepath), "i guess fetch first"

    remote_entries = []
    with open(filepath, "r") as file:
        while line := file.readline():
            remote_entries.append(line.strip())

    return remote_entries

def populate_config() -> configparser.ConfigParser:
    c = configparser.ConfigParser()
    c = configparser.ConfigParser()
    c["core"] = {
        "version": version(__package__),
    }
    return c

def load_config():
    global config
    config = configparser.ConfigParser()
    assert os.path.exists(PROJECT_FILEPATH_CONFIG), "no config"
    config.read(PROJECT_FILEPATH_CONFIG)
    assert config["core"]["version"] == version(__package__), "version mismatch"

def save_config():
    os.makedirs(os.path.dirname(PROJECT_FILEPATH_CONFIG), exist_ok=True)
    with open(PROJECT_FILEPATH_CONFIG, "w") as configfile:
        config.write(configfile)


### init

def init():
    global config
    assert config is None

    assert not os.path.exists(PROJECT_FILEPATH_CONFIG), "already initialized"
    config = populate_config()

    save_config()

### clone

def clone(url, output=None, origin=None):
    dirname = output
    if output is None:
        dirname = sanitize_filename(shenanigans.get_remote_title(url))

    assert not os.path.exists(dirname)

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

def remote_list(verbose=False):
    load_config()

    for section in config.sections():
        if section.startswith("remote"):
            print(section.removeprefix("remote").strip().strip("\""), end="")
            if verbose:
                print("  " + config[section]["url"], end="")
            print()

    save_config()

def remote_add(name, url):
    assert name and url

    # FIXME: name validation

    load_config()

    section_name = f"remote \"{name}\""
    assert section_name not in config.sections(), "already exists"

    config[section_name] = {}

    save_config()

    remote_set_url(name, url)

def remote_set_url(name, newurl):
    assert name and newurl

    load_config()

    remote_data = ensure_remote(name)

    newurl = url_strip_share_identifier(newurl)
    newurl = url_strip_utm(newurl)
    remote_data["url"] = newurl

    save_config()

def remote_remove(name):
    assert name

    load_config()

    # TODO: rework for return of remote
    ensure_remote(name)
    section_name = f"remote \"{name}\""

    del config[section_name]

    save_config()

def remote_rename(old, new):
    assert old and new

    load_config()

    raise NotImplementedError

### fetch

def fetch(remote=None, all=False, set_upstream=False):
    load_config()

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

def merge(remote):
    load_config()

    directory = "."
    local_ids = set(shenanigans.get_local_ids(directory))
    remote_ids = set(get_remote_entries(remote))


    entries = remote_ids - local_ids
    entries_length = len(entries)
    i = 0
    try:
        for e in entries:
            bar_template = f"({i}/{entries_length}) '{e}' $prefix |$bar| $percent %"
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

            shenanigans.process_entry(e, output_directory=directory,
                                      progress_hook=progress_hook)

            i += 1
    except KeyboardInterrupt:
        print("stopped")

### pull

def pull(remote=None, set_upstream=False):
    load_config()

    if set_upstream:
        checkout(remote)

    if remote is None:
        remote = get_current_remote()

    fetch(remote=remote)
    merge(remote=remote)

### status

def status():
    load_config()

    remote_ids = get_remote_entries(get_current_remote())
    local_ids = shenanigans.get_local_ids(".")

    remote_ids_set = set(remote_ids)
    local_ids_set = set(local_ids)
    missing = remote_ids_set - local_ids_set
    leftovers = local_ids_set - remote_ids_set
    print("missing:")
    print("\n".join([f"    {i}" for i in missing]))
    print("leftovers:")
    print("\n".join([f"    {i}" for i in leftovers]))

    return

    duplicates_local = utils.find_duplicates(remote_ids)
    print("local duplicates:")
    print("\n".join([f"    {i}" for i in duplicates_local]))
    duplicates_remote = utils.find_duplicates(remote_ids)
    print("remote duplicates:")
    print("\n".join([f"    {i}" for i in duplicates_remote]))

### checkout

def checkout(remote):
    load_config()

    ensure_remote(remote)
    set_current_remote(remote)
