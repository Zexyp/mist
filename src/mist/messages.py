from typing import Callable

from . import files

MSG_LOCAL_NO_REPOSITORY: str = "--local can only be used inside a mist repository"
MSG_NO_CONFIG_TO_WRITE: str = "not in a mist directory"
MSG_NOT_A_REPOSITORY: str = f"not a mist repository (or any of the parent directories): {files.DIR_REPOSITORY}"
MSG_NO_SUCH_REMOTE: str = "No such remote '{name}'"
MSG_REMOTE_ALREADY_EXISTS: str = "remote {name} already exists."
MSG_CD_NO_SUCH_DIR: str = "cannot change to '{directory}': No such directory"