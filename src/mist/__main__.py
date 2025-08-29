import sys
import traceback

from . import cli, log_verbose
from .log import log_error, log_warning, log_print, notify_failed, notify_death, log_debug, log_fatal, log_exception
from .errors import MistError

def main():
    try:
        cli.run()
    except MistError as e:
        log_exception(e)
        log_error(str(e))
        sys.exit(1)
    except AssertionError as e:
        log_exception(e)
        log_fatal(f"{type(e).__name__}: {str(e)}")
        sys.exit(1)
    except NotImplementedError as e:
        log_exception(e)
        log_error("lazy fuck detected")
        log_fatal(f"{type(e).__name__}: {str(e)}")
        notify_failed()
        sys.exit(1)
    except Exception as e:
        log_exception(e)
        log_fatal(f"{type(e).__name__}: {str(e)}")
        log_fatal("unrecoverable error")
        notify_death()
        sys.exit(1)
    
if __name__ == "__main__":
    main()
