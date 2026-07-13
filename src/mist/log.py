import sys
import os
import logging
import traceback
import warnings

from . import _package_name

COL_RESET  = ""
COL_RED    = ""
COL_YELLOW = ""
COL_DIM    = ""
COL_CYAN   = ""

SOUND_BASE_PATH = os.path.join(os.path.dirname(__file__), "res", "sounds")

logger = logging.getLogger(_package_name)

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

    logger.debug("colors deinitialized")

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

    logger.debug("colors initialized")

def announce_optional_module_error(error: ImportError):
    warnings.warn(f"optional module import error ({error.name})")

try:
    import colorama
except ImportError as e:
    colorama = None
    announce_optional_module_error(e)

class CustomHandler(logging.Handler):
    def emit(self, record):
        message = self.format(record)
        match record.levelno:
            case _ if record.levelno <= logging.DEBUG:
                print(COL_DIM + f"debug: {message}" + COL_RESET, file=sys.stderr)
            case _ if record.levelno <= logging.INFO:
                print(f"info: {message}")
            case _ if record.levelno <= logging.WARNING:
                print(COL_YELLOW + f"warning: {message}" + COL_RESET, file=sys.stderr)
            case _ if record.levelno <= logging.ERROR:
                print(COL_RED + f"error: {message}" + COL_RESET, file=sys.stderr)
            case _:
                print(COL_RED + f"fatal: {message}" + COL_RESET, file=sys.stderr)

        #self.stream.write(message)
        #self.stream.flush()
