"""Integration tests for tag application"""

import os
import shutil
import tempfile
from pathlib import Path

# Import tagger module (loaded by conftest.py)
import tagger_module
import yaml

# Import classes from the module
Tagger = tagger_module.Tagger


class TestTagApplication:
    """Test applying tags to audio files"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_apply_tags_to_mp3(self):
        """Test applying tags from YAML to MP3 file"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config
        yaml_config = {
            "defaults": {
                "album": "Test Album",
                "albumartist": "Test Album Artist",
                "year": 2024,
                "genre": "Rock",
            },
            "files": [
                {
                    "filename": "test.mp3",
                    "track": 1,
                    "artist": "Test Artist",
                    "title": "Test Title",
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

        # Verify tags were applied
        tags = tagger.read_tags(Path("01 Test Artist - Test Title.mp3"))
        assert tags["track"] == 1
        assert tags["artist"] == "Test Artist"
        assert tags["title"] == "Test Title"
        assert tags["album"] == "Test Album"
        assert tags["albumartist"] == "Test Album Artist"
        assert tags["year"] == 2024
        assert tags["genre"] == "Rock"

    def test_apply_tags_to_m4a(self):
        """Test applying tags from YAML to M4A file"""
        # Copy dummy M4A to test directory
        src_m4a = self.fixtures_dir / "dummy.m4a"
        test_m4a = Path(self.test_dir) / "test.m4a"
        shutil.copy(src_m4a, test_m4a)

        # Create YAML config
        yaml_config = {
            "defaults": {
                "album": "M4A Album",
                "year": 2023,
            },
            "files": [
                {
                    "filename": "test.m4a",
                    "track": 2,
                    "artist": "M4A Artist",
                    "title": "M4A Title",
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

        # Verify tags were applied
        tags = tagger.read_tags(Path("02 M4A Artist - M4A Title.m4a"))
        assert tags["track"] == 2
        assert tags["artist"] == "M4A Artist"
        assert tags["title"] == "M4A Title"
        assert tags["album"] == "M4A Album"
        assert tags["year"] == 2023

    def test_defaults_override(self):
        """Test that file-specific values override defaults"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config with file overriding default
        yaml_config = {
            "defaults": {
                "album": "Default Album",
                "year": 2024,
            },
            "files": [
                {
                    "filename": "test.mp3",
                    "track": 1,
                    "title": "Test Title",
                    "album": "Override Album",  # Override default
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

        # Verify override worked
        tags = tagger.read_tags(Path("01  - Test Title.mp3"))
        assert tags["album"] == "Override Album"  # Should be overridden
        assert tags["year"] == 2024  # Should use default

    def test_generate_yaml_from_files(self):
        """Test generating YAML from existing audio files"""
        # Copy dummy files to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "01 Artist - Song One.mp3"
        test_mp3_2 = Path(self.test_dir) / "02 Artist - Song Two.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)

        # Add tags to the files first
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)

        # Write tags to both files
        tagger.write_tags(
            test_mp3_1,
            {
                "track": 1,
                "artist": "Artist",
                "title": "Song One",
                "album": "Test Album",
                "year": 2024,
            },
        )
        tagger.write_tags(
            test_mp3_2,
            {
                "track": 2,
                "artist": "Artist",
                "title": "Song Two",
                "album": "Test Album",
                "year": 2024,
            },
        )

        # Generate YAML
        tagger.generate_yaml("generated.yaml")

        # Load and verify YAML
        with open("generated.yaml", "r") as f:
            data = yaml.safe_load(f)

        # Verify structure
        assert "defaults" in data
        assert "files" in data
        assert data["defaults"]["album"] == "Test Album"
        assert data["defaults"]["year"] == 2024
        assert len(data["files"]) == 2

        # Files should not have album/year since they're in defaults
        for file_entry in data["files"]:
            assert "album" not in file_entry
            assert "year" not in file_entry
            assert "artist" in file_entry
            assert "title" in file_entry
