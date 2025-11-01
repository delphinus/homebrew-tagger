"""Tests for Pydantic schema validation"""

import sys

import pytest

# Import tagger module (loaded by conftest.py)
import tagger_module
from pydantic import ValidationError

# Import classes from the module
Defaults = tagger_module.Defaults
FileEntry = tagger_module.FileEntry
TaggerConfig = tagger_module.TaggerConfig
Tagger = tagger_module.Tagger


class TestDefaultsValidation:
    """Test Defaults model validation"""

    def test_valid_defaults(self):
        """Test valid defaults configuration"""
        defaults = Defaults(
            album="Test Album", albumartist="Test Artist", year=2024, genre="Rock"
        )
        assert defaults.album == "Test Album"
        assert defaults.year == 2024

    def test_year_too_old(self):
        """Test that year before 1900 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Defaults(year=1899)

        errors = exc_info.value.errors()
        assert any(
            "Year must be between 1900 and 2100" in str(e["msg"]) for e in errors
        )

    def test_year_too_future(self):
        """Test that year after 2100 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Defaults(year=2101)

        errors = exc_info.value.errors()
        assert any(
            "Year must be between 1900 and 2100" in str(e["msg"]) for e in errors
        )

    def test_extra_field_rejected(self):
        """Test that extra fields are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Defaults(unknown_field="value")

        errors = exc_info.value.errors()
        assert any("extra" in str(e["type"]).lower() for e in errors)


class TestFileEntryValidation:
    """Test FileEntry model validation"""

    def test_valid_file_entry(self):
        """Test valid file entry"""
        entry = FileEntry(
            filename="01 Artist - Title.mp3", track=1, artist="Artist", title="Title"
        )
        assert entry.filename == "01 Artist - Title.mp3"
        assert entry.track == 1

    def test_filename_required(self):
        """Test that filename is required"""
        with pytest.raises(ValidationError) as exc_info:
            FileEntry(track=1, title="Test")

        errors = exc_info.value.errors()
        assert any("filename" in str(e["loc"]) for e in errors)

    def test_track_must_be_positive(self):
        """Test that track number must be positive"""
        with pytest.raises(ValidationError) as exc_info:
            FileEntry(filename="test.mp3", track=0)

        errors = exc_info.value.errors()
        assert any("Track number must be positive" in str(e["msg"]) for e in errors)

    def test_negative_track_rejected(self):
        """Test that negative track number is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            FileEntry(filename="test.mp3", track=-1)

        errors = exc_info.value.errors()
        assert any("Track number must be positive" in str(e["msg"]) for e in errors)


class TestTaggerConfigValidation:
    """Test TaggerConfig model validation"""

    def test_valid_config(self):
        """Test valid tagger configuration"""
        config = TaggerConfig(
            defaults=Defaults(album="Test Album", year=2024),
            files=[
                FileEntry(filename="01.mp3", track=1, title="Track 1"),
                FileEntry(filename="02.mp3", track=2, title="Track 2"),
            ],
        )
        assert config.defaults.album == "Test Album"
        assert len(config.files) == 2

    def test_files_required(self):
        """Test that files list is required"""
        with pytest.raises(ValidationError) as exc_info:
            TaggerConfig()

        errors = exc_info.value.errors()
        assert any("files" in str(e["loc"]) for e in errors)

    def test_empty_files_rejected(self):
        """Test that empty files list is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TaggerConfig(files=[])

        errors = exc_info.value.errors()
        assert any("files" in str(e["loc"]) for e in errors)

    def test_typo_in_defaults_rejected(self):
        """Test that typo 'default' instead of 'defaults' is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TaggerConfig(
                default={"album": "Test"},  # Typo: should be 'defaults'
                files=[FileEntry(filename="test.mp3", title="Test")],
            )

        errors = exc_info.value.errors()
        # Should reject 'default' as extra field
        assert any("extra" in str(e["type"]).lower() for e in errors)

    def test_config_without_defaults(self):
        """Test that defaults is optional"""
        config = TaggerConfig(files=[FileEntry(filename="test.mp3", title="Test")])
        assert config.defaults is None
        assert len(config.files) == 1
