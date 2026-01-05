#!/usr/bin/env python3
"""
reminder.py - Add URLs to macOS Reminders with automatic title extraction

This script allows you to add URLs to macOS Reminders app with:
- Automatic title extraction from YouTube and Bandcamp URLs
- Interactive selection of reminder lists
- Support for custom titles and notes
"""

import argparse
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from typing import Optional


def get_reminder_lists() -> list[dict[str, str]]:
    """Get all reminder lists from macOS Reminders app

    Returns:
        List of dictionaries with 'name' and 'id' keys
    """
    applescript = '''
    tell application "Reminders"
        set listNames to {}
        repeat with aList in lists
            set end of listNames to name of aList
        end repeat
        return listNames
    end tell
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse output: "List1, List2, List3"
        list_names = result.stdout.strip().split(', ')

        # Return as list of dicts with name
        return [{'name': name} for name in list_names if name]
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get reminder lists: {e.stderr}", file=sys.stderr)
        return []


def select_reminder_list(lists: list[dict[str, str]]) -> Optional[str]:
    """Interactively select a reminder list

    Args:
        lists: List of reminder list dictionaries

    Returns:
        Selected list name, or None if cancelled
    """
    if not lists:
        print("Error: No reminder lists found", file=sys.stderr)
        return None

    print("\nAvailable Reminder Lists:")
    print("=" * 60)
    for i, lst in enumerate(lists, 1):
        print(f"  {i}. {lst['name']}")
    print("=" * 60)

    while True:
        try:
            choice = input(f"\nSelect a list (1-{len(lists)}) [1]: ").strip()
            if choice == "":
                choice = "1"

            index = int(choice) - 1
            if 0 <= index < len(lists):
                return lists[index]['name']
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(lists)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            return None


class TitleParser(HTMLParser):
    """HTML parser to extract title tag content"""

    def __init__(self):
        super().__init__()
        self.title = None
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'title':
            self.in_title = True

    def handle_data(self, data):
        if self.in_title and data.strip():
            self.title = data.strip()
            self.in_title = False


def extract_title_from_html(url: str) -> Optional[str]:
    """Extract title from HTML page

    Args:
        url: URL to fetch and extract title from

    Returns:
        Extracted title from <title> tag, or None if extraction failed
    """
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            # Read and decode HTML
            html = response.read().decode('utf-8', errors='ignore')

            parser = TitleParser()
            parser.feed(html)

            return parser.title

    except Exception as e:
        print(f"Warning: Failed to extract title from HTML: {e}", file=sys.stderr)
        return None


def extract_title_from_url(url: str) -> Optional[str]:
    """Extract title from URL using yt-dlp or HTML parsing

    Tries yt-dlp first for enhanced metadata (artist, channel, etc.),
    then falls back to HTML title tag extraction.

    Supports:
    - YouTube videos (via yt-dlp)
    - Bandcamp albums/tracks (via yt-dlp)
    - Any web page with <title> tag (via HTML parsing)

    Args:
        url: URL to extract title from

    Returns:
        Extracted title, or None if extraction failed
    """
    # Try yt-dlp first for better metadata
    try:
        import yt_dlp

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Don't download, just get metadata
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Try different title fields
            title = info.get('title')
            if not title:
                title = info.get('track')
            if not title:
                title = info.get('alt_title')

            # For Bandcamp, try to get artist - title format
            if 'bandcamp.com' in url:
                artist = info.get('artist') or info.get('uploader')
                album = info.get('album')

                if artist and title:
                    if album and album != title:
                        return f"{artist} - {album} - {title}"
                    else:
                        return f"{artist} - {title}"

            # For YouTube, try to get channel - title format
            if 'youtube.com' in url or 'youtu.be' in url:
                channel = info.get('channel') or info.get('uploader')
                if channel and title:
                    return f"{channel} - {title}"

            if title:
                return title

    except ImportError:
        print("Note: yt-dlp not installed. Falling back to HTML title extraction.", file=sys.stderr)
    except Exception as e:
        print(f"Note: yt-dlp extraction failed, trying HTML: {e}", file=sys.stderr)

    # Fallback to HTML title extraction
    return extract_title_from_html(url)


def add_reminder(
    list_name: str,
    title: str,
    notes: Optional[str] = None,
    url: Optional[str] = None
) -> bool:
    """Add a reminder to macOS Reminders app

    Args:
        list_name: Name of the reminder list
        title: Reminder title
        notes: Optional notes
        url: Optional URL (will be added to notes if provided)

    Returns:
        True if successful, False otherwise
    """
    # Combine URL and notes
    full_notes = ""
    if url:
        full_notes = url
    if notes:
        if full_notes:
            full_notes += "\n\n" + notes
        else:
            full_notes = notes

    # Escape quotes in strings for AppleScript
    title_escaped = title.replace('"', '\\"')
    notes_escaped = full_notes.replace('"', '\\"')
    list_name_escaped = list_name.replace('"', '\\"')

    # Build AppleScript
    if full_notes:
        applescript = f'''
        tell application "Reminders"
            tell list "{list_name_escaped}"
                make new reminder with properties {{name:"{title_escaped}", body:"{notes_escaped}"}}
            end tell
        end tell
        '''
    else:
        applescript = f'''
        tell application "Reminders"
            tell list "{list_name_escaped}"
                make new reminder with properties {{name:"{title_escaped}"}}
            end tell
        end tell
        '''

    try:
        subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to add reminder: {e.stderr}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add URLs to macOS Reminders with automatic title extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add YouTube URL with auto-extracted title
  reminder.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

  # Add Bandcamp URL with custom title
  reminder.py "https://label.bandcamp.com/album/name" --title "Check out this album"

  # Add to specific list with notes
  reminder.py "https://example.com" --list "Music" --notes "Listen later"

  # Specify list interactively (default behavior)
  reminder.py "https://example.com"
        """
    )

    parser.add_argument(
        'url',
        help='URL to add to reminders'
    )

    parser.add_argument(
        '-t', '--title',
        help='Reminder title (if not provided, will be extracted from URL)'
    )

    parser.add_argument(
        '-l', '--list',
        help='Reminder list name (if not provided, will show selection menu)'
    )

    parser.add_argument(
        '-n', '--notes',
        help='Additional notes for the reminder'
    )

    args = parser.parse_args()

    # Get or select reminder list
    list_name = args.list
    if not list_name:
        lists = get_reminder_lists()
        if not lists:
            print("Error: No reminder lists found. Please create a list in Reminders app first.", file=sys.stderr)
            sys.exit(1)

        list_name = select_reminder_list(lists)
        if not list_name:
            sys.exit(1)

    # Get or extract title
    title = args.title
    if not title:
        print(f"Extracting title from URL...", end=" ", flush=True)
        title = extract_title_from_url(args.url)
        if title:
            print(f"✓")
            print(f"Extracted title: {title}")
        else:
            print(f"✗")
            print(f"\nError: Could not extract title from URL.", file=sys.stderr)
            print(f"Please specify a title manually using --title option.", file=sys.stderr)
            print(f"Example: reminder.py \"{args.url}\" --title \"Your Title Here\"", file=sys.stderr)
            sys.exit(1)

    # Add reminder
    print(f"\nAdding reminder to '{list_name}'...")
    if add_reminder(list_name, title, args.notes, args.url):
        print(f"✓ Successfully added reminder")
        print(f"\nDetails:")
        print(f"  List:  {list_name}")
        print(f"  Title: {title}")
        if args.url and args.url != title:
            print(f"  URL:   {args.url}")
        if args.notes:
            print(f"  Notes: {args.notes}")
    else:
        print(f"✗ Failed to add reminder")
        sys.exit(1)


if __name__ == "__main__":
    main()
