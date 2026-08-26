"""Resolve album track totals from Spotify's public web metadata."""

import time
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen


SPOTIFY_TRACK_PREFIX = "spotify:track:"
SPOTIFY_WEB_TRACK_PREFIX = "https://open.spotify.com/track/"


class SpotifyMetaParser(HTMLParser):
    """Collect the album URL and track links from Spotify meta tags."""

    def __init__(self):
        super().__init__()
        self.album_url = ""
        self.track_urls = []

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        values = dict(attrs)
        name = values.get("name")
        content = values.get("content", "")
        if name == "music:album":
            self.album_url = content
        elif name == "music:song" and content:
            self.track_urls.append(content)


def parse_spotify_meta(html):
    """Return the album URL and unique album-track URLs in page order."""
    parser = SpotifyMetaParser()
    parser.feed(html)
    return parser.album_url, tuple(dict.fromkeys(parser.track_urls))


def spotify_track_web_url(spotify_url):
    """Convert a Spotify track URI to its public HTTPS URL."""
    if spotify_url.startswith(SPOTIFY_TRACK_PREFIX):
        track_id = spotify_url[len(SPOTIFY_TRACK_PREFIX):]
        return SPOTIFY_WEB_TRACK_PREFIX + track_id
    if spotify_url.startswith(SPOTIFY_WEB_TRACK_PREFIX):
        return spotify_url.split("?", 1)[0]
    return ""


class SpotifyAlbumTrackCounter:
    """Cache public album track totals and throttle failed lookups."""

    def __init__(self, timeout=5, retry_seconds=60):
        self.timeout = timeout
        self.retry_seconds = retry_seconds
        self.track_totals = {}
        self.album_totals = {}
        self.retry_after = {}

    def resolve(self, spotify_url):
        """Return an album track total, or zero when it is unavailable."""
        track_url = spotify_track_web_url(spotify_url)
        if not track_url:
            return 0
        if track_url in self.track_totals:
            return self.track_totals[track_url]
        if time.monotonic() < self.retry_after.get(track_url, 0):
            return 0

        try:
            album_url, _ = parse_spotify_meta(self._read(track_url))
            if not album_url:
                raise ValueError("Spotify track page omitted album metadata")
            total = self.album_totals.get(album_url)
            if total is None:
                _, track_urls = parse_spotify_meta(self._read(album_url))
                total = len(track_urls)
                if total < 1:
                    raise ValueError("Spotify album page omitted track metadata")
                self.album_totals[album_url] = total
            self.track_totals[track_url] = total
            return total
        except (OSError, UnicodeError, URLError, ValueError):
            self.retry_after[track_url] = time.monotonic() + self.retry_seconds
            return 0

    def _read(self, url):
        request = Request(url, headers={"User-Agent": "AI-MacroPad/1.0"})
        with urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8")
