#!/usr/bin/env python3
"""Relay Spotify's macOS playback metadata to the MacroPad over USB."""

import argparse
import json
import subprocess
import time

import serial
from serial.tools import list_ports

from spotify_protocol import build_message


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
      duration: Number(track.duration()),
      position: Number(spotify.playerPosition())
    };
  }
}
JSON.stringify(playback);
'''

CIRCUITPY_USB_VENDOR_ID = 0x239A


def read_spotify():
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
    return playback


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
    connection = None
    while True:
        try:
            if connection is None or not connection.is_open:
                connection = connect(port_name)
            playback = read_spotify()
            message = build_message(
                playback.get("state", "stopped"),
                playback.get("title", ""),
                playback.get("artist", ""),
                playback.get("position", 0),
                playback.get("duration", 0),
            )
            connection.write(message.encode("ascii"))
            connection.flush()
            time.sleep(interval)
        except (OSError, ValueError, subprocess.SubprocessError, serial.SerialException) as error:
            print("Spotify relay:", error, flush=True)
            if connection is not None:
                connection.close()
                connection = None
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="CircuitPython data port; auto-detected by default")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    relay(args.port, max(0.25, args.interval))


if __name__ == "__main__":
    main()
