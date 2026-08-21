"""Profile-based AI firmware for the Adafruit MacroPad RP2040."""

import time

from adafruit_macropad import MacroPad

from config import (
    DOUBLE_TAP_GAP_SECONDS,
    LONG_PRESS_SECONDS,
    PIXEL_BRIGHTNESS,
    PRESS_BRIGHTNESS,
    PROFILES,
    PULSE_MIN_FACTOR,
    PULSE_PERIOD_SECONDS,
    PULSE_UPDATE_SECONDS,
    validate_profiles,
)


macropad = MacroPad()

KEYCODE_ALIASES = {
    "COMMAND": "GUI",
    "OPTION": "ALT",
}


def resolve_keycodes(names):
    """Convert readable config names to adafruit_hid Keycode values."""
    return tuple(
        getattr(macropad.Keycode, KEYCODE_ALIASES.get(name, name)) for name in names
    )


def brighten(color):
    """Return a brighter RGB color without overflowing a channel."""
    return tuple(min(255, int(channel * PRESS_BRIGHTNESS)) for channel in color)


def set_profile(profile_index):
    """Update the OLED and LEDs for the selected profile."""
    profile = PROFILES[profile_index]
    title = "{}/{}  {}".format(
        profile_index + 1, len(PROFILES), profile["name"]
    )
    display_lines[0].text = "{:<21}".format(title)

    for row in range(4):
        first = row * 3
        labels = [profile["keys"][first + column]["label"] for column in range(3)]
        display_lines[row + 1].text = "{:<5} {:<5} {:<5}".format(
            labels[0], labels[1], labels[2]
        )

    display_lines.show()
    macropad.pixels.fill(profile["color"])


def tap_hotkey(names):
    """Send one keyboard chord."""
    macropad.keyboard.send(*resolve_keycodes(names))


def press_key(index):
    """Run the active profile's configured press action."""
    binding = PROFILES[active_profile]["keys"][index]
    action = binding["action"]
    macropad.pixels[index] = brighten(PROFILES[active_profile]["color"])

    if action == "hold_hotkey":
        keycodes = resolve_keycodes(binding["keys"])
        held_keycodes[index] = keycodes
        macropad.keyboard.press(*keycodes)
    elif action == "tap_or_long_hotkey":
        pending_long_presses[index] = (time.monotonic(), binding)
    elif action == "tap_hotkey":
        tap_hotkey(binding["keys"])
    elif action == "double_tap_hotkey":
        tap_hotkey(binding["keys"])
        time.sleep(DOUBLE_TAP_GAP_SECONDS)
        tap_hotkey(binding["keys"])
    elif action == "consumer":
        code = getattr(macropad.ConsumerControlCode, binding["code"])
        macropad.consumer_control.send(code)
    elif action == "type_text":
        macropad.keyboard_layout.write(binding["text"])

    mode_toggle = binding.get("mode_toggle")
    if mode_toggle:
        if mode_toggle in active_mode_indicators:
            active_mode_indicators.pop(mode_toggle)
        else:
            active_mode_indicators[mode_toggle] = True

    for mode_name in binding.get("mode_clear", ()):
        active_mode_indicators.pop(mode_name, None)


def release_key(index):
    """Release held chords and restore the profile color."""
    pending = pending_long_presses.pop(index, None)
    if pending:
        tap_hotkey(pending[1]["tap_keys"])
    if index in held_keycodes:
        macropad.keyboard.release(*held_keycodes.pop(index))
    macropad.pixels[index] = PROFILES[active_profile]["color"]


def service_long_presses():
    """Fire each long-press chord once when its threshold is reached."""
    now = time.monotonic()
    for index in tuple(pending_long_presses):
        started_at, binding = pending_long_presses[index]
        if now - started_at >= LONG_PRESS_SECONDS:
            pending_long_presses.pop(index)
            tap_hotkey(binding["long_keys"])


def service_mode_indicator(last_update):
    """Pulse all key LEDs while an app mode is locally marked active."""
    now = time.monotonic()
    if now - last_update < PULSE_UPDATE_SECONDS:
        return last_update

    if active_mode_indicators:
        phase = (now % PULSE_PERIOD_SECONDS) / PULSE_PERIOD_SECONDS
        triangle = 1.0 - abs((phase * 2.0) - 1.0)
        factor = PULSE_MIN_FACTOR + ((1.0 - PULSE_MIN_FACTOR) * triangle)
        macropad.pixels.brightness = PIXEL_BRIGHTNESS * factor
    else:
        macropad.pixels.brightness = PIXEL_BRIGHTNESS

    return now


configuration_errors = validate_profiles()
if configuration_errors:
    raise ValueError("; ".join(configuration_errors))

macropad.pixels.brightness = PIXEL_BRIGHTNESS
display_lines = macropad.display_text()
display_lines[0].color = 0x000000
display_lines[0].background_color = 0xFFFFFF
held_keycodes = {}
pending_long_presses = {}
active_mode_indicators = {}
active_profile = 0
last_encoder_position = macropad.encoder
last_pulse_update = 0.0
set_profile(active_profile)

while True:
    key_event = macropad.keys.events.get()
    if key_event:
        if key_event.pressed:
            press_key(key_event.key_number)
        else:
            release_key(key_event.key_number)

    service_long_presses()
    last_pulse_update = service_mode_indicator(last_pulse_update)

    encoder_position = macropad.encoder
    encoder_delta = encoder_position - last_encoder_position
    if encoder_delta:
        macropad.keyboard.release_all()
        held_keycodes.clear()
        pending_long_presses.clear()
        active_profile = (active_profile + encoder_delta) % len(PROFILES)
        last_encoder_position = encoder_position
        set_profile(active_profile)

    time.sleep(0.005)
