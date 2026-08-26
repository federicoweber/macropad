"""Tests for public Spotify album metadata parsing."""

import unittest

from spotify_web_metadata import parse_spotify_meta, spotify_track_web_url


class SpotifyWebMetadataTests(unittest.TestCase):
    def test_parses_album_url_and_deduplicated_tracks(self):
        html = """
        <meta name="music:album" content="https://open.spotify.com/album/abc">
        <meta name="music:song" content="https://open.spotify.com/track/one">
        <meta name="music:song" content="https://open.spotify.com/track/two">
        <meta name="music:song" content="https://open.spotify.com/track/one">
        """
        self.assertEqual(
            parse_spotify_meta(html),
            (
                "https://open.spotify.com/album/abc",
                (
                    "https://open.spotify.com/track/one",
                    "https://open.spotify.com/track/two",
                ),
            ),
        )

    def test_converts_spotify_track_uri(self):
        self.assertEqual(
            spotify_track_web_url("spotify:track:abc123"),
            "https://open.spotify.com/track/abc123",
        )
        self.assertEqual(spotify_track_web_url("spotify:album:abc123"), "")


if __name__ == "__main__":
    unittest.main()
