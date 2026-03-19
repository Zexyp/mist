import os

import mist

from . import TempDirTestCase

class TestClone(TempDirTestCase):
    def test_yt(self):
        directory = "Awake EP"
        files = [
            "KIBI - Awake.d-7iHNTqiJ0.opus",
            "KIBI & KHALEN - Aware.CT2RBVdsvkM.opus",
            "KIBI - Lost.H61sdaEYb7E.opus",
            "KIBI - Remember.Jb-uJQHsQkU.opus",
        ]

        mist.clone("https://music.youtube.com/playlist?list=PL0LVK5Sb2wOeYQdrUjaGW2SjgMS_sZ8lB")

        self.assertTrue(os.path.isdir(directory))
        for file in files:
            self.assertTrue(os.path.isfile(os.path.join(directory, file)))

    def test_sc(self):
        directory = "Fall Away EP"
        files = [
            "Feint - Sincere.234331637.m4a",
            "Feint - Watch Me.234331642.m4a",
            "Feint - Shatter.234331640.m4a",
            "Feint - Fall Away.234331645.m4a"
        ]

        mist.clone("https://soundcloud.com/feintdnb/sets/fall-away-ep-2")

        self.assertTrue(os.path.isdir(directory))
        for file in files:
            self.assertTrue(os.path.isfile(os.path.join(directory, file)))
