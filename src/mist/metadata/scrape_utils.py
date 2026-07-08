import json
from pprint import pprint
from typing import Any

import requests

class RateLimitHitError(Exception):
    pass

def json_path_get(root: dict, path: str) -> Any:
    """reinventing the wheel, no simd optimisation tho"""
    keys = path.split("/")
    element = root
    for key in keys:
        if key.startswith("[") and key.endswith("]"):
            index = int(key.strip("[]"))
            element = element[index]
            continue

        #if isinstance(element, dict):
        #    print(element.keys())
        element = element[key]
    return element

def json_path_set(root: dict, path: str, value):
    keys = path.split("/")
    element = root
    for key in keys[:-1]:
        element = element.setdefault(key, {})
    element[keys[-1]] = value

# i have no fucking clue how to name this
def json_dict_of_key(dictionaries: list[dict], key) -> Any:
    for d in dictionaries:
        if key in d:
            return d[key]
    raise KeyError

def extract_script_data(tree, hook: str):
    results = tree.xpath(f"/html/body/script[starts-with(text(), '{hook}')]/text()")
    assert len(results) == 1
    json_str = results[0].removeprefix(hook).removesuffix(";").strip()
    return json.loads(json_str)

def assert_status_code(response: requests.Response, code=200):
    if response.status_code == code:
        return

    msg = "unexpected anomaly"
    match response.status_code:
        case status_code if 100 <= status_code <= 199: msg = "unexpected informational responses"
        case status_code if 200 <= status_code <= 299: msg = "unexpected successful responses"
        case status_code if 300 <= status_code <= 399: msg = "unexpected redirection messages"
        case status_code if 400 <= status_code <= 499: msg = "unexpected client error"
        case status_code if 500 <= status_code <= 599: msg = "unexpected server error"
    assert False, f"{msg} ({response.status_code})"

def urlappend(url: str, path: str) -> str:
    return url.rstrip("/") + "/" + path

def assert_single(value):
    assert len(value) == 1, "not a single element"
    return value[0]
