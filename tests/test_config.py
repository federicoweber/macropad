"""Host-side tests for the hardware-independent profiles."""

import unittest

from config import PROFILES, validate_profiles


class ProfileTests(unittest.TestCase):
    def test_default_profiles_are_valid(self):
        self.assertEqual(validate_profiles(), [])

    def test_expected_profiles_exist(self):
        self.assertEqual(
            [profile["name"] for profile in PROFILES],
            ["FLOW", "CODEX", "TOWN", "MUSIC"],
        )

    def test_every_profile_matches_physical_board(self):
        for profile in PROFILES:
            self.assertEqual(len(profile["keys"]), 12)

    def test_user_shortcut_overrides(self):
        flow_ptt = PROFILES[0]["keys"][0]
        town_open = PROFILES[2]["keys"][0]

        self.assertEqual(flow_ptt["action"], "hold_hotkey")
        self.assertEqual(flow_ptt["keys"], ("OPTION", "W"))
        self.assertEqual(town_open["keys"], ("OPTION", "T"))

    def test_town_navigation_forms_dpad(self):
        town = PROFILES[2]["keys"]
        self.assertEqual(town[2]["keys"], ("ESCAPE",))
        self.assertEqual(town[7]["keys"], ("UP_ARROW",))
        self.assertEqual(
            [binding["keys"] for binding in town[9:12]],
            [("LEFT_ARROW",), ("DOWN_ARROW",), ("RIGHT_ARROW",)],
        )

    def test_town_native_global_shortcuts(self):
        town = PROFILES[2]["keys"]
        self.assertEqual(
            [binding["label"] for binding in town[:6]],
            ["QUICK", "FOCUS", "ESC", "HOME", "SECT", "FULL"],
        )
        self.assertEqual(town[1]["keys"], ("OPTION", "SHIFT", "T"))
        self.assertEqual(town[3]["keys"], ("OPTION", "H"))
        self.assertEqual(town[4]["keys"], ("OPTION", "S"))
        self.assertEqual(town[5]["keys"], ("OPTION", "F"))

    def test_flow_hands_free_double_taps_ptt(self):
        hands_free = PROFILES[0]["keys"][1]
        self.assertEqual(hands_free["action"], "double_tap_hotkey")
        self.assertEqual(hands_free["keys"], ("OPTION", "W"))

    def test_flow_third_row_right_is_enter(self):
        enter = PROFILES[0]["keys"][8]
        self.assertEqual(enter["label"], "ENTER")
        self.assertEqual(enter["keys"], ("ENTER",))

    def test_codex_profile_matches_requested_layout(self):
        codex = PROFILES[1]["keys"]
        self.assertEqual(
            [binding["label"] for binding in codex],
            [
                "CMD", "VOICE", "ESC",
                "BACK", "FWD", "ENTER",
                "NEW", "UP", "TERM",
                "LEFT", "DOWN", "RIGHT",
            ],
        )
        self.assertEqual(codex[0]["keys"], ("COMMAND", "SHIFT", "P"))
        self.assertEqual(codex[1]["keys"], ("CONTROL", "SHIFT", "D"))
        self.assertEqual(codex[3]["keys"], ("COMMAND", "LEFT_BRACKET"))
        self.assertEqual(codex[4]["keys"], ("COMMAND", "RIGHT_BRACKET"))
        self.assertEqual(codex[6]["keys"], ("COMMAND", "N"))
        self.assertEqual(codex[7]["keys"], ("UP_ARROW",))
        self.assertEqual(codex[8]["keys"], ("CONTROL", "GRAVE_ACCENT"))
        self.assertEqual(
            [binding["keys"] for binding in codex[9:]],
            [("LEFT_ARROW",), ("DOWN_ARROW",), ("RIGHT_ARROW",)],
        )

    def test_music_profile_uses_consumer_controls(self):
        music = PROFILES[3]["keys"]
        self.assertEqual(
            [binding["code"] for binding in music[:3]],
            ["SCAN_PREVIOUS_TRACK", "PLAY_PAUSE", "SCAN_NEXT_TRACK"],
        )

    def test_validation_catches_wrong_key_count(self):
        invalid_profile = dict(PROFILES[0])
        invalid_profile["keys"] = invalid_profile["keys"][:-1]
        self.assertIn(
            "profile 0 must contain exactly 12 keys",
            validate_profiles((invalid_profile,)),
        )


if __name__ == "__main__":
    unittest.main()
