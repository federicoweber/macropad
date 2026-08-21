"""Host-side tests for Spotify playback messages and OLED rows."""

import unittest

from spotify_protocol import (
    build_message,
    clean_field,
    format_time,
    parse_message,
    playback_display_rows,
    transport_label,
)


class SpotifyProtocolTests(unittest.TestCase):
    def test_round_trip_playing_message(self):
        message = build_message(
            "playing", "Easier To Run", "Linkin Park", 155, 204, "Meteora"
        )
        self.assertEqual(
            parse_message(message),
            {
                "state": "playing",
                "title": "Easier To Run",
                "artist": "Linkin Park",
                "album": "Meteora",
                "position": 155,
                "duration": 204,
            },
        )

    def test_clean_field_is_one_ascii_line(self):
        self.assertEqual(clean_field("Beyoncé\tLive\n"), "Beyonc? Live ")

    def test_paused_and_stopped_do_not_replace_media_keymap(self):
        self.assertIsNone(playback_display_rows(parse_message("SPOTIFY\tstopped\n")))
        paused = parse_message(
            build_message("paused", "Song", "Artist", 1, 2, "Album")
        )
        self.assertIsNone(playback_display_rows(paused))

    def test_playing_rows_fit_oled(self):
        playback = parse_message(
            build_message(
                "playing",
                "A title that is much longer than the OLED",
                "A very long artist name",
                65,
                245,
                "An album with a very long name",
            )
        )
        rows = playback_display_rows(playback)
        self.assertEqual(rows[0], "A very long artist na")
        self.assertEqual(rows[1], "An album with a very ")
        self.assertEqual(rows[2], "A title that is much ")
        self.assertEqual(rows[3], "1:05 / 4:05")
        self.assertTrue(all(len(row) <= 21 for row in rows))

    def test_time_format(self):
        self.assertEqual(format_time(65), "1:05")
        self.assertEqual(format_time(3661), "1:01:01")

    def test_transport_label_tracks_playback_state(self):
        self.assertEqual(transport_label(None), "PLAY")
        self.assertEqual(transport_label({"state": "stopped"}), "PLAY")
        self.assertEqual(transport_label({"state": "paused"}), "PLAY")
        self.assertEqual(transport_label({"state": "playing"}), "PAUSE")

    def test_malformed_messages_are_ignored(self):
        self.assertIsNone(parse_message("hello"))
        self.assertIsNone(parse_message("SPOTIFY\tplaying\tmissing"))
        self.assertIsNone(
            parse_message("SPOTIFY\tplaying\tSong\tArtist\tAlbum\tbad\t10")
        )


if __name__ == "__main__":
    unittest.main()
