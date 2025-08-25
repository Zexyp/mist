class MistError(Exception):
    pass

class NotInitializedError(MistError):
    pass

class RemoteNotFoundError(MistError):
    pass