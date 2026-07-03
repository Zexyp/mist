import os
import warnings
from dataclasses import dataclass

from . import files
from .config import ConfigReader, ConfigStack
from .errors import MistError
from . import log
from . import config
from .messages import *
from . import shenanigans
from .shenanigans import Entry
from .utils import url_strip_utm, url_strip_share_identifier

# mist - another stupid content tracker

_package_name = __package__

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

        log.debug(f"repository dir '{self.repository_dir}'")

    def is_repository(self):
        return self.repository_dir is not None and os.path.isdir(self.repository_dir) and os.path.basename(self.repository_dir) == files.DIR_REPOSITORY

    def init(self, directory: str) -> str:
        if self.is_repository():
            raise NotImplementedError

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

    def fetch(self, remote: str, tags: bool = False, progress: Callable[[str], None] = None):
        self._assert_remote(remote)

        section_name = self._remote_section_name(remote)

        warnings.warn("tags enable disable not implemented")

        items = shenanigans.get_entries(self.config.local.get(f"{section_name}.url"),
                                        progress=progress,
                                        max_concurrency=self.config.local.getint("core.concurrency", os.cpu_count()))

        from .metadata import local
        local.save(self._get_cache_file(remote, files.CACHE_TYPE_ENTRIES), items)

    def list_remote(self, remote_url: str) -> list[Entry]:
        entries = shenanigans.get_entries_fast(_sanitize_url(remote_url),
                                               progress=lambda m: log.debug(m))
        return entries

    def merge(self, remote: str, progress: Callable[[str], None] = None):
        raise NotImplementedError

    def clone(self, url: str, destination_dir: str = None, origin: str = None):
        url = _sanitize_url(url)
        raise NotImplementedError

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
