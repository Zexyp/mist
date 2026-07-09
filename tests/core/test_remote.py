from mist import MistError
from . import MistTest


class TestRemote(MistTest):
    def setUp(self):
        super().setUp()

        self.mist.init(".")

    def test_add(self):
        self.mist.remote_add("origin", "https://music.youtube.com/playlist?list=PL0LVK5Sb2wOeYQdrUjaGW2SjgMS_sZ8lB")
        self.assertTrue(self.mist.config.active.has("remote.origin", sub=True))

    def test_remove(self):
        self.mist.remote_add("origin", "https://music.youtube.com/playlist?list=PL0LVK5Sb2wOeYQdrUjaGW2SjgMS_sZ8lB")
        self.mist.remote_remove("origin")
        self.assertFalse(self.mist.config.active.has("remote.origin", sub=True))

    def test_remove_fail(self):
        self.assertRaises(MistError, self.mist.remote_remove, "origin")

    def test_set_url(self):
        self.mist.remote_add("origin", "https://music.youtube.com/playlist?list=PL0LVK5Sb2wOeYQdrUjaGW2SjgMS_sZ8lB")
        self.mist.remote_set_url("origin", "crazy hamburger")
        self.assertTrue(self.mist.remote_get_url("origin"))
