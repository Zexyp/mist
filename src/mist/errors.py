class MistError(Exception):
    pass

class RemoteError(MistError):
    pass

class InitializationError(MistError):
    pass

class NoDataFileError(FileNotFoundError, MistError):
    pass

class ConfigurationError(MistError):
    pass

class RemoteNotFoundError(RemoteError):
    pass

class RemoteExistsError(RemoteError):
    pass