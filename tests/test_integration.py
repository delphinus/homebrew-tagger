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

        # Generate YAML (non-interactive for testing)
        tagger.generate_yaml("generated.yaml", interactive=False)

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

    def test_yaml_updates_on_filename_change(self):
        """Test that YAML file is updated when filename changes"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config
        yaml_config = {
            "defaults": {
                "album": "Test Album",
                "year": 2024,
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

        # Apply tags (this should rename the file)
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # Load YAML and verify filename was updated
        with open(yaml_file, "r") as f:
            updated_data = yaml.safe_load(f)

        expected_filename = "01 Test Artist - Test Title.mp3"
        assert updated_data["files"][0]["filename"] == expected_filename
        assert Path(expected_filename).exists()

        # Apply YAML again - it should succeed without errors
        # This tests the bug where the second run would fail because
        # the YAML still had the old filename
        tagger.apply_yaml("test.yaml")

        # Verify the file still exists with correct tags
        tags = tagger.read_tags(Path(expected_filename))
        assert tags["track"] == 1
        assert tags["artist"] == "Test Artist"
        assert tags["title"] == "Test Title"

    def test_yaml_updates_with_multiple_files(self):
        """Test that YAML file is updated correctly when multiple files are renamed"""
        # Copy dummy MP3s to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "file1.mp3"
        test_mp3_2 = Path(self.test_dir) / "file2.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)

        # Create YAML config
        yaml_config = {
            "defaults": {
                "album": "Multi Test Album",
            },
            "files": [
                {
                    "filename": "file1.mp3",
                    "track": 1,
                    "artist": "Artist One",
                    "title": "Title One",
                },
                {
                    "filename": "file2.mp3",
                    "track": 2,
                    "artist": "Artist Two",
                    "title": "Title Two",
                },
            ],
        }

        yaml_file = Path(self.test_dir) / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_config, f)

        # Apply tags
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # Load YAML and verify filenames were updated
        with open(yaml_file, "r") as f:
            updated_data = yaml.safe_load(f)

        expected_filename_1 = "01 Artist One - Title One.mp3"
        expected_filename_2 = "02 Artist Two - Title Two.mp3"

        assert updated_data["files"][0]["filename"] == expected_filename_1
        assert updated_data["files"][1]["filename"] == expected_filename_2
        assert Path(expected_filename_1).exists()
        assert Path(expected_filename_2).exists()

        # Apply YAML again to verify it works with updated filenames
        tagger.apply_yaml("test.yaml")

        # Both files should still exist with correct tags
        tags1 = tagger.read_tags(Path(expected_filename_1))
        tags2 = tagger.read_tags(Path(expected_filename_2))
        assert tags1["artist"] == "Artist One"
        assert tags2["artist"] == "Artist Two"

    def test_dry_run_no_output_when_tags_match(self, capsys):
        """Test that dry-run mode shows no output when tags already match YAML"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config
        yaml_config = {
            "defaults": {
                "album": "Test Album",
                "year": 2024,
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

        # Apply tags in execute mode first
        os.chdir(self.test_dir)
        tagger_exec = Tagger(execute=True)
        tagger_exec.apply_yaml("test.yaml")

        # Now run in dry-run mode - should show no "Would update" since tags match
        tagger_dry = Tagger(execute=False)
        capsys.readouterr()  # Clear any previous output
        tagger_dry.apply_yaml("test.yaml")

        captured = capsys.readouterr()
        # Should not contain "Would update tags for:"
        assert "Would update tags for:" not in captured.out

    def test_dry_run_shows_files_with_differences(self, capsys):
        """Test that dry-run mode only shows files that need updating"""
        # Copy dummy MP3s to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "test1.mp3"
        test_mp3_2 = Path(self.test_dir) / "test2.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)

        # Create YAML config
        yaml_config = {
            "defaults": {
                "album": "Test Album",
                "year": 2024,
            },
            "files": [
                {
                    "filename": "test1.mp3",
                    "track": 1,
                    "artist": "Artist One",
                    "title": "Title One",
                },
                {
                    "filename": "test2.mp3",
                    "track": 2,
                    "artist": "Artist Two",
                    "title": "Title Two",
                },
            ],
        }

        yaml_file = Path(self.test_dir) / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_config, f)

        # Apply tags in execute mode to first file only
        os.chdir(self.test_dir)
        tagger_exec = Tagger(execute=True)
        tagger_exec.write_tags(
            test_mp3_1,
            {
                "track": 1,
                "artist": "Artist One",
                "title": "Title One",
                "album": "Test Album",
                "year": 2024,
            },
        )

        # Leave test2.mp3 with different/no tags

        # Now run in dry-run mode
        tagger_dry = Tagger(execute=False)
        capsys.readouterr()  # Clear any previous output
        tagger_dry.apply_yaml("test.yaml")

        captured = capsys.readouterr()
        # Should show test2.mp3 but not test1.mp3
        assert "Would update tags for: test2.mp3" in captured.out
        assert "Would update tags for: test1.mp3" not in captured.out

    def test_execute_mode_skips_files_with_no_differences(self):
        """Test that execute mode skips updating files when tags already match"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config
        yaml_config = {
            "defaults": {
                "album": "Test Album",
                "year": 2024,
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

        # Apply tags first time
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # Get file modification time
        renamed_file = Path("01 Test Artist - Test Title.mp3")
        first_mtime = renamed_file.stat().st_mtime

        # Apply tags second time - file should not be modified since tags match
        import time

        time.sleep(0.1)  # Small delay to ensure different mtime if file is modified
        tagger.apply_yaml("test.yaml")

        second_mtime = renamed_file.stat().st_mtime
        # File should not have been modified
        assert first_mtime == second_mtime

    def test_compare_tags_detects_differences(self):
        """Test the _compare_tags method correctly identifies differences"""
        tagger = Tagger(execute=False)

        # Test with no differences
        current = {
            "track": 1,
            "artist": "Artist",
            "title": "Title",
            "album": "Album",
            "year": 2024,
        }
        expected = {
            "track": 1,
            "artist": "Artist",
            "title": "Title",
            "album": "Album",
            "year": 2024,
        }
        differences = tagger._compare_tags(current, expected)
        assert len(differences) == 0

        # Test with differences
        current = {
            "track": 1,
            "artist": "Old Artist",
            "title": "Old Title",
            "album": "Album",
            "year": 2024,
        }
        expected = {
            "track": 1,
            "artist": "New Artist",
            "title": "New Title",
            "album": "Album",
            "year": 2024,
        }
        differences = tagger._compare_tags(current, expected)
        assert len(differences) == 2
        assert "artist" in differences
        assert "title" in differences
        assert differences["artist"] == ("Old Artist", "New Artist")
        assert differences["title"] == ("Old Title", "New Title")

        # Test with None values in expected (should not be considered different)
        current = {
            "track": 1,
            "artist": "Artist",
            "title": "Title",
            "album": "Album",
        }
        expected = {
            "track": 1,
            "artist": "Artist",
            "title": "Title",
            "year": None,  # None means don't care
        }
        differences = tagger._compare_tags(current, expected)
        assert len(differences) == 0


class TestTrackNumberPadding:
    """Test track number padding in filenames"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_two_digit_padding_for_small_numbers(self):
        """Test that track numbers are padded to at least 2 digits"""
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML with 9 tracks
        yaml_config = {
            "files": [{"filename": "test.mp3", "track": 5, "title": "Track Five"}]
        }

        yaml_file = Path(self.test_dir) / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_config, f)

        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # Should be 05, not 5
        assert Path("05  - Track Five.mp3").exists()

    def test_three_digit_padding_for_large_numbers(self):
        """Test that track numbers pad to 3 digits when max is 100+"""
        src_mp3 = self.fixtures_dir / "dummy.mp3"

        # Create 3 test files
        files_data = []
        for i in [1, 50, 100]:
            test_mp3 = Path(self.test_dir) / f"track{i}.mp3"
            shutil.copy(src_mp3, test_mp3)
            files_data.append(
                {"filename": f"track{i}.mp3", "track": i, "title": f"Track {i}"}
            )

        yaml_config = {"files": files_data}

        yaml_file = Path(self.test_dir) / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_config, f)

        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # All should use 3 digits
        assert Path("001  - Track 1.mp3").exists()
        assert Path("050  - Track 50.mp3").exists()
        assert Path("100  - Track 100.mp3").exists()

    def test_consistent_padding_within_album(self):
        """Test that all files in an album use consistent padding"""
        src_mp3 = self.fixtures_dir / "dummy.mp3"

        # Create files with tracks 1-100
        files_data = []
        for i in [1, 10, 99, 100]:
            test_mp3 = Path(self.test_dir) / f"track{i}.mp3"
            shutil.copy(src_mp3, test_mp3)
            files_data.append(
                {"filename": f"track{i}.mp3", "track": i, "title": f"Song {i}"}
            )

        yaml_config = {"files": files_data}

        yaml_file = Path(self.test_dir) / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_config, f)

        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # All should use 3 digits because max is 100
        assert Path("001  - Song 1.mp3").exists()
        assert Path("010  - Song 10.mp3").exists()
        assert Path("099  - Song 99.mp3").exists()
        assert Path("100  - Song 100.mp3").exists()


class TestFilenamePreference:
    """Test prefer_filename functionality"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_prefer_filename_over_tags(self):
        """Test that prefer_filename uses filename metadata over embedded tags"""
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        # Create file with tags that differ from filename
        test_mp3 = Path(self.test_dir) / "01 Real Artist - Real Title.mp3"
        shutil.copy(src_mp3, test_mp3)

        os.chdir(self.test_dir)

        # Write different tags to the file
        tagger = Tagger(execute=True)
        tagger.write_tags(
            test_mp3,
            {"track": 99, "artist": "Wrong Artist", "title": "Wrong Title"},
        )

        # Generate YAML with prefer_filename
        tagger_prefer = Tagger(execute=True, prefer_filename=True)
        tagger_prefer.generate_yaml("generated.yaml", interactive=False)

        # Load and verify YAML
        with open("generated.yaml", "r") as f:
            data = yaml.safe_load(f)

        # Should use filename metadata
        file_entry = data["files"][0]
        assert file_entry["track"] == 1  # from filename, not 99
        assert file_entry["artist"] == "Real Artist"  # from filename
        assert file_entry["title"] == "Real Title"  # from filename

    def test_default_prefers_embedded_tags(self):
        """Test that by default, embedded tags are preferred"""
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        # Create file with tags that differ from filename
        test_mp3 = Path(self.test_dir) / "01 Filename Artist - Filename Title.mp3"
        shutil.copy(src_mp3, test_mp3)

        os.chdir(self.test_dir)

        # Write different tags to the file
        tagger = Tagger(execute=True)
        tagger.write_tags(
            test_mp3, {"track": 5, "artist": "Tag Artist", "title": "Tag Title"}
        )

        # Generate YAML without prefer_filename
        tagger.generate_yaml("generated.yaml", interactive=False)

        # Load and verify YAML
        with open("generated.yaml", "r") as f:
            data = yaml.safe_load(f)

        # Should use embedded tags
        file_entry = data["files"][0]
        assert file_entry["track"] == 5  # from tags, not 1
        assert file_entry["artist"] == "Tag Artist"  # from tags
        assert file_entry["title"] == "Tag Title"  # from tags


class TestArtworkDetection:
    """Test artwork detection with different APIC frame descriptions"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_artwork_detection_with_description(self):
        """Test that artwork is detected even when APIC frame has a description like 'Cover'"""
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        os.chdir(self.test_dir)

        # Add artwork with description "Cover"
        from mutagen.id3 import ID3, APIC
        from mutagen.mp3 import MP3

        audio = MP3(test_mp3, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()

        # Create a small PNG image (1x1 pixel)
        png_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
            b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # Add artwork with description "Cover"
        audio.tags.add(
            APIC(
                encoding=3,
                mime="image/png",
                type=3,  # Cover (front)
                desc="Cover",
                data=png_data,
            )
        )
        audio.save()

        # Read tags and verify artwork is detected
        tagger = Tagger(execute=False)
        tags = tagger.read_tags(test_mp3)
        assert tags["artwork"] == "<embedded>"

    def test_artwork_detection_without_description(self):
        """Test that artwork is detected even when APIC frame has no description"""
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        os.chdir(self.test_dir)

        # Add artwork without description
        from mutagen.id3 import ID3, APIC
        from mutagen.mp3 import MP3

        audio = MP3(test_mp3, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()

        # Create a small PNG image
        png_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
            b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # Add artwork without description (empty string)
        audio.tags.add(
            APIC(encoding=3, mime="image/png", type=3, desc="", data=png_data)
        )
        audio.save()

        # Read tags and verify artwork is detected
        tagger = Tagger(execute=False)
        tags = tagger.read_tags(test_mp3)
        assert tags["artwork"] == "<embedded>"

    def test_no_artwork_detection(self):
        """Test that files without artwork return None"""
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        os.chdir(self.test_dir)

        # Read tags and verify no artwork is detected
        tagger = Tagger(execute=False)
        tags = tagger.read_tags(test_mp3)
        assert tags.get("artwork") is None


class TestTrackSorting:
    """Test track number sorting in YAML files"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_yaml_files_sorted_by_track_on_apply(self):
        """Test that YAML files are sorted by track number when applying"""
        # Copy dummy MP3s to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "file1.mp3"
        test_mp3_2 = Path(self.test_dir) / "file2.mp3"
        test_mp3_3 = Path(self.test_dir) / "file3.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)
        shutil.copy(src_mp3, test_mp3_3)

        # Create YAML config with files in wrong order
        yaml_config = {
            "defaults": {"album": "Test Album"},
            "files": [
                {
                    "filename": "file3.mp3",
                    "track": 3,
                    "title": "Title Three",
                },
                {
                    "filename": "file1.mp3",
                    "track": 1,
                    "title": "Title One",
                },
                {
                    "filename": "file2.mp3",
                    "track": 2,
                    "title": "Title Two",
                },
            ],
        }

        yaml_file = Path(self.test_dir) / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_config, f)

        # Apply tags
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # Load YAML and verify files are sorted by track number
        with open(yaml_file, "r") as f:
            updated_data = yaml.safe_load(f)

        assert len(updated_data["files"]) == 3
        assert updated_data["files"][0]["track"] == 1
        assert updated_data["files"][1]["track"] == 2
        assert updated_data["files"][2]["track"] == 3

    def test_yaml_files_sorted_on_generate(self):
        """Test that generated YAML has files sorted by track number"""
        # Copy dummy MP3s to test directory with names in wrong order
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "03 Title Three.mp3"
        test_mp3_2 = Path(self.test_dir) / "01 Title One.mp3"
        test_mp3_3 = Path(self.test_dir) / "02 Title Two.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)
        shutil.copy(src_mp3, test_mp3_3)

        # Generate YAML (non-interactive for testing)
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.generate_yaml("generated.yaml", interactive=False)

        # Load and verify YAML
        with open("generated.yaml", "r") as f:
            data = yaml.safe_load(f)

        # Files should be sorted by track number
        assert len(data["files"]) == 3
        assert data["files"][0]["track"] == 1
        assert data["files"][0]["title"] == "Title One"
        assert data["files"][1]["track"] == 2
        assert data["files"][1]["title"] == "Title Two"
        assert data["files"][2]["track"] == 3
        assert data["files"][2]["title"] == "Title Three"


class TestDiscNumberSupport:
    """Test disc number support for multi-disc albums"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_disc_number_mp3(self):
        """Test applying disc number to MP3 file"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config with disc number
        yaml_config = {
            "defaults": {
                "album": "Multi-Disc Album",
                "disc": 1,
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

        # Verify disc number was applied (filename now includes disc number)
        tags = tagger.read_tags(Path("01-01 Test Artist - Test Title.mp3"))
        assert tags["disc"] == 1

    def test_disc_number_m4a(self):
        """Test applying disc number to M4A file"""
        # Copy dummy M4A to test directory
        src_m4a = self.fixtures_dir / "dummy.m4a"
        test_m4a = Path(self.test_dir) / "test.m4a"
        shutil.copy(src_m4a, test_m4a)

        # Create YAML config with disc number
        yaml_config = {
            "defaults": {
                "album": "Multi-Disc Album",
                "disc": 2,
            },
            "files": [
                {
                    "filename": "test.m4a",
                    "track": 1,
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

        # Verify disc number was applied (filename now includes disc number)
        tags = tagger.read_tags(Path("02-01 M4A Artist - M4A Title.m4a"))
        assert tags["disc"] == 2

    def test_disc_number_in_generated_yaml(self):
        """Test that disc number appears in generated YAML"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Add tags including disc number
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.write_tags(
            test_mp3,
            {
                "track": 1,
                "artist": "Artist",
                "title": "Song",
                "album": "Album",
                "disc": 1,
            },
        )

        # Generate YAML (non-interactive for testing)
        tagger.generate_yaml("generated.yaml", interactive=False)

        # Load and verify YAML
        with open("generated.yaml", "r") as f:
            data = yaml.safe_load(f)

        # Disc should be in defaults or file entry
        assert (
            data.get("defaults", {}).get("disc") == 1
            or data["files"][0].get("disc") == 1
        )

    def test_disc_number_in_filename(self):
        """Test that disc number appears in filename as 2-digit prefix"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config with disc number
        yaml_config = {
            "defaults": {
                "album": "Multi-Disc Album",
            },
            "files": [
                {
                    "filename": "test.mp3",
                    "disc": 1,
                    "track": 3,
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

        # Verify filename includes disc number as 01-03
        expected_filename = "01-03 Test Artist - Test Title.mp3"
        assert Path(expected_filename).exists()

        # Verify tags were applied
        tags = tagger.read_tags(Path(expected_filename))
        assert tags["disc"] == 1
        assert tags["track"] == 3

    def test_disc_number_in_filename_without_artist(self):
        """Test disc number in filename when artist is not specified"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config with disc number but no artist
        yaml_config = {
            "files": [
                {
                    "filename": "test.mp3",
                    "disc": 2,
                    "track": 5,
                    "title": "Title Only",
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

        # Verify filename includes disc number as 02-05 with double space before hyphen
        expected_filename = "02-05  - Title Only.mp3"
        assert Path(expected_filename).exists()

    def test_disc_number_padding(self):
        """Test that disc number is always 2 digits"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config with single-digit disc number
        yaml_config = {
            "files": [
                {
                    "filename": "test.mp3",
                    "disc": 9,
                    "track": 1,
                    "artist": "Artist",
                    "title": "Title",
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

        # Verify disc number is padded to 09
        expected_filename = "09-01 Artist - Title.mp3"
        assert Path(expected_filename).exists()

    def test_no_disc_number_in_filename(self):
        """Test that filename without disc number remains unchanged"""
        # Copy dummy MP3 to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        # Create YAML config without disc number
        yaml_config = {
            "files": [
                {
                    "filename": "test.mp3",
                    "track": 1,
                    "artist": "Artist",
                    "title": "Title",
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

        # Verify filename does not include disc number
        expected_filename = "01 Artist - Title.mp3"
        assert Path(expected_filename).exists()

    def test_multi_disc_album_with_different_disc_numbers(self):
        """Test multiple files with different disc numbers"""
        # Copy dummy MP3s to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "disc1.mp3"
        test_mp3_2 = Path(self.test_dir) / "disc2.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)

        # Create YAML config with different disc numbers
        yaml_config = {
            "defaults": {
                "album": "Multi-Disc Album",
            },
            "files": [
                {
                    "filename": "disc1.mp3",
                    "disc": 1,
                    "track": 1,
                    "artist": "Artist",
                    "title": "Disc 1 Track 1",
                },
                {
                    "filename": "disc2.mp3",
                    "disc": 2,
                    "track": 1,
                    "artist": "Artist",
                    "title": "Disc 2 Track 1",
                },
            ],
        }

        yaml_file = Path(self.test_dir) / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_config, f)

        # Apply tags
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.apply_yaml("test.yaml")

        # Verify filenames include different disc numbers
        expected_filename_1 = "01-01 Artist - Disc 1 Track 1.mp3"
        expected_filename_2 = "02-01 Artist - Disc 2 Track 1.mp3"
        assert Path(expected_filename_1).exists()
        assert Path(expected_filename_2).exists()
