"""Host-side tests for the hardware-independent profiles."""

import unittest

from config import (
    ENCODER_LEFT_ARROW_POINTS,
    ENCODER_PRESSED_LEFT_KEYS,
    ENCODER_PRESSED_RIGHT_KEYS,
    ENCODER_RIGHT_ARROW_POINTS,
    PROFILES,
    PULSE_PERIOD_SECONDS,
    validate_profiles,
)


class ProfileTests(unittest.TestCase):
    def test_default_profiles_are_valid(self):
        self.assertEqual(validate_profiles(), [])

    def test_expected_profiles_exist(self):
        self.assertEqual(
            [profile["name"] for profile in PROFILES],
            ["WISPR FLOW", "CODEX", "TOWN", "MEDIA"],
        )

    def test_profile_colors(self):
        self.assertEqual(
            [profile["color"] for profile in PROFILES],
            [
                (132, 62, 255),
                (255, 255, 255),
                (0, 190, 120),
                (255, 80, 0),
            ],
        )

    def test_conversation_pulse_uses_slow_cycle(self):
        self.assertEqual(PULSE_PERIOD_SECONDS, 4.0)

    def test_every_profile_matches_physical_board(self):
        for profile in PROFILES:
            self.assertEqual(len(profile["keys"]), 12)

    def test_pressed_encoder_navigation_shortcuts(self):
        self.assertEqual(
            ENCODER_PRESSED_LEFT_KEYS,
            ("CONTROL", "LEFT_ARROW"),
        )
        self.assertEqual(
            ENCODER_PRESSED_RIGHT_KEYS,
            ("CONTROL", "RIGHT_ARROW"),
        )

    def test_pressed_encoder_navigation_arrows_fit_display(self):
        self.assertEqual(
            ENCODER_LEFT_ARROW_POINTS[0],
            (43, 11),
        )
        self.assertEqual(
            ENCODER_RIGHT_ARROW_POINTS[0],
            (85, 11),
        )
        for points in (ENCODER_LEFT_ARROW_POINTS, ENCODER_RIGHT_ARROW_POINTS):
            self.assertTrue(all(0 <= x < 128 and 0 <= y < 64 for x, y in points))

    def test_user_shortcut_overrides(self):
        flow_ptt = PROFILES[0]["keys"][0]
        town_open = PROFILES[2]["keys"][0]

        self.assertEqual(flow_ptt["action"], "hold_hotkey")
        self.assertEqual(flow_ptt["keys"], ("OPTION", "W"))
        self.assertEqual(town_open["keys"], ("OPTION", "T"))

    def test_non_media_profiles_share_navigation_pad(self):
        expected_labels = ["BACK", "UP", "FWD", "LEFT", "DOWN", "RIGHT"]
        expected_keys = [
            ("COMMAND", "LEFT_BRACKET"),
            ("UP_ARROW",),
            ("COMMAND", "RIGHT_BRACKET"),
            ("LEFT_ARROW",),
            ("DOWN_ARROW",),
            ("RIGHT_ARROW",),
        ]

        for profile in PROFILES[:3]:
            navigation = profile["keys"][6:]
            self.assertEqual(
                [binding["label"] for binding in navigation],
                expected_labels,
            )
            self.assertEqual(
                [binding["keys"] for binding in navigation],
                expected_keys,
            )

    def test_non_media_profiles_share_enter_position(self):
        for profile in PROFILES[:3]:
            enter = profile["keys"][3]
            self.assertEqual(enter["label"], "ENTER")
            self.assertEqual(enter["action"], "tap_or_long_hotkey")
            self.assertEqual(enter["tap_keys"], ("ENTER",))
            self.assertEqual(enter["long_keys"], ("COMMAND", "ENTER"))

    def test_town_native_global_shortcuts(self):
        town = PROFILES[2]["keys"]
        self.assertEqual(
            [binding["label"] for binding in town[:6]],
            ["QUICK", "FOCUS", "ESC", "ENTER", "SECT", "FULL"],
        )
        self.assertEqual(town[1]["keys"], ("OPTION", "SHIFT", "T"))
        self.assertEqual(town[4]["keys"], ("OPTION", "S"))
        self.assertEqual(town[5]["keys"], ("OPTION", "F"))

    def test_flow_hands_free_double_taps_ptt(self):
        ptt = PROFILES[0]["keys"][0]
        hands_free = PROFILES[0]["keys"][1]
        self.assertEqual(ptt["media_pause"], "while_held")
        self.assertEqual(ptt["pulse_while_held"], "flow_ptt")
        self.assertEqual(hands_free["action"], "double_tap_hotkey")
        self.assertEqual(hands_free["keys"], ("OPTION", "W"))
        self.assertEqual(hands_free["mode_toggle"], "flow_free")
        self.assertEqual(hands_free["media_pause"], "while_active")

    def test_conversation_modes_control_pulse_indicator(self):
        flow = PROFILES[0]["keys"]
        codex = PROFILES[1]["keys"]

        self.assertEqual(flow[2]["mode_clear"], ("flow_free",))
        self.assertEqual(codex[1]["mode_toggle"], "codex_voice")
        self.assertEqual(codex[1]["media_pause"], "while_active")
        self.assertEqual(codex[2]["mode_clear"], ("codex_voice",))

    def test_flow_profile_matches_requested_layout(self):
        flow = PROFILES[0]["keys"]
        self.assertEqual(
            [binding["label"] for binding in flow],
            [
                "PTT", "FREE", "ESC",
                "ENTER", "COPY", "PASTE",
                "BACK", "UP", "FWD",
                "LEFT", "DOWN", "RIGHT",
            ],
        )
        self.assertEqual(flow[2]["keys"], ("ESCAPE",))
        self.assertEqual(flow[3]["action"], "tap_or_long_hotkey")
        self.assertEqual(flow[3]["tap_keys"], ("ENTER",))
        self.assertEqual(flow[3]["long_keys"], ("COMMAND", "ENTER"))

    def test_codex_profile_matches_requested_layout(self):
        codex = PROFILES[1]["keys"]
        self.assertEqual(
            [binding["label"] for binding in codex],
            [
                "CMD", "VOICE", "ESC",
                "ENTER", "NEW", "TERM",
                "BACK", "UP", "FWD",
                "LEFT", "DOWN", "RIGHT",
            ],
        )
        self.assertEqual(codex[0]["keys"], ("COMMAND", "SHIFT", "P"))
        self.assertEqual(codex[1]["keys"], ("OPTION", "C"))
        self.assertEqual(codex[4]["keys"], ("COMMAND", "N"))
        self.assertEqual(codex[5]["keys"], ("CONTROL", "GRAVE_ACCENT"))
        self.assertEqual(codex[7]["keys"], ("UP_ARROW",))

    def test_media_profile_uses_consumer_controls(self):
        media = PROFILES[3]["keys"]
        self.assertEqual(
            [binding["label"] for binding in media],
            [
                "PREV", "PLAY", "NEXT",
                "VOL-", "MUTE", "VOL+",
                "LINK", "UP", "INFO",
                "LEFT", "DOWN", "RIGHT",
            ],
        )
        self.assertEqual(
            [binding["code"] for binding in media[:3]],
            ["SCAN_PREVIOUS_TRACK", "PLAY_PAUSE", "SCAN_NEXT_TRACK"],
        )
        self.assertEqual(
            [binding["code"] for binding in media[3:6]],
            ["VOLUME_DECREMENT", "MUTE", "VOLUME_INCREMENT"],
        )
        self.assertEqual(media[6]["action"], "toggle_auto_pause")
        self.assertEqual(media[7]["keys"], ("UP_ARROW",))
        self.assertEqual(media[8]["action"], "toggle_media_display")
        self.assertEqual(media[9]["keys"], ("LEFT_ARROW",))
        self.assertEqual(media[10]["keys"], ("DOWN_ARROW",))
        self.assertEqual(media[11]["keys"], ("RIGHT_ARROW",))

    def test_validation_catches_wrong_key_count(self):
        invalid_profile = dict(PROFILES[0])
        invalid_profile["keys"] = invalid_profile["keys"][:-1]
        self.assertIn(
            "profile 0 must contain exactly 12 keys",
            validate_profiles((invalid_profile,)),
        )


if __name__ == "__main__":
    unittest.main()
