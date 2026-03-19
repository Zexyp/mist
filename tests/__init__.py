import os
import tempfile
import unittest


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self.prev_dir = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        #print("temporary directory: %s" % self.temp_dir.name)
        os.chdir(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()
        os.chdir(self.prev_dir)