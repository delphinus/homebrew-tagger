"""
Tests for tracklist parsing functionality
"""

import pytest
from tracklist_parser import Track, TracklistParser


class TestTrack:
    """Tests for Track dataclass"""

    def test_track_creation(self):
        """Test creating a track"""
        track = Track(1, "Artist", "Title", 120.0)
        assert track.number == 1
        assert track.artist == "Artist"
        assert track.title == "Title"
        assert track.timestamp == 120.0

    def test_track_str(self):
        """Test track string representation"""
        track = Track(1, "Artist", "Title", 120.0)
        assert "01" in str(track)
        assert "Artist - Title" in str(track)
        assert "2:00" in str(track)


class TestTracklistParser:
    """Tests for TracklistParser class"""

    def test_parse_timestamp(self):
        """Test timestamp parsing"""
        # [12:34] format
        assert TracklistParser.parse_timestamp("[12:34]") == 754
        # (12:34) format
        assert TracklistParser.parse_timestamp("(12:34)") == 754
        # 12:34 format
        assert TracklistParser.parse_timestamp("12:34") == 754
        # No timestamp
        assert TracklistParser.parse_timestamp("no timestamp here") is None

    def test_clean_track_info(self):
        """Test removing timestamps from track info"""
        text = "Artist - Title [12:34]"
        cleaned, timestamp = TracklistParser.clean_track_info(text)
        assert cleaned == "Artist - Title"
        assert timestamp == 754

    def test_parse_line_with_number_artist_title(self):
        """Test parsing '1. Artist - Title' format"""
        parser = TracklistParser()
        track = parser.parse_line("1. Artist Name - Track Title", 1)
        assert track is not None
        assert track.number == 1
        assert track.artist == "Artist Name"
        assert track.title == "Track Title"

    def test_parse_line_with_number_title(self):
        """Test parsing '1. Title' format (no artist)"""
        parser = TracklistParser()
        track = parser.parse_line("1. Track Title Only", 1)
        assert track is not None
        assert track.number == 1
        assert track.artist is None
        assert track.title == "Track Title Only"

    def test_parse_line_artist_title_no_number(self):
        """Test parsing 'Artist - Title' format (no number)"""
        parser = TracklistParser()
        track = parser.parse_line("Artist Name - Track Title", 5)
        assert track is not None
        assert track.number == 5  # Should use auto_number
        assert track.artist == "Artist Name"
        assert track.title == "Track Title"

    def test_parse_line_with_timestamp(self):
        """Test parsing with timestamp"""
        parser = TracklistParser()
        track = parser.parse_line("1. Artist - Title [12:34]", 1)
        assert track is not None
        assert track.number == 1
        assert track.artist == "Artist"
        assert track.title == "Title"
        assert track.timestamp == 754

    def test_parse_multiline_tracklist(self):
        """Test parsing a complete tracklist"""
        tracklist_text = """
1. First Artist - First Track
2. Second Artist - Second Track [5:30]
3. Third Artist - Third Track
        """
        parser = TracklistParser()
        tracks = parser.parse(tracklist_text)

        assert len(tracks) == 3
        assert tracks[0].number == 1
        assert tracks[0].artist == "First Artist"
        assert tracks[0].title == "First Track"

        assert tracks[1].number == 2
        assert tracks[1].timestamp == 330  # 5:30 = 330 seconds

        assert tracks[2].number == 3

    def test_parse_mixed_formats(self):
        """Test parsing tracklist with mixed formats"""
        tracklist_text = """
1. Artist One - Track One
Artist Two - Track Two
3. Artist Three - Track Three
        """
        parser = TracklistParser()
        tracks = parser.parse(tracklist_text)

        assert len(tracks) == 3
        assert tracks[0].number == 1
        assert tracks[1].number == 2  # Auto-numbered
        assert tracks[2].number == 3

    def test_parse_empty_lines(self):
        """Test that empty lines are ignored"""
        tracklist_text = """
1. First Track

2. Second Track


3. Third Track
        """
        parser = TracklistParser()
        tracks = parser.parse(tracklist_text)

        assert len(tracks) == 3

    def test_parse_with_various_separators(self):
        """Test parsing with different number formats"""
        parser = TracklistParser()

        # Dot separator
        track1 = parser.parse_line("1. Artist - Title", 1)
        assert track1.number == 1

        # Parenthesis
        track2 = parser.parse_line("1) Artist - Title", 1)
        assert track2.number == 1

        # Just number and space
        track3 = parser.parse_line("01 Artist - Title", 1)
        assert track3.number == 1

    def test_from_file(self, tmp_path):
        """Test reading tracklist from file"""
        tracklist_file = tmp_path / "tracklist.txt"
        tracklist_file.write_text(
            """
1. First Artist - First Track
2. Second Artist - Second Track
3. Third Artist - Third Track
            """
        )

        tracks = TracklistParser.from_file(str(tracklist_file))
        assert tracks is not None
        assert len(tracks) == 3
        assert tracks[0].artist == "First Artist"

    def test_from_file_nonexistent(self):
        """Test reading from nonexistent file"""
        tracks = TracklistParser.from_file("/nonexistent/file.txt")
        assert tracks is None

    def test_parse_real_world_format(self):
        """Test parsing real-world DJ mix tracklist format"""
        tracklist_text = """
CD2 Mixed by DJ Storm & Bananaman:

1. Kurt - Space Odyssey 2014
2. DJ Ham, DJ Demo & Justin Time - Here I Am (Fracus & Darwin Remix)
3. JHAL - Please Be Mine (Darwin Remix) [10:30]
4. Bananaman - Make You Dance
5. Force & Styles - Heart Of Gold (Bananaman & Storm 2014 Remix)
        """
        parser = TracklistParser()
        tracks = parser.parse(tracklist_text)

        # Should skip the "CD2 Mixed..." line and parse the tracks
        assert len(tracks) >= 5
        first_track = next((t for t in tracks if t.artist == "Kurt"), None)
        assert first_track is not None
        assert first_track.title == "Space Odyssey 2014"
