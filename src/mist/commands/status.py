import os
from typing import Iterable, Callable

from .. import command_print_call, utils, shenanigans, core, metadata

# FIXME: performance and clean code
@command_print_call
def status():
    core.load_project_config()

    current_remote = core.remote.get_current()
    pltf = metadata.detect_platform(core.remote.ensure(current_remote)["url"])
    metadata_cache_dir = core.remote.get_cache_path(current_remote)
    metadata.load_cache(metadata_cache_dir)

    local_ids = metadata.local.get_entries(".")

    # remove other remote entries
    for r in core.get_remotes():
        if r == current_remote:
            continue
        for i in core.remote.get_entries(r):
            if i not in local_ids:
                continue
            local_ids.remove(i)

    remote_ids = core.remote.get_entries(current_remote)

    error_ids_set = set(core.remote.get_errors(current_remote) or [])
    local_ids_set = set(local_ids)
    remote_ids_set = set(remote_ids)
    duplicates_remote = utils.find_duplicates(remote_ids)
    duplicates_local = utils.find_duplicates(local_ids)

    common_ids_set = local_ids_set & remote_ids_set
    renamed = []
    empty = []
    # compare names
    for i in common_ids_set:
        if i in duplicates_local:
            continue
        if (name_remote := metadata.get_full_title(pltf, i)) != (name_local := metadata.local.get_entry_title(".", i)):
            renamed.append((i, name_remote, name_local))
        if not os.path.getsize(metadata.local.get_entry_file(".", i)):
            empty.append(i)

    missing = remote_ids_set - local_ids_set - error_ids_set
    leftovers = local_ids_set - remote_ids_set

    metadata.save_cache(metadata_cache_dir)
    metadata.load_cache(metadata_cache_dir)

    print(f"remote: {current_remote}")
    if duplicates_remote: print("\n".join([f"    duplicate: {i}" for i in duplicates_remote])); print()
    if error_ids_set:     print("\n".join([f"    failed:    {i}" for i in error_ids_set if i])); print()
    if renamed:           print("\n".join([f"    misnomer:  {i[0]} '{i[1]}' -> '{i[2]}'" for i in renamed if i])); print()
    if missing:           print("\n".join([f"    added:     {i} '{metadata.get_full_title(pltf, i)}'" for i in missing if i])); print()
    print()

    print("local:")
    if duplicates_local:  print("\n".join([f"    duplicate: {i}" for i in duplicates_local])); print()
    if leftovers:         print("\n".join([f"    leftover:  {i} '{metadata.local.get_entry_title(".", i)}'" for i in leftovers if i])); print()
    if empty:             print("\n".join([f"    empty:     {i} '{metadata.local.get_entry_title(".", i)}'" for i in empty if i])); print()
    print()

    metadata.save_cache(metadata_cache_dir)