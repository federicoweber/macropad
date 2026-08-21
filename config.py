"""User-editable key map for the AI MacroPad."""

# Each label must fit in four OLED characters.
# Colors are RGB values shown at low brightness while a key is idle.
KEYMAP = (
    # Row 1: Wispr Flow. Bind these chords in Flow's shortcut settings.
    {
        "label": "PTT",
        "action": "hold_hotkey",
        "keys": ("CONTROL", "OPTION", "F13"),
        "color": (132, 62, 255),
    },
    {
        "label": "FREE",
        "action": "tap_hotkey",
        "keys": ("CONTROL", "OPTION", "F14"),
        "color": (132, 62, 255),
    },
    {
        "label": "CMD",
        "action": "hold_hotkey",
        "keys": ("CONTROL", "OPTION", "F15"),
        "color": (132, 62, 255),
    },
    # Row 2: Codex and ChatGPT.
    {
        "label": "CDX",
        "action": "launch_app",
        "app": "Codex",
        "color": (0, 174, 239),
    },
    {
        "label": "GPT",
        "action": "tap_hotkey",
        "keys": ("OPTION", "SPACE"),
        "color": (0, 174, 239),
    },
    {
        "label": "NEW",
        "action": "tap_hotkey",
        "keys": ("COMMAND", "N"),
        "color": (0, 174, 239),
    },
    # Row 3: Town.
    {
        "label": "OPEN",
        "action": "launch_app",
        "app": "Town",
        "color": (255, 139, 44),
    },
    {
        "label": "LINE",
        "action": "tap_hotkey",
        "keys": ("SHIFT", "ENTER"),
        "color": (255, 139, 44),
    },
    {
        "label": "SEND",
        "action": "tap_hotkey",
        "keys": ("ENTER",),
        "color": (255, 139, 44),
    },
    # Row 4: system media controls.
    {
        "label": "PREV",
        "action": "consumer",
        "code": "SCAN_PREVIOUS_TRACK",
        "color": (61, 214, 123),
    },
    {
        "label": "PLAY",
        "action": "consumer",
        "code": "PLAY_PAUSE",
        "color": (61, 214, 123),
    },
    {
        "label": "NEXT",
        "action": "consumer",
        "code": "SCAN_NEXT_TRACK",
        "color": (61, 214, 123),
    },
)

ROW_TITLES = ("FLOW", "AI", "TOWN", "MUSIC")

PIXEL_BRIGHTNESS = 0.12
PRESS_BRIGHTNESS = 2.0
SPOTLIGHT_DELAY_SECONDS = 0.18


def validate_keymap(keymap=KEYMAP):
    """Return human-readable configuration errors."""
    errors = []
    valid_actions = ("hold_hotkey", "tap_hotkey", "launch_app", "consumer")

    if len(keymap) != 12:
        errors.append("KEYMAP must contain exactly 12 entries")

    for index, key in enumerate(keymap):
        prefix = "key {}".format(index)
        label = key.get("label", "")
        action = key.get("action")

        if not label or len(label) > 4:
            errors.append("{} label must contain 1-4 characters".format(prefix))
        if action not in valid_actions:
            errors.append("{} has unsupported action {!r}".format(prefix, action))
        if action in ("hold_hotkey", "tap_hotkey") and not key.get("keys"):
            errors.append("{} must define keys".format(prefix))
        if action == "launch_app" and not key.get("app"):
            errors.append("{} must define app".format(prefix))
        if action == "consumer" and not key.get("code"):
            errors.append("{} must define code".format(prefix))

        color = key.get("color")
        if (
            not isinstance(color, tuple)
            or len(color) != 3
            or any(channel < 0 or channel > 255 for channel in color)
        ):
            errors.append("{} color must be an RGB tuple".format(prefix))

    return errors
