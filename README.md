# AI MacroPad

Profile-based CircuitPython firmware for the [Adafruit MacroPad RP2040 Starter
Kit](https://www.adafruit.com/product/5128), designed for an AI-heavy macOS
workflow.

Turn the encoder to switch between Wispr Flow, Codex, Town, and Media. Hold the
encoder down while turning it to send `Control+Left` counterclockwise or
`Control+Right` clockwise. While held, the OLED replaces the keymap with two
large navigation chevrons; releasing the encoder restores the same selected
profile. The OLED normally shows the active profile in an inverted title bar
and its 3×4 keymap, while all 12 NeoPixels change to the profile color. The
firmware appears to macOS as a standard USB keyboard and media controller.
Keyboard and media controls need no desktop helper; Spotify metadata uses the
optional local relay described below.

## Profiles

Hold the board upright with the OLED and encoder above the keys.

The bottom two rows are a shared navigation pad in Wispr Flow, Codex, and Town.
Media keeps its dedicated controls.

The full key backlight uses a slow four-second breathing cycle while Wispr Flow
PTT is held, or while Wispr Flow hands-free mode or Codex Voice Mode is locally
marked active. Press `FREE` or `VOICE` to toggle its mode; press that profile's
`ESC` to clear it. The indicator remains visible when the encoder switches
profiles.

If Spotify is playing, starting Wispr Flow `PTT` or `FREE`, or Codex `VOICE`,
automatically pauses playback. PTT resumes it on release; FREE and VOICE resume
it when toggled off or cleared with `ESC`. Overlapping modes keep playback
paused until the final active mode ends.

### 1. WISPR FLOW — purple

| Left | Middle | Right |
|------|--------|-------|
| `PTT` Push to talk | `FREE` Hands-free | `ESC` Cancel/dismiss |
| `ENTER` Submit | `COPY` Copy last | `PASTE` Paste last |
| `BACK` Navigate back | `UP` Up | `FWD` Navigate forward |
| `LEFT` Left | `DOWN` Down | `RIGHT` Right |

`PTT` holds `Option+W`, matching the user-configured Flow shortcut. `FREE`
double-taps the same shortcut, which Flow interprets as hands-free mode. A quick
press on `ENTER` sends `Enter`; holding it for 0.5 seconds sends `Command+Enter`.
This Enter behavior is shared by Wispr Flow, Codex, and Town.

The remaining shortcuts use Flow's current native bindings:

- Cancel: `Escape`
- Paste/copy last transcript: `Command+Control+V/C`
- Submit: `Enter` (tap) or `Command+Enter` (long press)
- Hub back/forward: `Command+[` / `Command+]`

### 2. CODEX — blue

| Left | Middle | Right |
|------|--------|-------|
| `CMD` Command menu | `VOICE` Voice Mode | `ESC` Dismiss |
| `ENTER` Submit | `NEW` New chat | `TERM` Terminal |
| `BACK` Navigate back | `UP` Up | `FWD` Navigate forward |
| `LEFT` Left | `DOWN` Down | `RIGHT` Right |

`VOICE` sends `Option+C`, matching the user-verified Codex Voice Mode shortcut.
`CMD` sends `Command+Shift+P`, while `NEW` sends `Command+N`. The command menu,
new-chat, terminal, and back/forward actions use Codex's native shortcuts. The
final two rows provide the shared navigation pad.

Because the MacroPad cannot read app state from macOS, the pulse tracks button
presses rather than querying Wispr Flow or Codex. If a mode is stopped elsewhere,
press its mode button or `ESC` once to synchronize the indicator.

### 3. TOWN — teal

| Left | Middle | Right |
|------|--------|-------|
| `QUICK` Quick Town | `FOCUS` Focus Town window | `ESC` Dismiss |
| `ENTER` Select | `SECT` Capture selection | `FULL` Capture full screen |
| `BACK` Navigate back | `UP` Up | `FWD` Navigate forward |
| `LEFT` Left | `DOWN` Down | `RIGHT` Right |

`QUICK` sends `Option+T`, `FOCUS` sends `Option+Shift+T`, `SECT` sends `Option+S`,
and `FULL` sends `Option+F`. The final two rows form a navigation D-pad.

### 4. MEDIA — white

| Left | Middle | Right |
|------|--------|-------|
| `PREV` Previous | `PLAY`/`PAUSE` | `NEXT` Next |
| `VOL-` Volume down | `MUTE` Mute | `VOL+` Volume up |
| `UNLNK`/`LINK` Auto-pause | `UP` Up | `INFO` Toggle OLED view |
| `LEFT` Left | `DOWN` Down | `RIGHT` Right |

Media uses native USB consumer-control commands and works without app-specific
configuration. While Spotify is playing, the OLED shows the artist, album,
song, and elapsed/total playback time. Artist, album, and song lines that exceed
the display width automatically scroll from their beginning to their end.
Press `INFO` to toggle between that view and the Media keymap. If Spotify is
paused, stopped, or unavailable, the keymap remains visible. In the keymap
view, the center transport label changes to `PAUSE` while Spotify is playing
and returns to `PLAY` otherwise.

While Spotify is playing and Media is selected, the 3×4 white key grid becomes
a three-band visualizer. The columns represent bass, mid, and treble, and each
four-spot bar grows upward from the bottom in time with Spotify's actual audio.
The bars transition from green at the bottom through yellow and orange to red
at the top. The default reduced gain keeps typical tracks from saturating the
full columns. Unfilled spots retain a dim version of their spectrum color, so
the red top row remains visible between peaks. When playback stops, all 12 keys
return to steady white at the normal profile brightness.

Automatic pausing starts unlinked after boot, so the button initially shows
`LINK`. Press it to enable the behavior; the label changes to `UNLNK`, which
disables it again.

## Spotify now playing

`spotify_relay.py` reads Spotify's native macOS playback metadata and sends it
to the MacroPad over a second USB serial channel. A local Swift helper captures
only Spotify's system-audio output and sends three frequency-band levels 30
times per second for the Media LED animation. The integration stays local and does
not need Spotify API credentials or an OAuth login.

After installing the host requirements and deploying the firmware, run the
relay in a terminal:

```sh
.venv/bin/python spotify_relay.py
```

macOS may ask whether Python can control Spotify the first time. Allow that
request so the relay can read the current track. macOS may also ask for Screen
& System Audio Recording access for **AI MacroPad Spotify Audio Meter**; allow
it so the LEDs can react to Spotify's audio. To start the relay automatically
at login, copy the included launch agent and load it:

```sh
cp launchd/com.federicoweber.ai-macropad-spotify.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.federicoweber.ai-macropad-spotify.plist
```

The launch agent paths assume this repository is located at
`/Users/federico/fwd_projects/ai-macropad`.

## Install

1. Install the latest stable CircuitPython release for the
   [Adafruit MacroPad RP2040](https://circuitpython.org/board/adafruit_macropad_rp2040/).
   The board should mount as `CIRCUITPY`.
2. Create a host environment with Python 3.10 or newer and install CircUp:

   ```sh
   python3.13 -m venv .venv
   .venv/bin/python -m pip install -r requirements-host.txt
   ```

3. Install the board libraries and deploy the firmware:

   ```sh
   make install CIRCUP=.venv/bin/circup
   ```

4. Request Spotify-only audio capture access for the visualizer:

   ```sh
   open .build/SpotifyAudioMeter.app --args --request-permission
   ```

   Choose **Allow** when macOS asks for Screen & System Audio Recording access.

If the board is mounted somewhere other than `/Volumes/CIRCUITPY`, add
`CIRCUITPY=/path/to/CIRCUITPY` to the `make` command.

CircuitPython reloads `code.py` automatically. Turn the encoder to verify that
the OLED, labels, and LEDs cycle through all four profiles.

## Configure shortcuts

The firmware assumes these two user-selected global bindings:

- Wispr Flow push to talk: `Option+W`
- Town spotlight: `Option+T`

Set the Flow binding under **Settings → General → Shortcuts**. Set Town's global
shortcut to `Option+T`. All other bindings are native defaults; if an app's
shortcut has been customized, update the matching entry in `config.py`.

## Customize

Profiles, labels, colors, and bindings live in `config.py`. Each profile must
contain exactly 12 keys, and OLED labels must be one to five characters.
Supported actions are:

- `hold_hotkey`: hold a chord until the physical key is released
- `tap_hotkey`: tap a chord once
- `double_tap_hotkey`: tap a chord twice
- `tap_or_long_hotkey`: send different chords for a tap and a long press
- `consumer`: send a USB media-control code
- `type_text`: type literal text
- `toggle_auto_pause`: link or unlink playback from voice modes
- `toggle_media_display`: switch the Media OLED between key and playback views
- `noop`: intentionally leave a key unused

Run the host checks and deploy changes with:

```sh
make check
make deploy
```

## Project structure

```text
boot.py                 Enables the second USB serial channel
code.py                 Profile switching and hardware event loop
config.py               Profiles, key bindings, labels, and colors
spotify_protocol.py     Shared compact metadata protocol
spotify_relay.py        Local macOS Spotify-to-USB relay
host/SpotifyAudioMeter  Native Spotify-only audio-level helper
launchd/                Optional automatic relay startup
requirements.txt        CircuitPython libraries installed on the board
requirements-host.txt   Host deployment and relay tools
tests/                  Hardware-independent checks
```

## References

- [Adafruit MacroPad RP2040 guide](https://learn.adafruit.com/adafruit-macropad-rp2040)
- [Adafruit MacroPad CircuitPython library](https://learn.adafruit.com/adafruit-macropad-rp2040/macropad-circuitpython-library)
- [Official OpenAI desktop commands](https://learn.chatgpt.com/docs/reference/commands)
- [Wispr Flow desktop shortcuts](https://docs.wisprflow.ai/articles/5096240724-navigating-the-wispr-flow-app-desktop-ios-and-android)
- [Wispr Flow transforms](https://docs.wisprflow.ai/articles/8068950331-how-to-use-transforms-beta)
- [Town assistant keyboard shortcuts](https://www.town.com/docs/using-town/assistant)

## License

MIT
