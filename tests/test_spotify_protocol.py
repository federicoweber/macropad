"""Host-side tests for Spotify playback messages and OLED rows."""

import unittest

from spotify_protocol import (
    PlaybackPauseController,
    build_audio_level_message,
    build_message,
    clean_field,
    equalizer_intensities,
    equalizer_pixels,
    pixel_index_for_key,
    format_time,
    parse_message,
    parse_audio_level_message,
    playback_is_active,
    playback_display_rows,
    scrolling_display_text,
    smooth_equalizer_intensities,
    transport_label,
)


class SpotifyProtocolTests(unittest.TestCase):
    def test_audio_level_round_trip_and_validation(self):
        message = build_audio_level_message((0.5, -1, 2))
        self.assertEqual(message, "SPOTIFY_LEVEL\t127\t0\t255\n")
        self.assertEqual(
            parse_audio_level_message(message),
            (127 / 255, 0.0, 1.0),
        )
        self.assertIsNone(parse_audio_level_message("SPOTIFY_LEVEL\tbad\t0\t0\n"))
        self.assertIsNone(parse_audio_level_message("SPOTIFY_LEVEL\t256\t0\t0\n"))
        with self.assertRaises(ValueError):
            build_audio_level_message((0.5, 0.5))

    def test_equalizer_pixels_grow_up_each_column(self):
        self.assertEqual(
            equalizer_pixels((0.3, 0.5, 0.9)),
            (
                False, False, True,
                False, True, True,
                False, True, True,
                True, True, True,
            ),
        )

    def test_equalizer_gain_reduces_saturation(self):
        full_gain = equalizer_pixels((0.7, 0.7, 0.7))
        reduced_gain = equalizer_pixels((0.7, 0.7, 0.7), 0.80)
        self.assertGreater(sum(full_gain), sum(reduced_gain))

    def test_equalizer_intensities_leave_untriggered_spots_off(self):
        self.assertEqual(equalizer_intensities((0.0, 0.0, 0.0)), (0.0,) * 12)
        intensities = equalizer_intensities((0.5, 0.5, 0.5))
        self.assertEqual(intensities[:3], (0.0, 0.0, 0.0))
        self.assertEqual(intensities[3:], (1.0,) * 9)

    def test_equalizer_intensities_fade_with_attack_and_release(self):
        faded_in = smooth_equalizer_intensities(
            (0.0, 0.0), (1.0, 0.0), 0.35, 0.12
        )
        self.assertEqual(faded_in, (0.35, 0.0))
        faded_out = smooth_equalizer_intensities(
            faded_in, (0.0, 0.0), 0.35, 0.12
        )
        self.assertAlmostEqual(faded_out[0], 0.308)
        self.assertEqual(faded_out[1], 0.0)

    def test_pixel_indices_follow_macropad_serpentine_rows(self):
        self.assertEqual(
            tuple(pixel_index_for_key(index) for index in range(12)),
            (0, 1, 2, 5, 4, 3, 6, 7, 8, 11, 10, 9),
        )

    def test_playback_pause_controller_handles_overlapping_modes(self):
        controller = PlaybackPauseController()
        self.assertTrue(controller.begin("flow_free", True))
        self.assertFalse(controller.begin("ptt", True))
        self.assertFalse(controller.end("flow_free"))
        self.assertTrue(controller.end("ptt"))

    def test_playback_pause_controller_does_not_resume_prepaused_music(self):
        controller = PlaybackPauseController()
        self.assertFalse(controller.begin("codex_voice", False))
        self.assertFalse(controller.end("codex_voice"))

    def test_playback_pause_controller_cancel_resumes_once(self):
        controller = PlaybackPauseController()
        self.assertTrue(controller.begin("flow_free", True))
        self.assertTrue(controller.cancel())
        self.assertFalse(controller.cancel())
        self.assertFalse(controller.end("flow_free"))

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

    def test_playing_rows_use_requested_order(self):
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
        self.assertEqual(rows[0], "A very long artist name")
        self.assertEqual(rows[1], "An album with a very long name")
        self.assertEqual(rows[2], "A title that is much longer than the OLED")
        self.assertEqual(rows[3], "1:05 / 4:05")

    def test_long_display_text_scrolls_toward_the_end(self):
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.assertEqual(scrolling_display_text(text, 0), "ABCDEFGHIJKLMNOPQRSTU")
        self.assertEqual(scrolling_display_text(text, 4), "BCDEFGHIJKLMNOPQRSTUV")
        self.assertEqual(scrolling_display_text(text, 8), "FGHIJKLMNOPQRSTUVWXYZ")
        self.assertEqual(scrolling_display_text(text, 13), "ABCDEFGHIJKLMNOPQRSTU")
        self.assertEqual(scrolling_display_text("Short", 99), "Short                ")

    def test_time_format(self):
        self.assertEqual(format_time(65), "1:05")
        self.assertEqual(format_time(3661), "1:01:01")

    def test_transport_label_tracks_playback_state(self):
        self.assertEqual(transport_label(None), "PLAY")
        self.assertEqual(transport_label({"state": "stopped"}), "PLAY")
        self.assertEqual(transport_label({"state": "paused"}), "PLAY")
        self.assertEqual(transport_label({"state": "playing"}), "PAUSE")

    def test_active_playback_state(self):
        self.assertFalse(playback_is_active(None))
        self.assertFalse(playback_is_active({"state": "paused"}))
        self.assertFalse(playback_is_active({"state": "stopped"}))
        self.assertTrue(playback_is_active({"state": "playing"}))

    def test_malformed_messages_are_ignored(self):
        self.assertIsNone(parse_message("hello"))
        self.assertIsNone(parse_message("SPOTIFY\tplaying\tmissing"))
        self.assertIsNone(
            parse_message("SPOTIFY\tplaying\tSong\tArtist\tAlbum\tbad\t10")
        )


if __name__ == "__main__":
    unittest.main()
