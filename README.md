# AI MacroPad

Custom CircuitPython firmware for the [Adafruit MacroPad RP2040 Starter
Kit](https://www.adafruit.com/product/5128), organized around an AI-heavy
macOS workflow.

The firmware uses all 12 keys, the OLED, per-key NeoPixels, and the rotary
encoder. It runs entirely on the MacroPad and appears to macOS as a standard
USB keyboard and media controller.

## Default layout

Hold the board upright with the OLED and encoder above the keys.

|             | Left | Middle | Right |
|-------------|------|--------|-------|
| Wispr Flow  | Push to talk | Hands-free | Command mode |
| AI          | Open Codex | Open ChatGPT bar | New chat/task |
| Town        | Open Town | New line | Send |
| Music       | Previous | Play/pause | Next |

The encoder controls volume. Press it to mute or unmute.

### What each key sends

| Key | OLED | Behavior |
|-----|------|----------|
| 1 | `PTT` | Holds `Control+Option+F13` |
| 2 | `FREE` | Taps `Control+Option+F14` |
| 3 | `CMD` | Holds `Control+Option+F15` |
| 4 | `CDX` | Opens Codex through Spotlight |
| 5 | `GPT` | Opens the ChatGPT Chat Bar with `Option+Space` |
| 6 | `NEW` | Sends `Command+N` to the focused AI app |
| 7 | `OPEN` | Opens Town through Spotlight |
| 8 | `LINE` | Sends `Shift+Enter` |
| 9 | `SEND` | Sends `Enter` |
| 10-12 | `PREV` / `PLAY` / `NEXT` | Sends native media commands |

## Install

1. Install the latest stable CircuitPython release for the
   [Adafruit MacroPad RP2040](https://circuitpython.org/board/adafruit_macropad_rp2040/).
   The board should mount as a drive named `CIRCUITPY`.
2. Install [CircUp](https://github.com/adafruit/circup) on the Mac:

   ```sh
   python3 -m pip install --user circup
   ```

3. From this project directory, install the CircuitPython libraries and copy
   the firmware:

   ```sh
   make install
   ```

   If the board is mounted somewhere other than `/Volumes/CIRCUITPY`, pass its
   path explicitly:

   ```sh
   make install CIRCUITPY=/path/to/CIRCUITPY
   ```

CircuitPython reloads `code.py` automatically. The OLED should show the four
rows and each key should glow with its row color.

## Configure Wispr Flow

USB keyboards cannot send Apple's hardware-only `Fn` key consistently, so the
firmware uses three collision-resistant chords instead. In Wispr Flow, open
**Settings → General → Shortcuts** and add:

| Flow action | MacroPad chord |
|-------------|-----------------|
| Push to talk | `Control+Option+F13` |
| Hands-free | `Control+Option+F14` |
| Command Mode | `Control+Option+F15` |

`PTT` and `CMD` are hold-to-use keys; `FREE` is a tap. Command Mode may need to
be enabled in Flow's experimental settings, depending on the plan and version.

## App assumptions

- macOS Spotlight still uses `Command+Space`. The Codex and Town launch keys
  search for the app by name, so they do not need a helper app.
- ChatGPT still uses its default `Option+Space` Chat Bar shortcut. If you have
  changed it, update key 5 in `config.py`.
- `NEW` sends `Command+N` to whichever application is focused. Open Codex or
  ChatGPT first, then press `NEW`.
- Town's `LINE` and `SEND` keys act on the focused Town composer.

## Customize

Edit `config.py`; no changes to the hardware loop should be necessary. Each
entry supports one of four actions:

- `hold_hotkey`: press a chord until the physical key is released
- `tap_hotkey`: tap a chord once
- `launch_app`: open a named macOS app through Spotlight
- `consumer`: send a USB media-control code

Keep OLED labels to four characters and keep exactly 12 entries. Run the local
checks before deploying:

```sh
make check
make deploy
```

## Project structure

```text
code.py            Hardware event loop and action dispatcher
config.py          Editable key map, labels, colors, and timing
requirements.txt   CircuitPython libraries installed by CircUp
tests/             Hardware-independent configuration checks
```

## References

- [Adafruit MacroPad RP2040 guide](https://learn.adafruit.com/adafruit-macropad-rp2040)
- [Adafruit MacroPad CircuitPython library](https://learn.adafruit.com/adafruit-macropad-rp2040/macropad-circuitpython-library)
- [Wispr Flow desktop navigation and shortcut defaults](https://docs.wisprflow.ai/articles/5096240724-navigating-the-wispr-flow-app-desktop-ios-and-android)
- [ChatGPT macOS Chat Bar shortcut](https://help.openai.com/en/articles/9295241-accessing-the-launcher-chatgpt-macos-app)
- [Town assistant keyboard shortcuts](https://www.town.com/docs/using-town/assistant)

## License

MIT
