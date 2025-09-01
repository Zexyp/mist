import sys
import os
import logging
import traceback

COL_RESET  = ""
COL_RED    = ""
COL_YELLOW = ""
COL_DIM    = ""

SOUND_BASE_PATH = os.path.join(os.path.dirname(__file__), "res", "sounds")

_verbose = False
_debug = False
_sound = True

def deinit_colors():
    global COL_RESET, COL_YELLOW, COL_DIM, COL_RED

    COL_RESET  = ""
    COL_RED    = ""
    COL_YELLOW = ""
    COL_DIM    = ""

    if not colorama:
        return

    colorama.deinit()

    log_debug("colors deinitialized")

def init_colors():
    if not colorama:
        return

    colorama.init()

    global COL_RESET, COL_YELLOW, COL_DIM, COL_RED

    COL_RESET = colorama.Style.RESET_ALL
    COL_RED = colorama.Fore.RED
    COL_YELLOW = colorama.Fore.YELLOW
    COL_DIM = colorama.Style.DIM

    log_debug("colors initialized")

def log_print(msg):
    print(msg)

def log_verbose(msg):
    if _verbose: print(COL_DIM + msg + COL_RESET)

def log_debug(msg):
    if _debug: print(COL_DIM + f"debug: {msg}" + COL_RESET, file=sys.stderr)

def log_warning(msg):
    print(COL_YELLOW + f"warning: {msg}" + COL_RESET, file=sys.stderr)

def log_error(msg):
    print(COL_RED + f"error: {msg}" + COL_RESET, file=sys.stderr)

def log_fatal(msg):
    print(COL_RED + f"fatal: {msg}" + COL_RESET, file=sys.stderr)

def log_exception(e):
    log_debug("".join(traceback.format_exception(e)))
    log_verbose(type(e).__name__)


def _play_random(category):
    if _sound and playsound:
        directory = os.path.join(SOUND_BASE_PATH, category)
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        import random
        playsound(os.path.join(directory, random.choice(files)), False)

def notify_failed():
    _play_random("failed")

def notify_death():
    _play_random("death")

def notify_target():
    _play_random("target")

try:
    import colorama
    init_colors()
except ImportError as e:
    log_exception(e)
    colorama = None
    log_warning("color module import error (colorama)")

# craptastic feature (dev) thingy
try:
    logging.getLogger("playsound").setLevel(logging.ERROR)  # way to make this nigga shut up
    from playsound import playsound
except ImportError as e:
    log_exception(e)
    playsound = None
    log_warning("sound module import error (playsound)")
