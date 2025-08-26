from ..core import *
from .. import command_print_call

DEFAULT_KIND = "local"

def _split_key(key) -> (str, str):
    parts = key.split(".", 1)
    section = parts[0]
    option = parts[1]
    return section, option


def _config_set(kind, key, value):
    section, option = _split_key(key)
    _config_write(kind, section, option, value)

def _config_unset(kind, key):
    section, option = _split_key(key)
    _config_remove(kind, section, option)

def _config_get(kind, key):
    active_conf = _config_get_active(kind)
    section, option = _split_key(key)
    if value := active_conf.get(section, option, fallback=None) is not None:
        print(value)


def _config_edit(kind):
    if (editor := configuration.get("core", "editor", fallback=None)) is None:
        print("no editor configured")
        return

    file = _config_edit_path(kind)

    import subprocess
    subprocess.call([editor, file])


def _config_list(kind):
    active_conf = _config_get_active(kind)

    for section in active_conf.sections():
        for key, value in active_conf[section].items():
            # handling of remote section names
            absolute_cinema = "\""
            print(f"{'.'.join([v.strip(absolute_cinema) for v in section.split(' ')])}.{key}={value}")


def _config_get_active(kind):
    match kind:
        case "local":
            load_project_config()
            active_conf = project_config
        case "global":
            active_conf = global_config

        # debug thingy
        case "forced":
            active_conf = forced_config

        # fallback, default all
        case None:
            active_conf = configuration

        case _:
            assert False, "unknown config kind"

    return active_conf


def _config_write(kind, section, option, value):
    match kind or DEFAULT_KIND:
        case "local":
            load_project_config()
            config_safe_set(project_config, section, option, value)
            save_project_config()
        case "global":
            config_safe_set(global_config, section, option, value)
            save_global_config()
        case _:
            assert False, "unknown config kind"

def _config_remove(kind, section, option):
    def remove(conf):
        conf.remove_option(section, option)
        # cleanup
        if len(conf[section]) == 0:
            conf.remove_section(section)

    match kind or DEFAULT_KIND:
        case "local":
            load_project_config()
            remove(project_config)
            save_project_config()
        case "global":
            remove(global_config)
            save_global_config()
        case _:
            assert False, "unknown config kind"


def _config_edit_path(kind):
    match kind or DEFAULT_KIND:
        case "local":
            file = PROJECT_FILEPATH_CONFIG
        case "global":
            file = FILEPATH_GLOBAL_CONFIG
        case _:
            assert False, "unknown config kind"

    return file

@command_print_call
def config(key, value=None, list=None, edit=None, kind=None, unset=False):
    if not sum([bool(key), list, edit]) == 1:
        raise ArgumentError("invalid args")

    if not key:
        if unset:
            raise ArgumentError("now what")

    if is_project():
        load_project_config()

    if list:
        _config_list(kind)
        return
    if edit:
        _config_edit(kind)
        return
    if unset:
        assert not value, "am i supposed to check the value to unset?"
        _config_unset(kind, key)
        return

    if not value:
        _config_get(kind, key)
        return

    _config_set(kind, key, value)