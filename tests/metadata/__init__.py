import unittest
from mist.metadata import yt, sc, lfm, bc


class ConnectorTest(unittest.TestCase):
    def test_lfm(self):
        conn = lfm.LastFmConnector()
        self.assertEqual(conn.get_track_tags("https://www.last.fm/music/Geoxor/_/Woosh"), [
            "electro house",
            "future bass",
            "drumstep",
            "melodic dubstep",
        ])
        self.assertEqual(conn.get_track_artwork("https://www.last.fm/music/Geoxor/_/Woosh"))
        raise NotImplementedError

    def test_yt(self):
        conn = yt.YouTubeConnector()
        raise NotImplementedError

    def test_sc(self):
        conn = sc.SoundCloudConnector()
        self.assertEqual(conn.get_track_genre("234331640"), "dnb")
        raise NotImplementedError
