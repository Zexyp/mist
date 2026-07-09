import os

from . import MistTest

class TestInit(MistTest):
    def test(self):
        self.mist.init(".")
        self.assertTrue(os.path.isdir(self.mist.repository_dir))

    def test_other_dir(self):
        self.mist.init("./yeet")
        self.assertTrue(os.path.isdir(self.mist.repository_dir))
