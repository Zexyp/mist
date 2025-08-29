import concurrent.futures
import subprocess
import platform
import traceback
from typing import Callable, Iterable

from .log import log_warning, log_verbose, log_error, log_debug

def is_termux():
    if platform.system() == 'Linux':
        return subprocess.check_output(['uname', '-o']).strip() == b"Android"
    return False

def run_concurrently(func: Callable, args_list: Iterable) -> Iterable:
    tid = 0
    # a bit skibidi return value
    def safety_wrapper(*args, **kwargs):
        nonlocal tid
        log_verbose(f"running task {tid}")
        tid += 1
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_debug(traceback.format_exc())
            log_verbose(type(e).__name__)
            log_error(f"concurrent task failed: {repr(e)}")
            return e

    if is_termux():
        log_warning("concurrency is not supported on this platform")

        def implementation():
            return [safety_wrapper(args) for args in args_list]
    else:
        def implementation():
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = executor.map(safety_wrapper, args_list)
                return results
            except KeyboardInterrupt:
                log_verbose("stopping concurrent tasks")
                executor.shutdown(cancel_futures=True)
                raise

    return implementation()
