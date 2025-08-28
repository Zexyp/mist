import concurrent.futures
import subprocess
import platform
from typing import Callable, Iterable

from .log import log_warning

def is_termux():
    if platform.system() == 'Linux':
        return subprocess.check_output(['uname', '-o']).strip() == "Android"
    return False

def run_concurrently(func: Callable, args_list: Iterable):
    if not is_termux():
        with concurrent.futures.ThreadPoolExecutor() as ex:
            futures = {ex.submit(func, arg) for arg in args_list}
            for future in concurrent.futures.as_completed(futures):
                future.result()
        return

    log_warning("concurrency is not supported on this platform")
    for args in args_list:
        func(*args)
