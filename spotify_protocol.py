"""Shared Spotify relay protocol for macOS and CircuitPython."""


PREFIX = "SPOTIFY"
LEVEL_PREFIX = "SPOTIFY_LEVEL"
DISPLAY_WIDTH = 21
SCROLL_PAUSE_STEPS = 4


class PlaybackPauseController:
    """Coordinate nested voice modes around one pause/resume pair."""

    def __init__(self):
        self.owners = set()
        self.should_resume = False

    def begin(self, owner, playback_active):
        """Register an owner and return whether playback should pause."""
        if owner in self.owners:
            return False
        should_pause = not self.owners and playback_active
        self.owners.add(owner)
        if should_pause:
            self.should_resume = True
        return should_pause

    def end(self, owner):
        """Release an owner and return whether playback should resume."""
        if owner not in self.owners:
            return False
        self.owners.remove(owner)
        should_resume = not self.owners and self.should_resume
        if should_resume:
            self.should_resume = False
        return should_resume

    def cancel(self):
        """Clear all owners and return whether playback should resume."""
        should_resume = self.should_resume
        self.owners.clear()
        self.should_resume = False
        return should_resume


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


def build_audio_level_message(levels):
    """Build one compact bass/mid/treble audio-level update."""
    encoded_levels = []
    for level in levels:
        level = min(1.0, max(0.0, float(level)))
        encoded_levels.append(str(int(level * 255)))
    if len(encoded_levels) != 3:
        raise ValueError("audio level message requires three bands")
    return "{}\t{}\n".format(LEVEL_PREFIX, "\t".join(encoded_levels))


def parse_audio_level_message(line):
    """Parse an audio-level update into a normalized float."""
    fields = line.rstrip("\r\n").split("\t")
    if len(fields) != 4 or fields[0] != LEVEL_PREFIX:
        return None
    try:
        encoded_levels = tuple(int(value) for value in fields[1:])
    except ValueError:
        return None
    if any(level < 0 or level > 255 for level in encoded_levels):
        return None
    return tuple(level / 255.0 for level in encoded_levels)


def equalizer_pixels(levels):
    """Map three audio bands to bottom-up columns on the 3x4 key grid."""
    heights = tuple(
        min(4, int(min(1.0, max(0.0, level)) * 6.0))
        for level in levels
    )
    return tuple(
        (3 - row) < heights[column]
        for row in range(4)
        for column in range(3)
    )


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
    if not playback_is_active(playback):
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
    if playback_is_active(playback):
        return "PAUSE"
    return "PLAY"


def playback_is_active(playback):
    """Return whether Spotify reports active playback."""
    return bool(playback and playback.get("state") == "playing")
