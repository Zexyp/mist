import os
import configparser
import sys
from functools import cache
from importlib.metadata import version
from pathlib import Path

from .errors import *
from . import log
from .log import log_debug, log_verbose

PROJECT_DIRECTORY = ".mist"
PROJECT_FILEPATH_CONFIG = PROJECT_DIRECTORY + "/config"
PROJECT_FILEPATH_REMOTE = PROJECT_DIRECTORY + "/remote"
PROJECT_DIRECTORY_CACHE = PROJECT_DIRECTORY + "/cache"
# TODO: submodules will allow for directory structure
# TODO: bracketeer
# TODO: genres
# TODO: extended mix, vip check
# TODO: mistconfig sound (on/off) and color (auto/off/force)

FILENAME_IGNORE = ".mistignore"
FILENAME_CONFIG = ".mistconfig"
FILENAME_MODULES = ".mistmodules"

FILEPATH_GLOBAL_CONFIG = os.path.join(Path.home(), FILENAME_CONFIG)

DEFAULT_ORIGIN_NAME = "origin"

CACHE_TYPE_TITLES = "titles"
CACHE_TYPE_ENTRIES = "entries"
CACHE_TYPE_ERRORS = "errors"

_remote_section_template = "remote \"{name}\""

project_config: configparser.ConfigParser = configparser.ConfigParser()
global_config: configparser.ConfigParser = configparser.ConfigParser()
configuration: configparser.ConfigParser = configparser.ConfigParser()
forced_config: configparser.ConfigParser = configparser.ConfigParser()

def ensure_remote(remote):
    section_name = _remote_section_template.format(name=remote)
    if not section_name in project_config.sections():
        raise RemoteNotFoundError(f"no such remote '{remote}'")
    return project_config[section_name]

def del_remote(remote):
    section_name = _remote_section_template.format(name=remote)
    if not section_name in project_config.sections():
        raise RemoteNotFoundError(f"no such remote '{remote}'")
    del project_config[section_name]

def add_remote(remote):
    section_name = _remote_section_template.format(name=remote)
    if section_name in project_config.sections():
        raise RemoteExistsError("already exists")
    project_config[section_name] = {}

def get_cache_path_for_remote(remote, type):
    path = os.path.join(PROJECT_DIRECTORY_CACHE, remote, type)
    return path

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
    ensure_remote(remote)

    filepath = get_cache_path_for_remote(remote, CACHE_TYPE_ENTRIES)
    if not os.path.exists(filepath):
        raise NoDataFileError("no entries data")

    remote_entries = []
    with open(filepath, "r") as file:
        while line := file.readline():
            remote_entries.append(line.strip())

    return remote_entries

def get_remote_errors(remote):
    ensure_remote(remote)

    errors = None
    error_cache_file = get_cache_path_for_remote(remote, CACHE_TYPE_ERRORS)
    if os.path.exists(error_cache_file):
        errors = []
        with open(error_cache_file, "r") as file:
            while line := file.readline():
                errors.append(line.strip())

    return errors

def project_config_template(conf: configparser.ConfigParser):
    conf["core"] = {}

def is_project() -> bool:
    return os.path.exists(PROJECT_FILEPATH_CONFIG)

def load_project_config():
    if not is_project():
        raise InitializationError("not a mist repository")

    log_verbose("reading local config")
    project_config.read(PROJECT_FILEPATH_CONFIG)

    apply_configuration()

def load_global_config():
    log_verbose("reading global config")
    global_config.read(FILEPATH_GLOBAL_CONFIG)

    apply_configuration()

def save_project_config():
    proj_dir = os.path.dirname(PROJECT_FILEPATH_CONFIG)
    os.makedirs(proj_dir, exist_ok=True)
    log_debug(f"project dir '{os.path.abspath(proj_dir)}'")
    log_verbose("writing local config")
    with open(PROJECT_FILEPATH_CONFIG, "w") as configfile:
        project_config.write(configfile)

def save_global_config():
    log_debug(f"global config at '{FILEPATH_GLOBAL_CONFIG}'")
    log_verbose("writing global config")
    with open(FILEPATH_GLOBAL_CONFIG, "w") as configfile:
        global_config.write(configfile)

def initialize():
    if os.path.exists(FILEPATH_GLOBAL_CONFIG):
        load_global_config()
    else:
        log_verbose(f"no global config to load")

def config_safe_set(conf: configparser.ConfigParser, section: str, option: str, value):
    if not conf.has_section(section):
        conf.add_section(section)
    conf.set(section, option, value)

def configure(debug: bool = None,
              verbose: bool = None,
              color: str = None,
              sound: bool = None):

    if color is not None: config_safe_set(forced_config, "core", "color", color)
    if verbose is not None: config_safe_set(forced_config, "core", "verbose", str(verbose))
    if debug is not None: config_safe_set(forced_config, "core", "debug", str(debug))
    if sound is not None: config_safe_set(forced_config, "core", "sound", str(sound))

def config_overlay(overlay: configparser.ConfigParser, on: configparser.ConfigParser):
    for section in overlay.sections():
        for key, value in overlay[section].items():
            config_safe_set(on, section, key, value)

def apply_configuration():
    config_overlay(global_config, configuration)
    config_overlay(project_config, configuration)
    config_overlay(forced_config, configuration)

    try:
        if value := configuration.getboolean("core", "debug", fallback=None) is not None: log._debug = value
        if value := configuration.getboolean("core", "sound", fallback=None) is not None: log._sound = value
        if value := configuration.getboolean("core", "verbose", fallback=None) is not None: log._verbose = value
        match value := configuration.get("core", "color", fallback=None):
            case "auto":
                if not (not sys.stdout.isatty() or ("NO_COLOR" in os.environ and os.environ["NO_COLOR"] != "\0")):
                    log.init_colors()
                else:
                    log.deinit_colors()
            case "force":
                log.init_colors()
            case "off":
                log.deinit_colors()
            case None:
                pass
            case _:
                # TODO: message
                raise ValueError
    except ValueError:
        raise ConfigurationError("invalid configuration")

# configuration translation functions
def _configurator_forced():
    pass

def _configurator_environment():
    pass

def _configurator_local():
    pass

def _configurator_global():
    pass