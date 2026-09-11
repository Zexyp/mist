import os
import warnings
from enum import Enum
from functools import wraps
from typing import AnyStr, Callable
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from textwrap import dedent, indent
import re


def url_strip_utm(url: str) -> AnyStr:
    utm_parameters = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}

    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if not any(param in query for param in utm_parameters):
        return url
    log.warning("removing utm params, better luck next time")

    query = {k: v for k, v in query.items() if k not in utm_parameters}

    pure_query = urlencode(query, doseq=True)
    pure_url = urlunparse(parsed_url._replace(query=pure_query))
    return pure_url

def url_strip_share_identifier(url: str) -> AnyStr:
    share_identifier_param = "si"

    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if share_identifier_param not in query:
        return url
    log.warning("removing share identifier param, better luck next time")

    query.pop(share_identifier_param)

    new_query = urlencode(query, doseq=True)
    pure_url = urlunparse(parsed_url._replace(query=new_query))
    return pure_url

def indent_list(ls: list) -> str:
    # safe function with fallback
    return indent("\n".join(ls) if ls else "", " " * 4)

def strip_ansi(text):
    return re.sub(r'\033\[[0-9;]*m', '', text)

def sanitize_filename(name):
    replacement_char = '_'
    for ch in ['\\', '/', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, replacement_char)
    assert name != "." and ".." not in name
    return name

class FileCache:
    def __init__(self,
                 serialize: Callable = None,
                 deserialize: Callable = None):
        assert bool(serialize) == bool(deserialize)

        self.cache: dict | None = None
        self.serialize: Callable | None = serialize
        self.deserialize: Callable | None = deserialize

    def save_file(self, file):
        assert self.cache is not None

        log.debug(f"saving cache '{file}'")

        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            for k, v in self.cache.items():
                data = v

                if self.serialize: data = self.serialize(data)

                f.write(f"{k}: {data}\n")

        self.cache = None

        log.verbose("cache off")

    def load_file(self, file):
        assert self.cache is None

        log.verbose("using cache")

        self.cache = {}

        log.debug(f"loading cache '{file}'")
        if os.path.isfile(file):
            with open(file, "r") as f:
                while line := f.readline():
                    parts = line.strip().split(": ", 1)

                    data = parts[1]

                    if self.deserialize: data = self.deserialize(data)

                    assert parts[0] not in self.cache
                    self.cache[parts[0]] = data
        else:
            log.debug("cache empty")

    # this is eew
    def cached(self, func=None, key: Callable = None, ignore=None):
        def decorator(actual_func):
            @wraps(actual_func)
            def wrapper(*args, **kwargs):
                nonlocal key
                if key is not None:
                    dict_key = key(*args, **kwargs)
                else:
                    assert len(args) == 1 and not kwargs
                    dict_key = args[0]
                assert isinstance(dict_key, str)

                if self.cache is not None and dict_key in self.cache:
                    return self.cache[dict_key]

                result = actual_func(*args, **kwargs)

                if self.cache is not None and result != ignore:
                    self.cache[dict_key] = result

                return result
            return wrapper

        if func is not None and callable(func):
            return decorator(func)

        return decorator

class MistEnum(Enum):
    @property
    def name(self):
        return self._name_.lower()

    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if member.name.lower() == str(value).lower():
                return member
        return None
