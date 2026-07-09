import os

import mist

from . import MistTest

_split_by = "."

class TestMerge(MistTest):
    def test_yt(self):
        directory = "Awake EP"
        files = {
            "KIBI - Awake.d-7iHNTqiJ0",
            "KIBI & KHALEN - Aware.CT2RBVdsvkM",
            "KIBI - Lost.H61sdaEYb7E",
            "KIBI - Pink Flames.8fv1u33UJM0",
            "KIBI - Remember.Jb-uJQHsQkU",
        }

        self.mist.clone("https://music.youtube.com/playlist?list=PL0LVK5Sb2wOeYQdrUjaGW2SjgMS_sZ8lB")

        self.assertTrue(os.path.isdir(directory))
        for file in os.listdir(directory):
            if not os.path.isfile(os.path.join(directory, file)):
                continue
            self.assertTrue(file.rsplit(_split_by, 1)[0] in files)

    def test_sc(self):
        directory = "Fall Away EP"
        files = {i.rsplit(_split_by, 1)[1] for i in {
            "Feint - Sincere.234331637",
            "Feint - Watch Me.234331642",
            "Feint - Shatter.234331640",
            "Feint - Fall Away.234331645"
        }}

        self.mist.clone("https://soundcloud.com/feintdnb/sets/fall-away-ep-2")

        self.assertTrue(os.path.isdir(directory))
        for file in os.listdir(directory):
            if not os.path.isfile(os.path.join(directory, file)):
                continue
            self.assertTrue(file.rsplit(_split_by, 2)[1] in files)
