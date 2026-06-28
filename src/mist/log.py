import sys
import os
import logging
import traceback

COL_RESET  = ""
COL_RED    = ""
COL_YELLOW = ""
COL_DIM    = ""
COL_CYAN   = ""

SOUND_BASE_PATH = os.path.join(os.path.dirname(__file__), "res", "sounds")

DEBUG: bool = False

def deinit_colors():
    global COL_RESET, COL_YELLOW, COL_DIM, COL_RED, COL_CYAN

    COL_RESET  = ""
    COL_RED    = ""
    COL_YELLOW = ""
    COL_CYAN   = ""
    COL_DIM    = ""

    if not colorama:
        return

    colorama.deinit()

    debug("colors deinitialized")

def init_colors():
    if not colorama:
        return

    colorama.init()

    global COL_RESET, COL_YELLOW, COL_DIM, COL_RED, COL_CYAN

    COL_RESET = colorama.Style.RESET_ALL
    COL_RED = colorama.Fore.RED
    COL_YELLOW = colorama.Fore.YELLOW
    COL_DIM = colorama.Style.DIM
    COL_CYAN = colorama.Fore.CYAN

    debug("colors initialized")

def debug(msg):
    if DEBUG:
        print(COL_DIM + f"debug: {msg}" + COL_RESET, file=sys.stderr)

def warning(msg):
    print(COL_YELLOW + f"warning: {msg}" + COL_RESET, file=sys.stderr)

def error(msg):
    print(COL_RED + f"error: {msg}" + COL_RESET, file=sys.stderr)

def fatal(msg):
    print(COL_RED + f"fatal: {msg}" + COL_RESET, file=sys.stderr)

def exception(exc):
    for line in traceback.format_exception(exc):
        debug(line.rstrip())

def configure(cfg):
    global DEBUG
    DEBUG = cfg.getbool("core.debug", False)
    match cfg.get("core.color", "auto"):
        case "off":
            pass
        case "force":
            init_colors()
        case "auto":
            if sys.stdin.isatty():
                init_colors()
        case _:
            assert False


try:
    import colorama
except ImportError as e:
    colorama = None
    exception(e)
    warning("color module import error (colorama)")

class CustomHandler(logging.Handler):
    def emit(self, record):
        message = self.format(record)
        match record.levelno:
            case _ if record.levelno <= logging.DEBUG:
                debug(message)
            case _ if record.levelno <= logging.INFO:
                print(message)
            case _ if record.levelno <= logging.WARNING:
                warning(message)
            case _ if record.levelno <= logging.ERROR:
                error(message)
            case _:
                fatal(message)

        #self.stream.write(message)
        #self.stream.flush()

_handler = CustomHandler()
_handler.setFormatter(logging.Formatter(
    fmt="[%(asctime)s][%(name)s][%(levelname)s]: %(message)s",
    datefmt="%Y.%m.%d-%H:%M:%S"
))

def spawn_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    logger.addHandler(_handler)
    return logger