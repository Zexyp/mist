from mist import Mist


class MistCompleter(object):
    def __init__(self, mist: Mist):
        self.mist = mist

class RemoteCompleter(MistCompleter):
    def __call__(self, **kwargs):
        if self.mist.is_repository():
            return [i.name for i in self.mist.get_remotes()]
        return None

class HelpCompleter(object):
    def __init__(self):
        pass

    def __call__(self, **kwargs):
        raise NotImplementedError