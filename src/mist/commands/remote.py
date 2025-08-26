from ..core import *
from ..utils import *
from .. import debug_print_call

@debug_print_call
def remote_list(verbose=False):
    load_project_config()

    for section in project_config.sections():
        if section.startswith("remote"):
            print(section.removeprefix("remote").strip().strip("\""), end="")
            if verbose:
                print("  " + project_config[section]["url"], end="")
            print()

    save_project_config()

@debug_print_call
def remote_add(name, url):
    assert name and url

    # FIXME: validation

    load_project_config()

    add_remote(name)

    save_project_config()

    remote_set_url(name, url)

@debug_print_call
def remote_set_url(name, newurl):
    assert name and newurl

    load_project_config()

    remote_data = ensure_remote(name)

    newurl = url_strip_share_identifier(newurl)
    newurl = url_strip_utm(newurl)
    remote_data["url"] = newurl

    save_project_config()

def remote_remove(name):
    assert name

    load_project_config()

    del_remote(name)

    save_project_config()