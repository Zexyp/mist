import configparser
import os
import pathlib
from typing import Callable

from . import files, log

# todo: from collections import OrderedDict

"""not so reader after all"""
class ConfigReader:
    def __init__(self, settings: dict[str, str] = None, path: str = None,
                 on_commit: Callable[['ConfigReader'], None] = None):
        if settings is None:
            settings = {}

        self.settings = settings
        self.path = path
        self._on_commit = on_commit

    def has(self, key: str, sub: bool = False) -> bool:
        if not sub:
            return key in self.settings

        return any(k.startswith(key) for k in self.settings)

    # fixme: i'm crying
    def get(self, key: str, default=None) -> str:
        result = self.settings.get(key, default)
        assert result is not None, "empty key reached"
        return result

    def getbool(self, key: str, default=None) -> bool:
        value = self.get(key, default)
        match value:
            case "true" | "on" | "yes" | "1" | True:
                return True
            case "false" | "off" | "no" | "0" | False:
                return False
            case _:
                raise ValueError("not convertable")

    def getint(self, key: str, default=None) -> int:
        value = self.get(key, default)
        return int(value)

    def getsub(self, key: str) -> dict:
        return {k.removeprefix(key): v for k, v in self.settings.items() if k.startswith(key)}

    def set(self, key: str, value):
        match value:
            case str():
                self.settings[key] = value
            case int():
                self.settings[key] = str(value)
            case bool():
                self.settings[key] = "true" if value else "false"
            case dict() if all(isinstance(k, str) for k in value):
                for k, v in value.items():
                    self.set(f"{key}{k}", v)
            case _:
                assert False, "invalid value for set"

    def unset(self, key: str, sub: bool = False):
        if not sub:
            del self.settings[key]
        for k in self.settings:
            if k.startswith(key):
                del self.settings[k]

    def overlay(self, reader: 'ConfigReader'):
        if reader is None:
            return
        self.settings.update(reader.settings)

    def clear(self):
        self.settings.clear()

    def save(self):
        if not self.path:
            raise FileNotFoundError("path is unusable")

        _write_ini(self.settings, self.path)

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
        #self.general: ConfigReader = self._create_config()
        self.general: ConfigReader = self._create_config(os.path.join(str(pathlib.Path.home()), ".mistconfig"))
        self.local: ConfigReader = self._create_config(None)
        #self.environment: ConfigReader = self._create_config(None)
        self.args: ConfigReader = self._create_config(None)
        self.active: ConfigReader = self._create_config(None)

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

    def _create_config(self, path) -> ConfigReader:
        return ConfigReader({}, path, on_commit=lambda _: self.apply())


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

def _write_ini(settings: dict[str, str], path: str):
    with open(path, "w") as file:
        _convert_to_ini(settings).write(file)

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

"""
def _translate_environment() -> dict[str, str]:
    mapping = [
        # repository
        "MIST_DIR",
        # diff
        "MIST_EXTERNAL_DIFF",
        "MIST_EXTERNAL_DIFF_TRUST_EXIT_CODE",
        # other
        "MIST_MERGE_VERBOSITY",
        "MIST_PAGER",
        "MIST_PROGRESS_DELAY",
        "MIST_EDITOR",
        "MIST_SSL_NO_VERIFY",
        "MIST_ASKPASS",
        "MIST_CONFIG_GLOBAL", "MIST_CONFIG_SYSTEM",
        "MIST_CONFIG_NOSYSTEM",
        "MIST_FLUSH",
        "MIST_TRACE",
        "MIST_TRACE_REDACT",
        "MIST_REDIRECT_STDIN", "MIST_REDIRECT_STDOUT", "MIST_REDIRECT_STDERR",
        "MIST_ADVICE"
    ]
"""
