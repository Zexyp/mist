import configparser
import os

from . import shenanigans
from .errors import RemoteNotFoundError
from .utils import url_strip_utm, url_strip_share_identifier

PROJECT_DIRECTORY = ".mist"
FILEPATH_PROJECT_CONFIG = PROJECT_DIRECTORY + "/config"
FILEPATH_PROJECT_REMOTE = PROJECT_DIRECTORY + "/remote"
FILEPATH_PROJECT_ENTRIES = PROJECT_DIRECTORY + "/entries"

FILENAME_IGNORE = ".mistignore"
FILENAME_CONFIG = ".mistconfig"

config: configparser.ConfigParser | None = None

def ensure_remote(remote):
    section_name = f"remote \"{remote}\""
    if not section_name in config.sections():
        raise RemoteNotFoundError(f"no such remote '{remote}'")
    return config[section_name]

def set_remote_as_upstream(remote):
    assert remote is not None, "no remote specified"
    ensure_remote(remote)

    with open(FILEPATH_PROJECT_REMOTE, "w") as file:
        file.write(remote)

def populate_config() -> configparser.ConfigParser:
    c = configparser.ConfigParser()
    c = configparser.ConfigParser()
    from importlib.metadata import version
    c["core"] = {
        "version": version(__package__),
    }
    return c

def load_config():
    global config
    config = configparser.ConfigParser()
    assert os.path.exists(FILEPATH_PROJECT_CONFIG), "no config"
    config.read(FILEPATH_PROJECT_CONFIG)

def save_config():
    os.makedirs(os.path.dirname(FILEPATH_PROJECT_CONFIG), exist_ok=True)
    with open(FILEPATH_PROJECT_CONFIG, "w") as configfile:
        config.write(configfile)

### init

def init():
    global config
    assert config is None

    assert not os.path.exists(FILEPATH_PROJECT_CONFIG), "already initialized"
    config = populate_config()

    save_config()

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

### fetch

def fetch(remote=None, all=False, set_upstream=False):
    load_config()

    if set_upstream:
        set_remote_as_upstream(remote)

    if remote is None:
        assert os.path.exists(FILEPATH_PROJECT_REMOTE), "no upstream remote"
        with open(FILEPATH_PROJECT_REMOTE, "r") as file:
            remote = file.readline()

    remote_data = ensure_remote(remote)

    with open(FILEPATH_PROJECT_ENTRIES, "w") as file:
        remote_ids = shenanigans.get_remote_ids(remote_data["url"])
        file.write("\n".join(remote_ids))

### merge

def merge():
    load_config()



    raise NotImplementedError

### pull

def pull(remote=None, all=False, set_upstream=False):
    fetch(remote=remote, all=all, set_upstream=set_upstream)

    load_config()

    raise NotImplementedError

### clone

def clone(url, output=None, origin="origin"):
    # fetch data
    # create directory
    # create config
    # create remote
    # begin download
    raise NotImplementedError

def status():
    load_config()

    assert os.path.exists(FILEPATH_PROJECT_ENTRIES)

    remote_ids = []
    with open(FILEPATH_PROJECT_ENTRIES, "r") as file:
        while line := file.readline():
            remote_ids.append(line.strip())
    local_ids = shenanigans.get_local_ids(".")

    remote_ids_set = set(remote_ids)
    local_ids_set = set(local_ids)
    missing = remote_ids_set - local_ids_set
    leftovers = local_ids_set - remote_ids_set
    print("missing:")
    print("\n".join([f"    {i}" for i in missing]))
    print("leftovers:")
    print("\n".join([f"    {i}" for i in leftovers]))
