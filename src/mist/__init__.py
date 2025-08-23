import configparser
import os

FILEPATH_CONFIG = ".mist"
FILEPATH_IGNORE = ".mistignore"

config: configparser.ConfigParser | None = None

def populate_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config = configparser.ConfigParser()
    from importlib.metadata import version
    config["core"] = {
        "version": version(__package__),
    }
    return config

def load():
    global config
    config = configparser.ConfigParser()
    config.read(FILEPATH_CONFIG)

def must_load():
    load()
    assert config, "no config"

def save_config():
    with open(FILEPATH_CONFIG, "w") as file:
        config.write(file)

### init

def init():
    global config
    assert config is None

    assert not os.path.exists(FILEPATH_CONFIG), "already initialized"
    config = populate_config()

    save_config()

### remote

def remote_list(verbose = False):
    must_load()

    for section in config.sections():
        if section.startswith("remote"):
            print(section.removeprefix("remote").strip().strip("\""), end="")
            if verbose:
                print("  " + config[section]["url"], end="")
            print()

    save_config()

def remote_add(name, url):
    assert name and url

    must_load()

    config[f"remote \"{name}\""] = {
        "url": url,
    }

    save_config()

def remote_remove(name):
    assert name

    must_load()

    section_name = f"remote \"{name}\""
    assert section_name in config, "no such remote"
    del config[section_name]

    save_config()

def pull():
    must_load()

    raise NotImplementedError
