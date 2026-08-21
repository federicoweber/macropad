# AI MacroPad

Profile-based CircuitPython firmware for the [Adafruit MacroPad RP2040 Starter
Kit](https://www.adafruit.com/product/5128), designed for an AI-heavy macOS
workflow.

Turn the encoder to switch between Flow, Codex, Town, and Music. The OLED shows
the active profile and its 3×4 keymap, while all 12 NeoPixels change to the
profile color. The firmware appears to macOS as a standard USB keyboard and
media controller; it does not require a desktop helper.

## Profiles

Hold the board upright with the OLED and encoder above the keys.

### 1. Flow — purple

| Left | Middle | Right |
|------|--------|-------|
| `PTT` Push to talk | `FREE` Hands-free | `CMD` Command Mode |
| `CANC` Cancel | `PAST` Paste last | `COPY` Copy last |
| `POL` Polish | `PRMT` Prompt Engineer | `ENTER` Submit |
| `BACK` Hub back | `FWD` Hub forward | `NOTE` Scratchpad |

`PTT` holds `Option+W`, matching the user-configured Flow shortcut. `FREE`
double-taps the same shortcut, which Flow interprets as hands-free mode. `CMD`
holds Flow's native non-Apple-keyboard fallback, `Command+Control+Option`.

The remaining shortcuts use Flow's current native bindings:

- Cancel: `Escape`
- Paste/copy last transcript: `Command+Control+V/C`
- Polish / Prompt Engineer: `Option+1/2`
- Submit: `Enter`
- Hub back/forward: `Command+[` / `Command+]`
- Scratchpad: `Option+S`

### 2. Codex — cyan

| Left | Middle | Right |
|------|--------|-------|
| `QCK` Quick chat | `NEW` New chat | `SRCH` Search chats |
| `PREV` Previous chat | `NEXT` Next chat | `FIND` Find in chat |
| `RVW` Review tab | `TERM` Terminal | `SIDE` Sidebar |
| `CMD` Command menu | `BACK` Navigate back | `FWD` Navigate forward |

These use the native shortcuts documented for the current ChatGPT/Codex desktop
app, including `Command+Option+N` for quick chat and `Command+N` for a new chat.

### 3. Town — orange

| Left | Middle | Right |
|------|--------|-------|
| `QUICK` Quick Town | `FOCUS` Focus Town window | `ESC` Dismiss |
| `HOME` Home | `SECT` Capture selection | `FULL` Capture full screen |
| `----` Unused | `UP` Up | `----` Unused |
| `LEFT` Left | `DOWN` Down | `RGHT` Right |

`QUICK` sends `Option+T`, `FOCUS` sends `Option+Shift+T`, `HOME` sends `Option+H`,
`SECT` sends `Option+S`, and `FULL` sends `Option+F`. The final two rows form a
navigation D-pad.

### 4. Music — green

| Left | Middle | Right |
|------|--------|-------|
| `PREV` Previous | `PLAY` Play/pause | `NEXT` Next |
| `RW` Rewind | `STOP` Stop | `FF` Fast-forward |
| `VOL-` Volume down | `MUTE` Mute | `VOL+` Volume up |
| `DIM` Brightness down | `----` Unused | `BRIT` Brightness up |

Music uses native USB consumer-control commands and works without app-specific
configuration.

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
- `consumer`: send a USB media-control code
- `type_text`: type literal text
- `noop`: intentionally leave a key unused

Run the host checks and deploy changes with:

```sh
make check
make deploy
```

## Project structure

```text
code.py                 Profile switching and hardware event loop
config.py               Profiles, key bindings, labels, and colors
requirements.txt        CircuitPython libraries installed on the board
requirements-host.txt   Host deployment tools
tests/                  Hardware-independent profile checks
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
