import collections
from typing import AnyStr # ide kept yappin
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import math
import time
import threading
from collections import deque

from .log import *

def url_strip_utm(url: str) -> AnyStr:
    utm_parameters = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}

    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if not any(param in query for param in utm_parameters):
        return url
    log_warning("removing utm params, better luck next time")

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
    log_warning("removing share identifier param, better luck next time")

    query.pop(share_identifier_param)

    new_query = urlencode(query, doseq=True)
    pure_url = urlunparse(parsed_url._replace(query=new_query))
    return pure_url

def sanitize_filename(name):
    replacement_char = '_'
    for ch in ['\\', '/', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, replacement_char)
    assert name != "." and name != ".."
    return name

def find_duplicates(items: list):
    # try passing in set and i will beat your ass
    duplicates = [item for item, count in collections.Counter(items).items() if count > 1]
    return duplicates

import string
import re

def print_progress_bar(amount: int | float, total: int | float,
                       prefix: str = "",
                       suffix: str = "",
                       decimals: int = 0,
                       percent_decimals: int = 1,
                       width: int | None = None, # automatic if set to None, 0 to force bar length
                       bar_length: int = 80,
                       fill: str = '█',
                       empty: str = '-',
                       template: str ="$prefix |$bar| $percent % ($amount/$total) $suffix",
                       finish: bool | None = None # if set to None finishing action is automatic
                       ):
    """
    this function is not just *stolen*, it's also improved
    it's my precious child
    """
    assert 0 <= amount <= total

    percent_length = 3 + 1 + percent_decimals
    total_string = f"{total:.{decimals}f}"
    total_string_length = len(total_string)

    # auto set width
    if width is None and sys.stdout.isatty():
        width = os.get_terminal_size().columns

    if width:
        junk_length = 0
        def replacer(m):
            nonlocal junk_length
            match m.group(1) or m.group(2):
                case "prefix": junk_length += len(prefix)
                case "suffix": junk_length += len(suffix)
                case "percent": junk_length += percent_length
                case "total": junk_length += total_string_length
                case "amount": junk_length += total_string_length
                case "bar": pass
                case _: assert False
            return ""

        # put skull emoji here for the regex
        # default patter from docs https://docs.python.org/3/library/string.html
        junk = re.sub(r"(?<!\$)\$([_a-z][_a-z0-9]*)|(?<!\$)\$\{([_a-z][_a-z0-9]*)\}", replacer, template)
        junk_length += len(junk)
        # clamp
        bar_length = max(width - junk_length, 0)

    if total:
        percent_value = 100 * (amount / total)
        percent = f"{percent_value:.{percent_decimals}f}".rjust(percent_length)
        filled_length = min(bar_length, int(bar_length * amount // total))
    else:
        percent = "-".rjust(percent_length)
        filled_length = 0

    bar = fill * filled_length + empty * (bar_length - filled_length)

    line = string.Template(template).safe_substitute(prefix=prefix,
                                                     bar=bar,
                                                     percent=percent,
                                                     amount=f"{amount:.{decimals}f}".rjust(total_string_length),
                                                     total=total_string,
                                                     suffix=suffix)
    print(f"\r{line}", end="")

    # print new line on complete
    if amount == total and finish is None:
        print()

    if finish:
        print()

def float_or_none(v, scale=1, invscale=1, default=None):
    if v is None:
        return default
    if invscale == 1 and scale < 1:
        invscale = int(1 / scale)
        scale = 1
    try:
        return float(v) * invscale / scale
    except (ValueError, TypeError):
        return default

def format_decimal_suffix(num, fmt='%d%s', *, factor=1000):
    """ Formats numbers with decimal sufixes like K, M, etc """
    num, factor = float_or_none(num), float(factor)
    if num is None or num < 0:
        return None
    POSSIBLE_SUFFIXES = 'kMGTPEZY'
    exponent = 0 if num == 0 else min(int(math.log(num, factor)), len(POSSIBLE_SUFFIXES))
    suffix = ['', *POSSIBLE_SUFFIXES][exponent]
    if factor == 1024:
        suffix = {'k': 'Ki', '': ''}.get(suffix, f'{suffix}i')
    converted = num / (factor ** exponent)
    return fmt % (converted, suffix)

def format_bytes(bytes):
    return format_decimal_suffix(bytes, '%.2f%sB', factor=1024) or 'N/A'


class RateLimiter:
    def __init__(self, max_calls, period_seconds):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls = deque()
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.time()

            def clear_timestamps():
                while self.calls and now - self.calls[0] > self.period:
                    self.calls.popleft()

            clear_timestamps()

            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                # NOTE: rate is not spelled tate
                log_verbose(f"rate limit hit, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                now = time.time()
                clear_timestamps()

            self.calls.append(time.time())