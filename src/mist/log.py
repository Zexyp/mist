import sys
import os

COL_RESET  = ""
COL_RED    = ""
COL_YELLOW = ""

SOUND_BASE_PATH = os.path.join(os.path.dirname(__file__), "res", "sounds")

# craptastic feature (dev) thingy
try:
    from playsound import playsound
except ImportError:
    print("sound module import error (playsound)", file=sys.stderr)
    pass

try:
    import colorama
    colorama.init()
    COL_RESET  = colorama.Fore.RESET
    COL_RED    = colorama.Fore.RED
    COL_YELLOW = colorama.Fore.YELLOW
except ImportError:
    print("color module import error (colorama)", file=sys.stderr)
    pass

_verbose = False

def log_print(msg):
    print(msg)

def log_verbose(msg):
    if _verbose: print(msg)

def log_warning(msg):
    print(COL_YELLOW + msg + COL_RESET, file=sys.stderr)

def log_error(msg):
    print(COL_RED + msg + COL_RESET, file=sys.stderr)

def play_random(category):
    if playsound:
        directory = os.path.join(SOUND_BASE_PATH, category)
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        import random
        playsound(os.path.join(directory, random.choice(files)), False)

def notify_failed():
    play_random("failed")

def notify_death():
    play_random("death")

