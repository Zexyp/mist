import os
from typing import Iterable

from . import Entry, files, metadata, MistError, DistinguishedId
from .metadata import local as local_cache

class Storage:
    def init(self, repodir):
        self.repository_dir: str = repodir

    def introduce_remote(self, remote_name: str, entries: list[Entry], prune: bool = False):
        raise Exception("wtf")

    def introduce_tags(self, entries: list[Entry], prune: bool = False):
        raise Exception("wtf")

    def save_remote_entries_direct(self, source: metadata.Source, remote_name: str, entries: list[Entry]) -> None:
        """
        direct since we do not merge here
        """

        dir_refs = os.path.join(self.repository_dir, files.DIR_REFS_REMOTES)
        dir_objects = os.path.join(self.repository_dir, files.DIR_OBJECTS, source.name)

        os.makedirs(dir_refs, exist_ok=True)
        os.makedirs(dir_objects, exist_ok=True)

        for e in entries:
            object_path = os.path.join(dir_objects, e.id)
            local_cache._write_entry(object_path, e)

        self._write_refs(os.path.join(dir_refs, remote_name), (e.id for e in entries))

    def get_remote_ids(self, remote_name: str) -> list[str] | None:
        dir_refs = os.path.join(self.repository_dir, files.DIR_REFS_REMOTES)

        if not os.path.isfile(refs_path := os.path.join(dir_refs, remote_name)):
            return None

        ids = self._read_refs(refs_path)

        return ids

    def get_remote_entries(self, source: metadata.Source, remote_name: str) -> list[Entry] | None:
        ids = self.get_remote_ids(remote_name)
        if ids is None: return None

        output = []
        for ident in ids:
            output.append(self.get_object(source, ident))
        return output

    def get_object(self, source: metadata.Source, ident: str) -> Entry:
        object_path = os.path.join(self.repository_dir, files.DIR_OBJECTS, source.name, ident)
        if not os.path.isfile(object_path):
            raise MistError("cache broken")
        return local_cache._read_entry(object_path)

    def _read_refs(self, file: str) -> list[str]:
        with open(file, mode="r") as f:
            items = [stripped for l in f.readlines() if (stripped := l.strip())]
        return items

    def _write_refs(self, file: str, items: Iterable[str]):
        with open(file, "w") as f:
            for i in items:
                f.write(f"{i}\n")
