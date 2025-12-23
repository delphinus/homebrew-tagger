"""Tests for YouTube comment functionality"""

import os
import shutil
import tempfile
from pathlib import Path

# Import tagger module (loaded by conftest.py)
import tagger_module
import yaml

# Import classes from the module
Tagger = tagger_module.Tagger


class TestYouTubeComment:
    """Test YouTube URL extraction from filename and comment field"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_parse_youtube_id_from_filename(self):
        """Test extracting YouTube ID from filename"""
        tagger = Tagger(execute=False)

        # Test with YouTube ID in filename
        parsed = tagger.parse_filename("Foo - Bar (Hoge Remix) [TEtLwnrhn5U].m4a")
        assert parsed["artist"] == "Foo"
        assert parsed["title"] == "Bar (Hoge Remix)"
        assert parsed["comment"] == "https://www.youtube.com/watch?v=TEtLwnrhn5U"

    def test_parse_youtube_id_various_patterns(self):
        """Test YouTube ID extraction with various filename patterns"""
        tagger = Tagger(execute=False)

        # Pattern with track number
        parsed = tagger.parse_filename("01 Artist - Title [dQw4w9WgXcQ].mp3")
        assert parsed["track"] == 1
        assert parsed["artist"] == "Artist"
        assert parsed["title"] == "Title"
        assert parsed["comment"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Pattern without track number
        parsed = tagger.parse_filename("Artist - Title [a1B2c3D4e5F].mp3")
        assert parsed["artist"] == "Artist"
        assert parsed["title"] == "Title"
        assert parsed["comment"] == "https://www.youtube.com/watch?v=a1B2c3D4e5F"

        # Pattern with only title
        parsed = tagger.parse_filename("Some Title [_-AbCdEfGhI].mp3")
        assert parsed["title"] == "Some Title"
        assert parsed["comment"] == "https://www.youtube.com/watch?v=_-AbCdEfGhI"

    def test_no_youtube_id_in_filename(self):
        """Test that files without YouTube ID have no comment"""
        tagger = Tagger(execute=False)

        parsed = tagger.parse_filename("Artist - Title.mp3")
        assert parsed["artist"] == "Artist"
        assert parsed["title"] == "Title"
        assert parsed["comment"] is None

    def test_write_comment_to_mp3(self):
        """Test writing comment tag to MP3 file"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Write comment tag
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.write_tags(
            test_mp3,
            {
                "artist": "Test Artist",
                "title": "Test Title",
                "comment": "https://www.youtube.com/watch?v=TestVideoID",
            },
        )

        # Read tags and verify comment was written
        tags = tagger.read_tags(test_mp3)
        assert tags["comment"] == "https://www.youtube.com/watch?v=TestVideoID"

    def test_write_comment_to_m4a(self):
        """Test writing comment tag to M4A file"""
        # Copy dummy M4A to test directory
        src_m4a = self.fixtures_dir / "dummy.m4a"
        test_m4a = Path(self.test_dir) / "test.m4a"
        shutil.copy(src_m4a, test_m4a)

        # Write comment tag
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.write_tags(
            test_m4a,
            {
                "artist": "M4A Artist",
                "title": "M4A Title",
                "comment": "https://www.youtube.com/watch?v=M4AVideoID",
            },
        )

        # Read tags and verify comment was written
        tags = tagger.read_tags(test_m4a)
        assert tags["comment"] == "https://www.youtube.com/watch?v=M4AVideoID"

    def test_generate_yaml_with_youtube_comment(self):
        """Test that generated YAML includes comment from YouTube ID in filename"""
        # Copy dummy MP3 with YouTube ID in filename
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "Artist - Song [dQw4w9WgXcQ].mp3"
        shutil.copy(src_mp3, test_mp3)

        # Generate YAML (non-interactive for testing)
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.generate_yaml("generated.yaml", interactive=False)

        # Load and verify YAML
        with open("generated.yaml", "r") as f:
            # Skip schema comment line
            lines = f.readlines()
            yaml_content = "".join([l for l in lines if not l.startswith("# yaml-language-server:")])
            data = yaml.safe_load(yaml_content)

        # Comment should be in file entry
        assert data["files"][0]["comment"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_apply_yaml_with_comment(self):
        """Test applying YAML with comment field"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config with comment
        yaml_config = {
            "files": [
                {
                    "filename": "test.mp3",
                    "artist": "Test Artist",
                    "title": "Test Title",
                    "comment": "https://www.youtube.com/watch?v=TestID123",
                }
            ],
        }

        yaml_file = Path(self.test_dir) / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_config, f)

        # Apply tags
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # Verify comment was applied
        renamed_file = Path("Test Artist - Test Title.mp3")
        tags = tagger.read_tags(renamed_file)
        assert tags["comment"] == "https://www.youtube.com/watch?v=TestID123"

    def test_youtube_id_with_hyphens_and_underscores(self):
        """Test YouTube IDs containing hyphens and underscores"""
        tagger = Tagger(execute=False)

        # YouTube IDs can contain hyphens and underscores
        parsed = tagger.parse_filename("Song [_a-B1-C_2-3].mp3")
        assert parsed["comment"] == "https://www.youtube.com/watch?v=_a-B1-C_2-3"

    def test_invalid_youtube_id_length(self):
        """Test that IDs with wrong length are not treated as YouTube IDs"""
        tagger = Tagger(execute=False)

        # Too short (10 chars)
        parsed = tagger.parse_filename("Song [1234567890].mp3")
        assert parsed["comment"] is None

        # Too long (12 chars)
        parsed = tagger.parse_filename("Song [123456789012].mp3")
        assert parsed["comment"] is None

        # Exactly 11 chars should work
        parsed = tagger.parse_filename("Song [12345678901].mp3")
        assert parsed["comment"] == "https://www.youtube.com/watch?v=12345678901"
