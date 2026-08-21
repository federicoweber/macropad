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
        self.assertEqual(town[1]["keys"], ("OPTION", "SHIFT", "T"))
        self.assertEqual(town[6]["keys"], ("OPTION", "H"))
        self.assertEqual(town[8]["keys"], ("OPTION", "F"))

    def test_flow_hands_free_double_taps_ptt(self):
        hands_free = PROFILES[0]["keys"][1]
        self.assertEqual(hands_free["action"], "double_tap_hotkey")
        self.assertEqual(hands_free["keys"], ("OPTION", "W"))

    def test_codex_profile_uses_native_new_and_search_shortcuts(self):
        codex = PROFILES[1]["keys"]
        self.assertEqual(codex[1]["keys"], ("COMMAND", "N"))
        self.assertEqual(codex[2]["keys"], ("COMMAND", "G"))

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
