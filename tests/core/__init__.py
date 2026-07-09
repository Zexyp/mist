import os
from textwrap import indent

from mist import Mist
from .. import TempDirTestCase

class MistTest(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.mist = Mist()

    def tearDown(self):
        self.mist = None
        super().tearDown()
