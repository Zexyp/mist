import os
from . import files
from .config import SimpleConfig, ConfigStack
from .errors import MistError
from . import log
from . import config

_package_name = __package__

def _find_repository_dir(start: str, soft: bool = True) -> str | None:
    """start should be abs"""
    path = start

    while path not in ["", "/"]:
        candidate = os.path.join(path, files.DIR_REPOSITORY)
        if os.path.isdir(candidate):
            return candidate
        path = os.path.dirname(path)

    if soft:
        return None

    raise MistError(f"not a mist repository (or any of the parent directories): {files.DIR_REPOSITORY}")

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
        if not self.is_repository():
            raise MistError(f"not a mist repository (or any of the parent directories): .mist")

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
        target_dir = os.path.join(os.path.abspath(directory), files.DIR_REPOSITORY)
        os.makedirs(target_dir)
        self.repository_dir = target_dir

        self.config.file_set(repository_dir=self.repository_dir)

        # write cfg
        from importlib.metadata import version
        self.config.local.set("core.version", version(_package_name))
        self.config.local.save()

        return target_dir

    # now operates on local config
    def _assert_remote(self, name: str):
        section_name = f"remote.{name}"
        if not self.config.local.has(f"{section_name}.url"):
            raise MistError(f"No such remote '{name}'")

    def remotes_list(self) -> list[str]:
        ls = set()
        for key in self.config.local.settings:
            if key.startswith("remote."):
                name = key.removeprefix("remote.").split(".", 1)[0]
                ls.add(name)
        return list(ls)

    def remote_add(self, name: str, url: str):
        section_name = f"remote.{name}"

        if self.config.local.has(f"{section_name}.url"):
            raise MistError(f"remote {name} already exists.")

        self.config.local.set(f"{section_name}.url", url)
        self.config.local.save()

    def remote_remove(self, name: str):
        self._assert_remote(name)

        raise NotImplementedError

    def remote_rename(self, old_name: str, new_name: str):
        self._assert_remote(old_name)

        raise NotImplementedError

    def remote_get_url(self, name: str) -> str:
        self._assert_remote(name)

        section_name = f"remote.{name}"

        return self.config.local.get(f"{section_name}.url")

    def remote_set_url(self, name: str, new_url: str):
        self._assert_remote(name)

        section_name = f"remote.{name}"

        self.config.local.set(f"{section_name}.url", new_url)
        self.config.local.save()
