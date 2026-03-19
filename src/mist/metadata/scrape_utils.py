import json
from typing import Any

class RateLimitHitError(Exception):
    pass

def json_path_get(root: dict, path: str) -> Any:
    keys = path.split("/")
    element = root
    for key in keys[:-1]:
        element = element[key]
    return element[keys[-1]]

def json_path_set(root: dict, path: str, value):
    keys = path.split("/")
    element = root
    for key in keys[:-1]:
        element = element.setdefault(key, {})
    element[keys[-1]] = value

# i have no fucking clue how to name this
def json_dict_of_key(dictionary: list[dict], key) -> Any:
    for d in dictionary:
        if key in d:
            return d[key]
    raise KeyError

def extract_script_data(tree, hook: str):
    results = tree.xpath(f"/html/body/script[starts-with(text(), '{hook}')]/text()")
    assert len(results) == 1
    json_str = results[0].removeprefix(hook).removesuffix(";").strip()
    return json.loads(json_str)