"""User-editable profiles for the AI MacroPad."""


def hotkey(label, *keys, hold=False):
    """Create a tap or hold keyboard binding."""
    return {
        "label": label,
        "action": "hold_hotkey" if hold else "tap_hotkey",
        "keys": keys,
    }


def tap_or_long_hotkey(label, tap_keys, long_keys):
    """Create a binding with distinct short- and long-press chords."""
    return {
        "label": label,
        "action": "tap_or_long_hotkey",
        "tap_keys": tap_keys,
        "long_keys": long_keys,
    }


def enter_key():
    """Create the shared Enter key used by non-music profiles."""
    return tap_or_long_hotkey(
        "ENTER",
        ("ENTER",),
        ("COMMAND", "ENTER"),
    )


def consumer(label, code):
    """Create a USB consumer-control binding."""
    return {"label": label, "action": "consumer", "code": code}


def text(label, value):
    """Create a binding that types literal text."""
    return {"label": label, "action": "type_text", "text": value}


def unused():
    """Create an intentionally unassigned key."""
    return {"label": "----", "action": "noop"}


def navigation_pad():
    """Create the shared navigation rows used by non-music profiles."""
    return (
        hotkey("BACK", "COMMAND", "LEFT_BRACKET"),
        hotkey("UP", "UP_ARROW"),
        hotkey("FWD", "COMMAND", "RIGHT_BRACKET"),
        hotkey("LEFT", "LEFT_ARROW"),
        hotkey("DOWN", "DOWN_ARROW"),
        hotkey("RIGHT", "RIGHT_ARROW"),
    )


PROFILES = (
    {
        "name": "WISPR FLOW",
        "color": (132, 62, 255),
        "keys": (
            # User-configured Flow push-to-talk shortcut.
            hotkey("PTT", "OPTION", "W", hold=True),
            {
                "label": "FREE",
                "action": "double_tap_hotkey",
                "keys": ("OPTION", "W"),
                "mode_toggle": "flow_free",
            },
            {
                "label": "ESC",
                "action": "tap_hotkey",
                "keys": ("ESCAPE",),
                "mode_clear": ("flow_free",),
            },
            enter_key(),
            hotkey("COPY", "COMMAND", "CONTROL", "C"),
            hotkey("PASTE", "COMMAND", "CONTROL", "V"),
        ) + navigation_pad(),
    },
    {
        "name": "CODEX",
        "color": (255, 255, 255),
        "keys": (
            hotkey("FOCUS", "CONTROL", "THREE"),
            {
                "label": "VOICE",
                "action": "tap_hotkey",
                "keys": ("OPTION", "C"),
                "mode_toggle": "codex_voice",
            },
            {
                "label": "ESC",
                "action": "tap_hotkey",
                "keys": ("ESCAPE",),
                "mode_clear": ("codex_voice",),
            },
            enter_key(),
            hotkey("CMD", "COMMAND", "SHIFT", "P"),
            hotkey("TERM", "CONTROL", "GRAVE_ACCENT"),
        ) + navigation_pad(),
    },
    {
        "name": "TOWN",
        "color": (0, 190, 120),
        "keys": (
            # User-configured Town global spotlight shortcut.
            hotkey("QUICK", "OPTION", "T"),
            hotkey("FOCUS", "OPTION", "SHIFT", "T"),
            hotkey("ESC", "ESCAPE"),
            enter_key(),
            hotkey("SECT", "OPTION", "S"),
            hotkey("FULL", "OPTION", "F"),
        ) + navigation_pad(),
    },
    {
        "name": "MEDIA",
        "color": (255, 80, 0),
        "keys": (
            consumer("PREV", "SCAN_PREVIOUS_TRACK"),
            consumer("PLAY", "PLAY_PAUSE"),
            consumer("NEXT", "SCAN_NEXT_TRACK"),
            consumer("RW", "REWIND"),
            consumer("STOP", "STOP"),
            consumer("FF", "FAST_FORWARD"),
            consumer("VOL-", "VOLUME_DECREMENT"),
            consumer("MUTE", "MUTE"),
            consumer("VOL+", "VOLUME_INCREMENT"),
            consumer("DIM", "BRIGHTNESS_DECREMENT"),
            unused(),
            consumer("BRIT", "BRIGHTNESS_INCREMENT"),
        ),
    },
)

PIXEL_BRIGHTNESS = 0.14
PRESS_BRIGHTNESS = 2.25
DOUBLE_TAP_GAP_SECONDS = 0.12
LONG_PRESS_SECONDS = 0.5
PULSE_PERIOD_SECONDS = 1.5
PULSE_MIN_FACTOR = 0.25
PULSE_UPDATE_SECONDS = 0.03


def validate_profiles(profiles=PROFILES):
    """Return human-readable configuration errors."""
    errors = []
    valid_actions = (
        "hold_hotkey",
        "tap_hotkey",
        "tap_or_long_hotkey",
        "double_tap_hotkey",
        "consumer",
        "type_text",
        "noop",
    )

    if not profiles:
        errors.append("PROFILES must contain at least one profile")

    for profile_index, profile in enumerate(profiles):
        profile_prefix = "profile {}".format(profile_index)
        name = profile.get("name", "")
        keys = profile.get("keys", ())

        if not name:
            errors.append("{} must define a name".format(profile_prefix))
        if len(keys) != 12:
            errors.append("{} must contain exactly 12 keys".format(profile_prefix))

        color = profile.get("color")
        if (
            not isinstance(color, tuple)
            or len(color) != 3
            or any(channel < 0 or channel > 255 for channel in color)
        ):
            errors.append("{} color must be an RGB tuple".format(profile_prefix))

        for key_index, binding in enumerate(keys):
            key_prefix = "{} key {}".format(profile_prefix, key_index)
            label = binding.get("label", "")
            action = binding.get("action")

            if not label or len(label) > 5:
                errors.append("{} label must contain 1-5 characters".format(key_prefix))
            if action not in valid_actions:
                errors.append("{} has unsupported action {!r}".format(key_prefix, action))
            if action in ("hold_hotkey", "tap_hotkey", "double_tap_hotkey"):
                if not binding.get("keys"):
                    errors.append("{} must define keys".format(key_prefix))
            if action == "tap_or_long_hotkey":
                if not binding.get("tap_keys"):
                    errors.append("{} must define tap_keys".format(key_prefix))
                if not binding.get("long_keys"):
                    errors.append("{} must define long_keys".format(key_prefix))
            if action == "consumer" and not binding.get("code"):
                errors.append("{} must define code".format(key_prefix))
            if action == "type_text" and not binding.get("text"):
                errors.append("{} must define text".format(key_prefix))

    return errors
