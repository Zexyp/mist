from ..core import *
from ..utils import *
from .. import command_print_call, core

@command_print_call
def remote_list(verbose=False):
    load_project_config()

    for r in get_remotes():
        r_url = core.remote.ensure(r)["url"]
        print(r, end="")
        if verbose:
            print("  " + r_url, end="")
        print()

    save_project_config()

@command_print_call
def remote_add(name, url):
    assert name and url

    # FIXME: validation

    load_project_config()

    core.remote.add(name)

    save_project_config()

    remote_set_url(name, url)

@command_print_call
def remote_set_url(name, newurl):
    assert name and newurl

    load_project_config()

    remote_data = core.remote.ensure(name)

    newurl = url_strip_share_identifier(newurl)
    newurl = url_strip_utm(newurl)
    remote_data["url"] = newurl

    save_project_config()

def remote_remove(name):
    assert name

    load_project_config()

    core.remote.delete(name)

    save_project_config()