"""Shared Spotify relay protocol for macOS and CircuitPython."""


PREFIX = "SPOTIFY"
HOST_COMMAND_PREFIX = "MACROPAD"
DISPLAY_WIDTH = 21
SCROLL_PAUSE_STEPS = 4


def clean_field(value):
    """Return one printable ASCII protocol field."""
    text = str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")
    return "".join(
        character if 32 <= ord(character) <= 126 else "?"
        for character in text
    )


def build_message(
    state, title="", artist="", position=0, duration=0, album=""
):
    """Build one newline-delimited playback update."""
    fields = [PREFIX, clean_field(state)]
    if state in ("playing", "paused"):
        fields.extend(
            (
                clean_field(title),
                clean_field(artist),
                clean_field(album),
                str(max(0, int(position))),
                str(max(0, int(duration))),
            )
        )
    return "\t".join(fields) + "\n"


def parse_message(line):
    """Parse one relay update, returning None for malformed input."""
    fields = line.rstrip("\r\n").split("\t")
    if len(fields) < 2 or fields[0] != PREFIX:
        return None

    state = fields[1]
    if state not in ("playing", "paused", "stopped"):
        return None
    if state == "stopped":
        return {
            "state": state,
            "title": "",
            "artist": "",
            "album": "",
            "position": 0,
            "duration": 0,
        }
    if len(fields) != 7:
        return None

    try:
        position = max(0, int(fields[5]))
        duration = max(0, int(fields[6]))
    except ValueError:
        return None

    return {
        "state": state,
        "title": fields[2],
        "artist": fields[3],
        "album": fields[4],
        "position": position,
        "duration": duration,
    }


def build_host_command(command):
    """Build one MacroPad-to-host command."""
    return "{}\t{}\n".format(HOST_COMMAND_PREFIX, clean_field(command))


def parse_host_command(line):
    """Parse one MacroPad-to-host command."""
    fields = line.rstrip("\r\n").split("\t")
    if len(fields) != 2 or fields[0] != HOST_COMMAND_PREFIX:
        return None
    return fields[1]


def format_time(seconds):
    """Format a non-negative duration for the compact OLED."""
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return "{}:{:02}:{:02}".format(hours, minutes, seconds)
    return "{}:{:02}".format(minutes, seconds)


def playback_display_rows(playback):
    """Return four OLED rows only for active playback."""
    if not playback or playback.get("state") != "playing":
        return None

    title = playback.get("title") or "Unknown track"
    artist = playback.get("artist") or "Unknown artist"
    album = playback.get("album") or "Unknown album"
    progress = "{} / {}".format(
        format_time(playback.get("position", 0)),
        format_time(playback.get("duration", 0)),
    )
    return (
        artist,
        album,
        title,
        progress,
    )


def scrolling_display_text(
    text, step, width=DISPLAY_WIDTH, pause_steps=SCROLL_PAUSE_STEPS
):
    """Return one display-width window that advances through long text."""
    if len(text) <= width:
        return text + (" " * (width - len(text)))

    last_offset = len(text) - width
    cycle_steps = pause_steps + last_offset + pause_steps
    phase = step % cycle_steps
    if phase < pause_steps:
        offset = 0
    elif phase < pause_steps + last_offset:
        offset = phase - pause_steps + 1
    else:
        offset = last_offset
    return text[offset:offset + width]


def transport_label(playback):
    """Return the action the center transport key will perform."""
    if playback and playback.get("state") == "playing":
        return "PAUSE"
    return "PLAY"
