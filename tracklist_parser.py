#!/usr/bin/env python3
"""
Tracklist Parser Module

Parses tracklists from various sources (clipboard, SoundCloud, text files)
to improve DJ mix segmentation accuracy.
"""

import re
import sys
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Track:
    """Represents a single track in a tracklist"""

    number: int
    artist: Optional[str] = None
    title: Optional[str] = None
    timestamp: Optional[float] = None  # In seconds

    def __str__(self) -> str:
        parts = [f"{self.number:02d}"]
        if self.artist and self.title:
            parts.append(f"{self.artist} - {self.title}")
        elif self.title:
            parts.append(self.title)
        if self.timestamp is not None:
            mins = int(self.timestamp // 60)
            secs = int(self.timestamp % 60)
            parts.append(f"[{mins}:{secs:02d}]")
        return " ".join(parts)


class TracklistParser:
    """Parses tracklists from various text formats"""

    # Common patterns for tracklist entries
    PATTERNS = [
        # "1. Artist - Title"
        re.compile(r"^(\d+)[\.\)]\s+(.+?)\s+-\s+(.+)$"),
        # "01 Artist - Title"
        re.compile(r"^(\d+)\s+(.+?)\s+-\s+(.+)$"),
        # "1. Title" (no artist)
        re.compile(r"^(\d+)[\.\)]\s+(.+)$"),
        # "01 Title" (no artist)
        re.compile(r"^(\d+)\s+(.+)$"),
        # "Artist - Title" (no track number, will auto-number)
        re.compile(r"^(.+?)\s+-\s+(.+)$"),
    ]

    # Patterns for timestamps
    TIMESTAMP_PATTERNS = [
        # [12:34] or (12:34)
        re.compile(r"[\[\(](\d+):(\d+)[\]\)]"),
        # 12:34
        re.compile(r"(\d+):(\d+)"),
    ]

    @staticmethod
    def parse_timestamp(text: str) -> Optional[float]:
        """
        Extract timestamp from text.

        Args:
            text: Text containing potential timestamp

        Returns:
            Timestamp in seconds, or None if not found
        """
        for pattern in TracklistParser.TIMESTAMP_PATTERNS:
            match = pattern.search(text)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                return minutes * 60 + seconds
        return None

    @staticmethod
    def clean_track_info(text: str) -> Tuple[str, Optional[float]]:
        """
        Remove timestamp from track info and return cleaned text + timestamp.

        Args:
            text: Track info text

        Returns:
            Tuple of (cleaned text, timestamp in seconds)
        """
        timestamp = TracklistParser.parse_timestamp(text)

        # Remove timestamp from text
        cleaned = text
        for pattern in TracklistParser.TIMESTAMP_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        # Clean up extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned, timestamp

    def parse_line(self, line: str, auto_number: int) -> Optional[Track]:
        """
        Parse a single line of tracklist.

        Args:
            line: Line of text
            auto_number: Track number to use if not found in line

        Returns:
            Track object or None if line doesn't match any pattern
        """
        line = line.strip()
        if not line:
            return None

        # Try to extract timestamp first
        cleaned_line, timestamp = self.clean_track_info(line)

        # Try each pattern
        for pattern in self.PATTERNS:
            match = pattern.match(cleaned_line)
            if match:
                groups = match.groups()

                if len(groups) == 3:
                    # Pattern with track number, artist, and title
                    track_num = int(groups[0])
                    artist = groups[1].strip()
                    title = groups[2].strip()
                    return Track(track_num, artist, title, timestamp)
                elif len(groups) == 2:
                    # Could be "number + title" or "artist + title"
                    # Check if first group is a number
                    try:
                        track_num = int(groups[0])
                        # "number + title" pattern
                        title = groups[1].strip()
                        return Track(track_num, None, title, timestamp)
                    except ValueError:
                        # "artist + title" pattern (no number)
                        artist = groups[0].strip()
                        title = groups[1].strip()
                        return Track(auto_number, artist, title, timestamp)

        return None

    def parse(self, text: str) -> List[Track]:
        """
        Parse a complete tracklist.

        Args:
            text: Tracklist text (multi-line)

        Returns:
            List of Track objects
        """
        lines = text.split("\n")
        tracks = []
        auto_number = 1

        for line in lines:
            track = self.parse_line(line, auto_number)
            if track:
                tracks.append(track)
                auto_number = track.number + 1

        return tracks

    @staticmethod
    def from_clipboard() -> Optional[List[Track]]:
        """
        Read tracklist from clipboard.

        Returns:
            List of Track objects, or None if clipboard is unavailable
        """
        try:
            # Try using pyperclip
            import pyperclip

            text = pyperclip.paste()
            if not text:
                return None

            parser = TracklistParser()
            return parser.parse(text)
        except ImportError:
            print(
                "Warning: pyperclip not installed. Install with: pip install pyperclip",
                file=sys.stderr,
            )
            return None
        except Exception as e:
            print(f"Error reading clipboard: {e}", file=sys.stderr)
            return None

    @staticmethod
    def from_file(filepath: str) -> Optional[List[Track]]:
        """
        Read tracklist from a text file.

        Args:
            filepath: Path to tracklist file

        Returns:
            List of Track objects, or None if file cannot be read
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            parser = TracklistParser()
            return parser.parse(text)
        except Exception as e:
            print(f"Error reading file {filepath}: {e}", file=sys.stderr)
            return None

    @staticmethod
    def from_soundcloud(url: str) -> Optional[List[Track]]:
        """
        Extract tracklist from SoundCloud URL.

        Args:
            url: SoundCloud URL

        Returns:
            List of Track objects, or None if extraction fails
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            print(
                "Warning: requests and beautifulsoup4 not installed. "
                "Install with: pip install requests beautifulsoup4",
                file=sys.stderr,
            )
            return None

        try:
            # Fetch the page
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Look for description (SoundCloud puts tracklists in description)
            # This is a simplified extraction - real implementation may need
            # more sophisticated parsing
            description = None

            # Try to find description in meta tags
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc:
                description = meta_desc.get("content", "")

            # Try to find description in page content
            if not description:
                desc_div = soup.find("div", class_="description")
                if desc_div:
                    description = desc_div.get_text()

            if description:
                parser = TracklistParser()
                return parser.parse(description)

            return None
        except Exception as e:
            print(f"Error fetching SoundCloud page: {e}", file=sys.stderr)
            return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse DJ mix tracklists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse from clipboard
  python tracklist_parser.py --clipboard

  # Parse from file
  python tracklist_parser.py --file tracklist.txt

  # Parse from SoundCloud URL
  python tracklist_parser.py --soundcloud https://soundcloud.com/...

  # Parse from stdin
  echo "1. Artist - Title" | python tracklist_parser.py
        """,
    )

    parser.add_argument(
        "--clipboard", action="store_true", help="Read tracklist from clipboard"
    )
    parser.add_argument("--file", help="Read tracklist from file")
    parser.add_argument("--soundcloud", help="Extract tracklist from SoundCloud URL")

    args = parser.parse_args()

    tracks = None

    if args.clipboard:
        tracks = TracklistParser.from_clipboard()
    elif args.file:
        tracks = TracklistParser.from_file(args.file)
    elif args.soundcloud:
        tracks = TracklistParser.from_soundcloud(args.soundcloud)
    else:
        # Read from stdin
        text = sys.stdin.read()
        parser = TracklistParser()
        tracks = parser.parse(text)

    if tracks:
        print(f"Found {len(tracks)} tracks:")
        for track in tracks:
            print(f"  {track}")
    else:
        print("No tracks found", file=sys.stderr)
        sys.exit(1)
