from ..errors import *
from . import *

_remote_section_template = "remote \"{name}\""

def ensure(remote):
    section_name = _remote_section_template.format(name=remote)
    if not section_name in project_config.sections():
        raise RemoteNotFoundError(f"no such remote '{remote}'")
    return project_config[section_name]

def delete(remote):
    # cleanup
    if remote == get_current():
        set_current("")

    section_name = _remote_section_template.format(name=remote)
    if not section_name in project_config.sections():
        raise RemoteNotFoundError(f"no such remote '{remote}'")
    del project_config[section_name]

def add(remote):
    section_name = _remote_section_template.format(name=remote)
    if section_name in project_config.sections():
        raise RemoteExistsError("already exists")
    project_config[section_name] = {}

def get_cache_path(remote, type=None):
    if type:
        path = os.path.join(PROJECT_DIRECTORY_CACHE, remote, type)
    else:
        path = os.path.join(PROJECT_DIRECTORY_CACHE, remote)
    return path

def set_current(remote):
    assert remote is not None, "no remote specified"

    if remote != "":
        ensure(remote)

    with open(PROJECT_FILEPATH_REMOTE, "w") as file:
        file.write(remote)

def get_current() -> str:
    if not os.path.exists(PROJECT_FILEPATH_REMOTE):
        raise RemoteNotFoundError(f"no remote")

    with open(PROJECT_FILEPATH_REMOTE, "r") as file:
        remote = file.readline()

    ensure(remote)
    return remote

def get_entries(remote) -> list[str]:
    ensure(remote)

    filepath = get_cache_path(remote, CACHE_TYPE_ENTRIES)
    if not os.path.exists(filepath):
        raise NoDataFileError("no entries data")

    remote_entries = []
    with open(filepath, "r") as file:
        while line := file.readline():
            remote_entries.append(line.strip())

    return remote_entries

def get_errors(remote) -> list[str]:
    ensure(remote)

    errors = None
    error_cache_file = get_cache_path(remote, CACHE_TYPE_ERRORS)
    if os.path.exists(error_cache_file):
        errors = []
        with open(error_cache_file, "r") as file:
            while line := file.readline():
                errors.append(line.strip())

    return errors