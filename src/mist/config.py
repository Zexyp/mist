import configparser
import os
import pathlib
from typing import Callable

from . import files, log

# todo: from collections import OrderedDict

"""not so simple after all"""
class SimpleConfig:
    def __init__(self, settings: dict[str, str] = None, path: str = None,
                 on_commit: Callable[['SimpleConfig'], None] = None):
        if settings is None:
            settings = {}

        self.settings = settings
        self.path = path
        self._on_commit = on_commit

    def has(self, key: str) -> bool:
        return key in self.settings

    # fixme: i'm crying
    def get(self, key: str, default) -> str:
        return self.settings.get(key, default)

    def getbool(self, key: str, default) -> bool:
        match self.settings.get(key, "1" if default else "0"):
            case "true" | "on" | "yes" | "1":
                return True
            case "false" | "off" | "no" | "0":
                return False
            case _:
                raise ValueError("Invalid setting value")

    def getint(self, key: str, default) -> int:
        return int(self.settings.get(key, str(default)))

    def set(self, key: str, value):
        self.settings[key] = str(value)

    def unset(self, key: str):
        del self.settings[key]

    def overlay(self, reader: 'SimpleConfig'):
        if reader is None:
            return
        self.settings.update(reader.settings)

    def clear(self):
        self.settings.clear()

    def save(self):
        if not self.path:
            raise FileNotFoundError("path is unusable")

        with open(self.path, "w") as file:
            _convert_to_ini(self.settings).write(file)

        log.debug(f"config write '{self.path}'")

        self.commit()

    def load(self):
        if not self.path:
            raise FileNotFoundError("path is unusable")

        self.settings = _read_ini(self.path)

        log.debug(f"config read '{self.path}'")

        self.commit()

    def commit(self):
        if self._on_commit:
            self._on_commit(self)

class ConfigStack:
    def __init__(self):
        self.general: SimpleConfig = self._create_config(os.path.join(str(pathlib.Path.home()), ".mistconfig"))
        self.local: SimpleConfig = self._create_config(None)
        self.args: SimpleConfig = self._create_config(None)
        self.active: SimpleConfig = self._create_config(None)

    def apply(self):
        self.active.clear()
        self.active.overlay(self.general)
        self.active.overlay(self.local)
        self.active.overlay(self.args)

    def file_set(self, repository_dir=None, working_dir=None):
        if repository_dir is not None:
            self.local.path = os.path.join(repository_dir, files.FILE_REPOSITORY_CONFIG)
        else:
            self.local.path = None

    def load(self):
        self.general.clear()
        if self.general.path and os.path.isfile(self.general.path):
            self.general.load()
        self.local.clear()
        if self.local.path and os.path.isfile(self.local.path):
            self.local.load()
        self.apply()

    def _create_config(self, path) -> SimpleConfig:
        return SimpleConfig({}, path, on_commit=lambda _: self.apply())


def _read_ini(path: str) -> dict[str, str]:
    assert os.path.isfile(path)

    parser = configparser.ConfigParser()
    parser.read(path)
    d = {}
    for section in parser.sections():
        section_path = ".".join([p.strip("\"") for p in section.split(" ")])

        for key, value in parser.items(section):
            d[f"{section_path}.{key}"] = value

    return d

def _convert_to_ini(d: dict[str, str]) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    for k, v in d.items():
        key_parts = k.split(".", 1)
        section = key_parts[0]
        key = key_parts[1]

        if "." in key:
            tail_parts = key.rsplit(".", 1)
            section = f"{section} \"{tail_parts[0]}\""
            key = tail_parts[1]

        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, key, v)
    return parser
