"""AI-focused firmware for the Adafruit MacroPad RP2040."""

import time

from adafruit_macropad import MacroPad

from config import (
    KEYMAP,
    PIXEL_BRIGHTNESS,
    PRESS_BRIGHTNESS,
    ROW_TITLES,
    SPOTLIGHT_DELAY_SECONDS,
    validate_keymap,
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


def show_layout():
    """Render one compact line for each physical key row."""
    lines = macropad.display_text(title="AI MACROPAD")
    for row, title in enumerate(ROW_TITLES):
        first = row * 3
        labels = [KEYMAP[first + column]["label"] for column in range(3)]
        lines[row].text = "{:<5} {:<4} {:<4} {:<4}".format(
            title, labels[0], labels[1], labels[2]
        )
    lines.show()


def open_app(app_name):
    """Open a macOS app through Spotlight without desktop-side software."""
    macropad.keyboard.send(macropad.Keycode.GUI, macropad.Keycode.SPACE)
    time.sleep(SPOTLIGHT_DELAY_SECONDS)
    macropad.keyboard_layout.write(app_name)
    time.sleep(SPOTLIGHT_DELAY_SECONDS)
    macropad.keyboard.send(macropad.Keycode.ENTER)


def press_key(index):
    """Run the configured press action for a physical key."""
    binding = KEYMAP[index]
    action = binding["action"]
    macropad.pixels[index] = brighten(binding["color"])

    if action == "hold_hotkey":
        macropad.keyboard.press(*resolve_keycodes(binding["keys"]))
    elif action == "tap_hotkey":
        macropad.keyboard.send(*resolve_keycodes(binding["keys"]))
    elif action == "launch_app":
        open_app(binding["app"])
    elif action == "consumer":
        code = getattr(macropad.ConsumerControlCode, binding["code"])
        macropad.consumer_control.send(code)


def release_key(index):
    """Release held chords and restore the key's idle color."""
    binding = KEYMAP[index]
    if binding["action"] == "hold_hotkey":
        macropad.keyboard.release(*resolve_keycodes(binding["keys"]))
    macropad.pixels[index] = binding["color"]


configuration_errors = validate_keymap()
if configuration_errors:
    raise ValueError("; ".join(configuration_errors))

macropad.pixels.brightness = PIXEL_BRIGHTNESS
for key_number, key_binding in enumerate(KEYMAP):
    macropad.pixels[key_number] = key_binding["color"]

show_layout()
last_encoder_position = macropad.encoder

while True:
    key_event = macropad.keys.events.get()
    if key_event:
        if key_event.pressed:
            press_key(key_event.key_number)
        else:
            release_key(key_event.key_number)

    macropad.encoder_switch_debounced.update()
    if macropad.encoder_switch_debounced.pressed:
        macropad.consumer_control.send(macropad.ConsumerControlCode.MUTE)

    encoder_position = macropad.encoder
    encoder_delta = encoder_position - last_encoder_position
    if encoder_delta:
        volume_code = (
            macropad.ConsumerControlCode.VOLUME_INCREMENT
            if encoder_delta > 0
            else macropad.ConsumerControlCode.VOLUME_DECREMENT
        )
        for _ in range(abs(encoder_delta)):
            macropad.consumer_control.send(volume_code)
        last_encoder_position = encoder_position

    time.sleep(0.005)
