"""Profile-based AI firmware for the Adafruit MacroPad RP2040."""

import board
import displayio
import time
import usb_cdc
import vectorio

from adafruit_macropad import MacroPad

from config import (
    DOUBLE_TAP_GAP_SECONDS,
    ENCODER_LEFT_ARROW_POINTS,
    ENCODER_PRESSED_LEFT_KEYS,
    ENCODER_PRESSED_RIGHT_KEYS,
    ENCODER_RIGHT_ARROW_POINTS,
    LONG_PRESS_SECONDS,
    MEDIA_VISUALIZER_GAIN,
    MEDIA_VISUALIZER_ROW_COLORS,
    MEDIA_SCROLL_UPDATE_SECONDS,
    PIXEL_BRIGHTNESS,
    PRESS_BRIGHTNESS,
    PROFILES,
    PULSE_MIN_FACTOR,
    PULSE_PERIOD_SECONDS,
    PULSE_UPDATE_SECONDS,
    SPOTIFY_LEVEL_STALE_SECONDS,
    SPOTIFY_STALE_SECONDS,
    validate_profiles,
)
from spotify_protocol import (
    DISPLAY_WIDTH,
    PlaybackPauseController,
    equalizer_pixels,
    parse_audio_level_message,
    parse_message,
    playback_is_active,
    playback_display_rows,
    scrolling_display_text,
    transport_label,
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


def dim(color, factor):
    """Scale an RGB color for an unlit equalizer spot."""
    return tuple(int(channel * factor) for channel in color)


def set_profile(profile_index):
    """Update the OLED and LEDs for the selected profile."""
    profile = PROFILES[profile_index]
    title = "{}/{}  {}".format(
        profile_index + 1, len(PROFILES), profile["name"]
    )
    display_lines[0].text = "{:<21}".format(title.upper())

    playback_rows = None
    if profile["name"] == "MEDIA" and media_info_enabled:
        playback_rows = playback_display_rows(spotify_playback)

    if playback_rows:
        for row, text in enumerate(playback_rows):
            display_lines[row + 1].text = scrolling_display_text(
                text, media_scroll_step
            )
    else:
        for row in range(4):
            first = row * 3
            labels = [
                profile["keys"][first + column]["label"]
                for column in range(3)
            ]
            if profile["name"] == "MEDIA" and first == 0:
                labels[1] = transport_label(spotify_playback)
            elif profile["name"] == "MEDIA" and first == 6:
                labels[0] = "UNLNK" if auto_pause_enabled else "LINK"
            display_lines[row + 1].text = "{:<5} {:<5} {:<5}".format(
                labels[0], labels[1], labels[2]
            )

    display_lines.show()
    macropad.pixels.fill(profile["color"])


def show_encoder_navigation():
    """Replace the OLED keymap with large navigation chevrons."""
    board.DISPLAY.root_group = encoder_navigation_group


def tap_hotkey(names):
    """Send one keyboard chord."""
    macropad.keyboard.send(*resolve_keycodes(names))


def send_encoder_navigation(delta):
    """Send one Control+Arrow chord per pressed encoder step."""
    keys = ENCODER_PRESSED_RIGHT_KEYS if delta > 0 else ENCODER_PRESSED_LEFT_KEYS
    for _ in range(abs(delta)):
        tap_hotkey(keys)


def toggle_media_playback():
    """Send the native play/pause consumer-control command."""
    macropad.consumer_control.send(macropad.ConsumerControlCode.PLAY_PAUSE)


def begin_media_pause(owner):
    """Pause active playback for the first voice-mode owner."""
    if not auto_pause_enabled:
        return
    if media_pause_controller.begin(owner, playback_is_active(spotify_playback)):
        toggle_media_playback()


def end_media_pause(owner):
    """Resume playback after the final voice-mode owner ends."""
    if media_pause_controller.end(owner):
        toggle_media_playback()


def release_held_media_pauses():
    """Release every PTT pause owner, such as during profile changes."""
    for owner in tuple(held_media_pause_owners.values()):
        end_media_pause(owner)
    held_media_pause_owners.clear()


def toggle_auto_pause():
    """Toggle voice-mode playback linking and synchronize current state."""
    global auto_pause_enabled

    auto_pause_enabled = not auto_pause_enabled
    if auto_pause_enabled:
        for mode_name in active_mode_indicators:
            begin_media_pause("mode:{}".format(mode_name))
    else:
        held_media_pause_owners.clear()
        if media_pause_controller.cancel():
            toggle_media_playback()


def press_key(index):
    """Run the active profile's configured press action."""
    global media_info_enabled, media_scroll_step

    binding = PROFILES[active_profile]["keys"][index]
    action = binding["action"]
    pause_policy = binding.get("media_pause")
    mode_toggle = binding.get("mode_toggle")
    mode_activating = (
        mode_toggle is not None
        and mode_toggle not in active_mode_indicators
    )

    if pause_policy == "while_held":
        owner = "held:{}:{}".format(active_profile, index)
        held_media_pause_owners[index] = owner
        begin_media_pause(owner)
    elif pause_policy == "while_active" and mode_activating:
        begin_media_pause("mode:{}".format(mode_toggle))

    pulse_while_held = binding.get("pulse_while_held")
    if pulse_while_held:
        held_pulse_indicators[index] = pulse_while_held

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
    elif action == "toggle_auto_pause":
        toggle_auto_pause()
        set_profile(active_profile)
    elif action == "toggle_media_display":
        media_info_enabled = not media_info_enabled
        if media_info_enabled:
            media_scroll_step = 0
        set_profile(active_profile)

    if mode_toggle:
        if mode_toggle in active_mode_indicators:
            active_mode_indicators.pop(mode_toggle)
            if pause_policy == "while_active":
                end_media_pause("mode:{}".format(mode_toggle))
        else:
            active_mode_indicators[mode_toggle] = True

    for mode_name in binding.get("mode_clear", ()):
        active_mode_indicators.pop(mode_name, None)
        end_media_pause("mode:{}".format(mode_name))


def release_key(index):
    """Release held chords and restore the profile color."""
    pending = pending_long_presses.pop(index, None)
    if pending:
        tap_hotkey(pending[1]["tap_keys"])
    if index in held_keycodes:
        macropad.keyboard.release(*held_keycodes.pop(index))
    held_pause_owner = held_media_pause_owners.pop(index, None)
    if held_pause_owner:
        end_media_pause(held_pause_owner)
    held_pulse_indicators.pop(index, None)
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

    media_playing = (
        PROFILES[active_profile]["name"] == "MEDIA"
        and playback_is_active(spotify_playback)
    )
    if media_playing:
        macropad.pixels.brightness = PIXEL_BRIGHTNESS
        levels = spotify_audio_levels
        if now - last_spotify_level_update > SPOTIFY_LEVEL_STALE_SECONDS:
            levels = (0.0, 0.0, 0.0)
        for index, illuminated in enumerate(
            equalizer_pixels(levels, MEDIA_VISUALIZER_GAIN)
        ):
            row_color = MEDIA_VISUALIZER_ROW_COLORS[index // 3]
            macropad.pixels[index] = (
                row_color if illuminated else dim(row_color, 0.06)
            )
    elif active_mode_indicators or held_pulse_indicators:
        phase = (now % PULSE_PERIOD_SECONDS) / PULSE_PERIOD_SECONDS
        triangle = 1.0 - abs((phase * 2.0) - 1.0)
        factor = PULSE_MIN_FACTOR + ((1.0 - PULSE_MIN_FACTOR) * triangle)
        macropad.pixels.brightness = PIXEL_BRIGHTNESS * factor
    else:
        macropad.pixels.brightness = PIXEL_BRIGHTNESS

    return now


def apply_spotify_message(line):
    """Update cached playback state from one complete relay message."""
    global last_spotify_update, media_scroll_step, spotify_playback

    playback = parse_message(line)
    if playback is None:
        return
    previous_track = None
    if spotify_playback:
        previous_track = (
            spotify_playback.get("artist"),
            spotify_playback.get("album"),
            spotify_playback.get("title"),
        )
    current_track = (
        playback.get("artist"),
        playback.get("album"),
        playback.get("title"),
    )
    if current_track != previous_track:
        media_scroll_step = 0
    spotify_playback = playback
    last_spotify_update = time.monotonic()
    if PROFILES[active_profile]["name"] == "MEDIA" and not encoder_navigation_active:
        set_profile(active_profile)


def service_spotify_serial():
    """Consume pending metadata without blocking the key event loop."""
    global last_spotify_level_update, spotify_audio_levels
    global spotify_playback, spotify_serial_buffer

    if spotify_serial is not None and spotify_serial.in_waiting:
        data = spotify_serial.read(spotify_serial.in_waiting)
        if data:
            spotify_serial_buffer += data.decode("ascii")
            while "\n" in spotify_serial_buffer:
                line, spotify_serial_buffer = spotify_serial_buffer.split("\n", 1)
                audio_levels = parse_audio_level_message(line)
                if audio_levels is None:
                    apply_spotify_message(line)
                else:
                    spotify_audio_levels = audio_levels
                    last_spotify_level_update = time.monotonic()

    if (
        spotify_playback
        and spotify_playback.get("state") == "playing"
        and time.monotonic() - last_spotify_update > SPOTIFY_STALE_SECONDS
    ):
        spotify_playback = None
        if PROFILES[active_profile]["name"] == "MEDIA" and not encoder_navigation_active:
            set_profile(active_profile)


def service_media_scroll(last_update):
    """Advance overflowing Spotify rows without blocking key input."""
    global media_scroll_step

    now = time.monotonic()
    if now - last_update < MEDIA_SCROLL_UPDATE_SECONDS:
        return last_update
    if (
        PROFILES[active_profile]["name"] != "MEDIA"
        or not media_info_enabled
        or encoder_navigation_active
    ):
        return now

    playback_rows = playback_display_rows(spotify_playback)
    if playback_rows and any(len(text) > DISPLAY_WIDTH for text in playback_rows):
        media_scroll_step += 1
        for row, text in enumerate(playback_rows):
            display_lines[row + 1].text = scrolling_display_text(
                text, media_scroll_step
            )
    return now


configuration_errors = validate_profiles()
if configuration_errors:
    raise ValueError("; ".join(configuration_errors))

macropad.pixels.brightness = PIXEL_BRIGHTNESS
display_lines = macropad.display_text()
display_lines[0].color = 0x000000
display_lines[0].background_color = 0xFFFFFF
encoder_navigation_palette = displayio.Palette(1)
encoder_navigation_palette[0] = 0xFFFFFF
encoder_navigation_group = displayio.Group()
encoder_navigation_group.append(
    vectorio.Polygon(
        pixel_shader=encoder_navigation_palette,
        points=list(ENCODER_LEFT_ARROW_POINTS),
        x=0,
        y=0,
    )
)
encoder_navigation_group.append(
    vectorio.Polygon(
        pixel_shader=encoder_navigation_palette,
        points=list(ENCODER_RIGHT_ARROW_POINTS),
        x=0,
        y=0,
    )
)
held_keycodes = {}
held_media_pause_owners = {}
held_pulse_indicators = {}
pending_long_presses = {}
active_mode_indicators = {}
media_pause_controller = PlaybackPauseController()
auto_pause_enabled = False
spotify_playback = None
spotify_audio_levels = (0.0, 0.0, 0.0)
spotify_serial = usb_cdc.data
spotify_serial_buffer = ""
last_spotify_update = 0.0
last_spotify_level_update = 0.0
media_info_enabled = True
media_scroll_step = 0
active_profile = 0
encoder_navigation_active = False
last_encoder_position = macropad.encoder
last_pulse_update = 0.0
last_media_scroll_update = 0.0
set_profile(active_profile)

while True:
    macropad.encoder_switch_debounced.update()
    if macropad.encoder_switch_debounced.pressed:
        encoder_navigation_active = True
        show_encoder_navigation()
    elif macropad.encoder_switch_debounced.released:
        encoder_navigation_active = False
        set_profile(active_profile)

    key_event = macropad.keys.events.get()
    if key_event:
        if key_event.pressed:
            press_key(key_event.key_number)
        else:
            release_key(key_event.key_number)

    service_long_presses()
    last_pulse_update = service_mode_indicator(last_pulse_update)
    service_spotify_serial()
    last_media_scroll_update = service_media_scroll(last_media_scroll_update)

    encoder_position = macropad.encoder
    encoder_delta = encoder_position - last_encoder_position
    if encoder_delta:
        macropad.keyboard.release_all()
        held_keycodes.clear()
        release_held_media_pauses()
        held_pulse_indicators.clear()
        pending_long_presses.clear()
        last_encoder_position = encoder_position
        if encoder_navigation_active:
            send_encoder_navigation(encoder_delta)
        else:
            active_profile = (active_profile + encoder_delta) % len(PROFILES)
            set_profile(active_profile)

    time.sleep(0.005)
