#!/usr/bin/env python3
"""Relay Spotify's macOS playback metadata to the MacroPad over USB."""

import argparse
import atexit
import json
import os
import subprocess
import threading
import time

import serial
from serial.tools import list_ports

from spotify_protocol import build_audio_level_message, build_message
from spotify_web_metadata import SpotifyAlbumTrackCounter


SPOTIFY_JXA = r'''
const spotify = Application("Spotify");
let playback;
if (!spotify.running()) {
  playback = {state: "stopped"};
} else {
  const state = String(spotify.playerState());
  if (state !== "playing" && state !== "paused") {
    playback = {state: "stopped"};
  } else {
    const track = spotify.currentTrack();
    playback = {
      state: state,
      title: String(track.name()),
      artist: String(track.artist()),
      album: String(track.album()),
      duration: Number(track.duration()),
      position: Number(spotify.playerPosition()),
      track_number: Number(track.trackNumber()),
      spotify_url: String(track.spotifyUrl())
    };
  }
}
JSON.stringify(playback);
'''

CIRCUITPY_USB_VENDOR_ID = 0x239A
AUDIO_LEVEL_INTERVAL = 1.0 / 30.0
AUDIO_LEVEL_MAX_AGE = 0.2
AUDIO_METER_RETRY_SECONDS = 5.0
AUDIO_METER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    ".build",
    "SpotifyAudioMeter.app",
    "Contents",
    "MacOS",
    "SpotifyAudioMeter",
)


def read_spotify(track_counter=None):
    """Read Spotify without launching it or requiring Web API credentials."""
    result = subprocess.run(
        ["/usr/bin/osascript", "-l", "JavaScript", "-e", SPOTIFY_JXA],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    playback = json.loads(result.stdout.strip())
    duration = float(playback.get("duration", 0))
    # Spotify's dictionary describes seconds, but current macOS builds return ms.
    if duration > 10000:
        duration /= 1000
    playback["duration"] = duration
    playback["track_number"] = max(0, int(playback.get("track_number", 0)))
    playback["track_total"] = (
        track_counter.resolve(playback.get("spotify_url", ""))
        if track_counter and playback.get("state") in ("playing", "paused")
        else 0
    )
    return playback


class SpotifyPoller:
    """Read Spotify metadata in the background so LED updates never stall."""

    def __init__(self, interval):
        self.interval = interval
        self.lock = threading.Lock()
        self.playback = {"state": "stopped"}
        self.track_counter = SpotifyAlbumTrackCounter()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return dict(self.playback)

    def _run(self):
        while True:
            started_at = time.monotonic()
            try:
                playback = read_spotify(self.track_counter)
                with self.lock:
                    self.playback = playback
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                print("Spotify metadata:", error, flush=True)
            elapsed = time.monotonic() - started_at
            time.sleep(max(0.1, self.interval - elapsed))


class SpotifyAudioMeter:
    """Manage the native helper and retain its most recent audio level."""

    def __init__(self, executable=AUDIO_METER_PATH):
        self.executable = executable
        self.process = None
        self.levels = (0.0, 0.0, 0.0)
        self.level_time = 0.0
        self.lock = threading.Lock()
        self.next_start_time = 0.0

    def ensure_running(self, should_run):
        if self.process is not None and self.process.poll() is not None:
            self.process = None
            self.next_start_time = time.monotonic() + AUDIO_METER_RETRY_SECONDS
            with self.lock:
                self.levels = (0.0, 0.0, 0.0)
                self.level_time = 0.0

        if not should_run:
            self.stop()
            return
        if self.process is not None or time.monotonic() < self.next_start_time:
            return
        if not os.path.isfile(self.executable):
            self.next_start_time = time.monotonic() + AUDIO_METER_RETRY_SECONDS
            return

        try:
            self.process = subprocess.Popen(
                [self.executable],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as error:
            print("Spotify audio meter:", error, flush=True)
            self.next_start_time = time.monotonic() + AUDIO_METER_RETRY_SECONDS
            return

        threading.Thread(
            target=self._read_levels,
            args=(self.process,),
            daemon=True,
        ).start()
        threading.Thread(
            target=self._read_errors,
            args=(self.process,),
            daemon=True,
        ).start()

    def current_levels(self):
        with self.lock:
            if time.monotonic() - self.level_time > AUDIO_LEVEL_MAX_AGE:
                return (0.0, 0.0, 0.0)
            return self.levels

    def stop(self):
        process = self.process
        self.process = None
        with self.lock:
            self.levels = (0.0, 0.0, 0.0)
            self.level_time = 0.0
        if process is not None and process.poll() is None:
            process.terminate()

    def _read_levels(self, process):
        for line in process.stdout:
            try:
                levels = tuple(
                    min(1.0, max(0.0, float(value)))
                    for value in line.strip().split(",")
                )
            except ValueError:
                continue
            if len(levels) != 3:
                continue
            with self.lock:
                self.levels = levels
                self.level_time = time.monotonic()

    @staticmethod
    def _read_errors(process):
        for line in process.stderr:
            print("Spotify audio meter:", line.rstrip(), flush=True)


def candidate_ports():
    """Return likely CircuitPython data ports, preferring the second CDC port."""
    candidates = []
    for port in list_ports.comports():
        if port.vid != CIRCUITPY_USB_VENDOR_ID:
            continue
        if not port.device.startswith("/dev/cu.usbmodem"):
            continue
        interface = (port.interface or "").lower()
        data_rank = 1 if "data" in interface or "cdc2" in interface else 0
        candidates.append((data_rank, port.device))
    return [device for _, device in sorted(candidates, reverse=True)]


def connect(port_name=None):
    """Open the requested data port or the best automatically detected one."""
    ports = [port_name] if port_name else candidate_ports()
    if not ports:
        raise serial.SerialException("MacroPad data serial port not found")
    last_error = None
    for device in ports:
        try:
            return serial.Serial(device, 115200, write_timeout=2)
        except serial.SerialException as error:
            last_error = error
    raise last_error


def relay(port_name=None, interval=1.0):
    """Poll Spotify forever and reconnect automatically after USB changes."""
    poller = SpotifyPoller(interval)
    poller.start()
    audio_meter = SpotifyAudioMeter()
    atexit.register(audio_meter.stop)
    connection = None
    next_metadata_update = 0.0
    while True:
        try:
            if connection is None or not connection.is_open:
                connection = connect(port_name)

            playback = poller.snapshot()
            playing = playback.get("state") == "playing"
            audio_meter.ensure_running(playing)
            payload = build_audio_level_message(
                audio_meter.current_levels() if playing else (0.0, 0.0, 0.0)
            )

            now = time.monotonic()
            if now >= next_metadata_update:
                payload += build_message(
                    playback.get("state", "stopped"),
                    playback.get("title", ""),
                    playback.get("artist", ""),
                    playback.get("position", 0),
                    playback.get("duration", 0),
                    playback.get("album", ""),
                    playback.get("track_number", 0),
                    playback.get("track_total", 0),
                )
                next_metadata_update = now + interval

            connection.write(payload.encode("ascii"))
            connection.flush()
            time.sleep(AUDIO_LEVEL_INTERVAL)
        except (OSError, ValueError, subprocess.SubprocessError, serial.SerialException) as error:
            print("Spotify relay:", error, flush=True)
            if connection is not None:
                connection.close()
                connection = None
            next_metadata_update = 0.0
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="CircuitPython data port; auto-detected by default")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    relay(args.port, max(0.25, args.interval))


if __name__ == "__main__":
    main()
