import sys
import traceback

from . import cli
from .log import log_error, log_warning, log_print, notify_failed, notify_death, log_debug
from .errors import MistError

def main():
    try:
        cli.run()
    except MistError as e:
        log_error(str(e))
        sys.exit(1)
    except AssertionError as e:
        log_error(repr(e))
        log_debug(traceback.format_exc())
        sys.exit(1)
    except NotImplementedError as e:
        log_error(repr(e))
        notify_failed()
        log_error("lazy fuck detected")
        log_debug(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        log_error(repr(e))
        notify_death()
        log_error("unrecoverable error")
        log_debug(traceback.format_exc())
        sys.exit(1)
    
if __name__ == "__main__":
    main()
