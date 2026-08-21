"""Host-side tests for the hardware-independent key map."""

import unittest

from config import KEYMAP, ROW_TITLES, validate_keymap


class KeymapTests(unittest.TestCase):
    def test_default_keymap_is_valid(self):
        self.assertEqual(validate_keymap(), [])

    def test_layout_matches_physical_board(self):
        self.assertEqual(len(KEYMAP), 12)
        self.assertEqual(len(ROW_TITLES), 4)

    def test_flow_row_uses_dedicated_shortcuts(self):
        self.assertEqual(
            [binding["keys"][-1] for binding in KEYMAP[:3]],
            ["F13", "F14", "F15"],
        )

    def test_music_row_uses_consumer_controls(self):
        self.assertEqual(
            [binding["code"] for binding in KEYMAP[9:]],
            ["SCAN_PREVIOUS_TRACK", "PLAY_PAUSE", "SCAN_NEXT_TRACK"],
        )

    def test_validation_catches_wrong_key_count(self):
        self.assertIn(
            "KEYMAP must contain exactly 12 entries",
            validate_keymap(KEYMAP[:-1]),
        )


if __name__ == "__main__":
    unittest.main()
