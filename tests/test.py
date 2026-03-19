import mist
import mist.errors

from . import TempDirTestCase

class TestInit(TempDirTestCase):
    def test(self):
        mist.init()

class TestInitFail(TempDirTestCase):
    def setUp(self):
        super().setUp()
        mist.init()

    def test(self):
        self.assertRaises(mist.errors.InitializationError, mist.init)

class TestStatusFail(TempDirTestCase):
    def test(self):
        self.assertRaises(mist.errors.InitializationError, mist.status)
