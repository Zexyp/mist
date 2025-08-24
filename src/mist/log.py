import sys
try:
    import colorama
    colorama.init()
    COL_RESET  = colorama.Fore.RESET
    COL_RED    = colorama.Fore.RED
    COL_YELLOW = colorama.Fore.YELLOW
except ImportError:
    print("color module not found")
    pass

COL_RESET  = COL_RESET  or ""
COL_RED    = COL_RED    or ""
COL_YELLOW = COL_YELLOW or ""

_verbose = True

def log_print(msg):
    print(msg)

def log_verbose(msg):
    if _verbose: print(msg)

def log_warning(msg):
    print(COL_YELLOW + msg + COL_RESET, file=sys.stderr)

def log_error(msg):
    print(COL_RED + msg + COL_RESET, file=sys.stderr)
