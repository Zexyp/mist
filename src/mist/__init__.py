# mist - another stupid content tracker

import os
import warnings
from dataclasses import dataclass
from pprint import pprint

_package_name = __package__
# entry can be just a remote snapshot
# or a local file description
# or be full of metadata
@dataclass
class Entry:
    id: str = None
    title: str = None
    url: str = None
    name: str = None
    tags: list[str] = None
    artist: str = None
    artist_name: str = None
    genre: str = None
    artist_links: list[tuple[str, str]] = None
    visited: set[str] = None

from . import files
from .config import ConfigReader, ConfigStack
from .errors import MistError
from . import log
from . import config
from .messages import *
from . import shenanigans, metadata
from .utils import url_strip_utm, url_strip_share_identifier, sanitize_filename
from .metadata import local as local_cache, worktree as worktree_cache

def _find_repository_dir(start: str, soft: bool = True) -> str | None:
    assert os.path.isabs(start)

    path = start
    while path not in ["", "/"]:
        candidate = os.path.join(path, files.DIR_REPOSITORY)
        if os.path.isdir(candidate):
            return candidate
        path = os.path.dirname(path)

    if soft:
        return None

    raise MistError(MSG_NOT_A_REPOSITORY)

def _sanitize_url(url: str) -> str:
    url = url_strip_share_identifier(url)
    url = url_strip_utm(url)
    return url

def _merge_entry(original: Entry, new: Entry, prune_tags: bool, ignore_tags: bool, is_fast: bool) -> Entry:
    assert original.id == new.id

    if not is_fast:
        original.name = new.name
        original.title = new.title
        original.genre = new.genre

    if not ignore_tags:
        if not prune_tags and set(original.tags or []).difference(set(new.tags or [])):
            raise MistError("tags would be removed")
        original.tags = new.tags

    if new.visited:
        if original.visited:
            original.visited.update(new.visited)
        else:
            original.visited = new.visited

    return original

@dataclass
class Remote:
    name: str = None
    url: str = None

class Mist:
    def __init__(self):
        self.working_dir: str = None
        self.repository_dir: str = None
        self.config: ConfigStack = ConfigStack()

    def set_working_dir(self, working_dir):
        assert os.path.isdir(working_dir)

        self.working_dir = working_dir
        self.config.load()

        log.configure(self.config.active)

        if found_repository := _find_repository_dir(working_dir):
            log.debug(f"found repository dir '{found_repository}'")
            self.set_repository_dir(found_repository)

        log.debug(f"working dir '{self.working_dir}'")

    def set_repository_dir(self, repository_dir):
        assert os.path.isdir(repository_dir)

        self.repository_dir = repository_dir
        self._assert_repository()

        # only set if in repo
        self.config.file_set(
            repository_dir=self.repository_dir,
            working_dir=self.working_dir,
        )
        self.config.load()

        log.configure(self.config.active)

        from importlib.metadata import version
        if self.config.local.get("core.version") != version(_package_name):
            log.warning("repository was created using a different Mist version")

        log.debug(f"repository dir '{self.repository_dir}'")

    def is_repository(self):
        return self.repository_dir is not None and os.path.isdir(self.repository_dir) and os.path.basename(self.repository_dir) == files.DIR_REPOSITORY

    def init(self, directory: str) -> str:
        if self.is_repository():
            raise NotImplementedError("repository reinitialization")

        target_dir = os.path.join(os.path.abspath(directory), files.DIR_REPOSITORY)
        os.makedirs(target_dir)
        self.repository_dir = target_dir

        self.config.file_set(repository_dir=self.repository_dir)

        # write cfg
        from importlib.metadata import version
        self.config.local.set("core.version", version(_package_name))
        self.config.local.save()

        return target_dir

    def _get_cache_file(self, remote_name: str, cache_type: str) -> str:
        result = os.path.join(self.repository_dir, files.DIR_REPOSITORY_CACHE, remote_name, cache_type)
        os.makedirs(os.path.dirname(result), exist_ok=True)
        return result

    def fetch(self, remote: str, tags: bool = False,
              dry_run: bool = False,
              force: bool = False,
              prune: bool = False,
              prune_tags: bool = False,
              progress: Callable[[str], None] = None) -> list[Entry]:
        """returns a list of locally available entries"""
        self._assert_remote(remote)

        log.debug(f"fetch {force=}, {prune=}, {prune_tags=}")

        section_name = self._remote_section_name(remote)

        list_url = self.config.local.get(f"{section_name}.url")
        if tags:
            items = shenanigans.get_entries(list_url,
                                            progress=progress,
                                            max_concurrency=self._get_concurrency())
        else:
            items = shenanigans.get_entries_fast(list_url,
                                                 progress=progress)

        loaded = not prune and self.get_remote_entries(remote) or []

        merged = []
        if loaded:
            for existing in loaded:
                new_for_merging = [i for i in items if i.id == existing.id]
                if new_for_merging:
                    new = new_for_merging[0]
                    items.remove(new)
                    # forcing uses the whole new item
                    merged.append(new if force else _merge_entry(existing, new, prune_tags=prune_tags, ignore_tags=not tags, is_fast=not tags))
                else:
                    merged.append(existing)

        merged[:0] = items # prepend existing so they might get overwritten if duplicates occurred
        loaded = merged

        if not dry_run:
            entries_file = self._get_cache_file(remote, files.CACHE_TYPE_ENTRIES)
            local_cache.local_save(entries_file, loaded)

        return loaded

    def get_remote_entries(self, remote: str) -> list[Entry] | None:
        self._assert_remote(remote)

        entries_file = self._get_cache_file(remote, files.CACHE_TYPE_ENTRIES)
        if not os.path.exists(entries_file):
            return None
        return local_cache.local_load(entries_file)

    def list_remote(self, remote_url: str) -> list[Entry]:
        entries = shenanigans.get_entries_fast(_sanitize_url(remote_url),
                                               progress=lambda m: log.debug(m))
        return entries

    def merge(self, remote: str, progress: Callable = None) -> list[Entry]:
        if progress:
            raise NotImplementedError("merge progress reporting not implemented")

        entries = self.get_remote_entries(remote)
        source = metadata.detect_source(self.get_remote(remote).url)

        worktree_items = worktree_cache.worktree_load(self.working_dir)
        missing_ids = set([e.id for e in entries]).difference(set([e.id for e in worktree_items]))

        entries_to_download = [e for e in entries if e.id in missing_ids]
        if entries_to_download:
            shenanigans.download_entries(source, entries_to_download,
                                         destination_dir=self.working_dir,
                                         max_concurrency=self._get_concurrency())
        return entries_to_download


    def clone(self, url: str, destination_dir: str = None, origin: str = None, tags: bool = False):
        url = _sanitize_url(url)
        destination_dir = destination_dir or sanitize_filename(shenanigans.get_playlist_title(url))

        self.init(destination_dir)
        self.set_working_dir(os.path.abspath(destination_dir))
        remote = origin or self.config.active.get("clone.defaultRemoteName", "origin")
        self.remote_add(remote, url)
        self.fetch(remote, tags=tags)
        self.merge(remote)

    def get_remotes(self) -> list[Remote]:
        self._assert_repository()

        keys = self.config.local.keys("remote.")
        return [self.get_remote(k) for k in keys]

    def get_remote(self, name) -> Remote | None:
        self._assert_repository()

        section_name = self._remote_section_name(name)

        if not self.config.local.has(f"{section_name}.", sub=True):
            return None

        remote = Remote()
        remote.name = name
        remote.url = self.config.local.get(f"{section_name}.url")

        return remote

    @staticmethod
    def _remote_section_name(mame: str) -> str:
        return f"remote.{mame}"

    def _assert_repository(self):
        if not self.is_repository():
            raise MistError(MSG_NOT_A_REPOSITORY)

    # now operates on local config only, which make sense ig
    def _assert_remote(self, name: str):
        self._assert_repository()

        if name is None:
            raise MistError(MSG_NO_REMOTE)

        section_name = self._remote_section_name(name)
        if not self.config.local.has(f"{section_name}.", sub=True):
            raise MistError(MSG_NO_SUCH_REMOTE.format(name=name))

    def remote_add(self, name: str, url: str):
        url = _sanitize_url(url)

        section_name = self._remote_section_name(name)

        if self.config.local.has(f"{section_name}.", sub=True):
            raise MistError(MSG_REMOTE_ALREADY_EXISTS.format(name=name))

        self.config.local.set(f"{section_name}.url", url)
        self.config.local.save()

    def remote_remove(self, name: str):
        self._assert_remote(name)

        section_name = self._remote_section_name(name)

        self.config.local.unset(f"{section_name}.", sub=True)
        self.config.local.save()

    def remote_rename(self, old_name: str, new_name: str):
        self._assert_remote(old_name)
        # TODO: assert new name

        raise NotImplementedError

    def remote_get_url(self, name: str) -> str:
        self._assert_remote(name)

        section_name = self._remote_section_name(name)

        return self.config.local.get(f"{section_name}.url")

    def remote_set_url(self, name: str, new_url: str):
        self._assert_remote(name)

        new_url = _sanitize_url(new_url)

        section_name = self._remote_section_name(name)

        self.config.local.set(f"{section_name}.url", new_url)
        self.config.local.save()

    def _get_active_remote_storage_file(self) -> str:
        self._assert_repository()

        return os.path.join(self.repository_dir, files.FILE_REPOSITORY_REMOTE)

    def active_remote_name_get(self) -> str | None:
        self._assert_repository()

        file = self._get_active_remote_storage_file()
        if not os.path.isfile(file):
            return None
        with open(file, mode="r") as f:
            return f.readline().strip()

    def active_remote_name_set(self, name: str):
        self._assert_remote(name)

        with open(self._get_active_remote_storage_file(), mode="w") as f:
            f.write(f"{name}\n")

    def _get_concurrency(self) -> int:
        return self.config.local.getint("core.concurrency", os.cpu_count())