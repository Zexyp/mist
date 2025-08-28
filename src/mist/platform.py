import concurrent.futures
import subprocess
import platform
import traceback
from typing import Callable, Iterable

from .log import log_warning, log_verbose, log_error

def is_termux():
    if platform.system() == 'Linux':
        return subprocess.check_output(['uname', '-o']).strip() == "Android"
    return False

def run_concurrently(func: Callable, args_list: Iterable) -> Iterable:
    tid = 0
    def safety_wrapper(*args, **kwargs):
        nonlocal tid
        log_verbose(f"running task {tid}")
        tid += 1
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_verbose(traceback.format_exc())
            log_error(f"concurrent task failed: {repr(e)}")
            return e

    if not is_termux():

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(safety_wrapper, args_list)
        return results

    log_warning("concurrency is not supported on this platform")

    return [safety_wrapper(args) for args in args_list]
