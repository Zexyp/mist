import os

DIR_REPOSITORY = ".mist"

#FILE_IGNORE = ".mistignore"
#FILE_MODULES = ".mistmodules"

FILE_GLOBAL_CONFIG = ".mistconfig"

FILE_REPOSITORY_CONFIG = "config" # repository config name
FILE_REPOSITORY_REMOTE = "remote" # current remote name

DIR_REFS = "refs"
DIR_REFS_REMOTES = os.path.join(DIR_REFS, "remotes")
DIR_REFS_TAGS = os.path.join(DIR_REFS, "tags")
DIR_OBJECTS = "objects"