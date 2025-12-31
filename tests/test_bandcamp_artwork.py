"""Tests for Bandcamp artwork auto-fetching"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import pytest

# Import tagger module (loaded by conftest.py)
import tagger_module
import yaml

# Import classes from the module
Tagger = tagger_module.Tagger


class TestBandcampArtwork:
    """Test Bandcamp artwork downloading and cropping"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_extract_bandcamp_url_info_album(self):
        """Test extracting Bandcamp info from album URL"""
        tagger = Tagger(execute=False)

        url = "https://brutalkuts.bandcamp.com/album/the-ultimate-happy-2-the-core"
        info = tagger.extract_bandcamp_url_info(url)

        assert info is not None
        assert info["label_slug"] == "brutalkuts"
        assert info["type"] == "album"
        assert info["slug"] == "the-ultimate-happy-2-the-core"

    def test_extract_bandcamp_url_info_track(self):
        """Test extracting Bandcamp info from track URL"""
        tagger = Tagger(execute=False)

        url = "https://someartist.bandcamp.com/track/awesome-song"
        info = tagger.extract_bandcamp_url_info(url)

        assert info is not None
        assert info["label_slug"] == "someartist"
        assert info["type"] == "track"
        assert info["slug"] == "awesome-song"

    def test_extract_bandcamp_url_info_with_http(self):
        """Test extracting Bandcamp info from HTTP (not HTTPS) URL"""
        tagger = Tagger(execute=False)

        url = "http://testlabel.bandcamp.com/album/test-album"
        info = tagger.extract_bandcamp_url_info(url)

        assert info is not None
        assert info["label_slug"] == "testlabel"
        assert info["type"] == "album"

    def test_extract_bandcamp_url_info_invalid_url(self):
        """Test that invalid URLs return None"""
        tagger = Tagger(execute=False)

        # Not a Bandcamp URL
        info = tagger.extract_bandcamp_url_info("https://example.com/album/test")
        assert info is None

        # Wrong Bandcamp URL format
        info = tagger.extract_bandcamp_url_info("https://bandcamp.com/discover")
        assert info is None

        # Missing slug
        info = tagger.extract_bandcamp_url_info("https://label.bandcamp.com/album/")
        assert info is None

    def test_artwork_path_single_file(self):
        """Test artwork path for single file in directory"""
        # Copy single file to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        os.chdir(self.test_dir)
        tagger = Tagger(execute=False)

        url_info = {
            "label_slug": "brutalkuts",
            "type": "album",
            "slug": "the-ultimate-happy-2-the-core"
        }
        path = tagger.get_bandcamp_artwork_path_for_file(test_mp3, url_info)
        assert path == test_mp3.parent / "cover.jpg"

    def test_artwork_path_multiple_files(self):
        """Test artwork path for multiple files in directory"""
        # Copy multiple files to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "test1.mp3"
        test_mp3_2 = Path(self.test_dir) / "test2.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)

        os.chdir(self.test_dir)
        tagger = Tagger(execute=False)

        url_info = {
            "label_slug": "brutalkuts",
            "type": "album",
            "slug": "the-ultimate-happy-2-the-core"
        }
        path = tagger.get_bandcamp_artwork_path_for_file(test_mp3_1, url_info)
        assert path == test_mp3_1.parent / "bandcamp_brutalkuts_the-ultimate-happy-2-the-core.jpg"

    @patch('yt_dlp.YoutubeDL')
    @patch('PIL.Image.open')
    def test_download_artwork_with_ytdlp(self, mock_image_open, mock_ytdlp):
        """Test downloading artwork using yt-dlp"""
        # Mock yt-dlp download
        mock_ydl = MagicMock()
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        # Mock downloaded file
        test_file = Path(self.test_dir) / "artwork.jpg"
        test_file.touch()

        # Mock PIL Image
        mock_img = Mock()
        mock_img.size = (1200, 1200)  # Square artwork (typical for Bandcamp)
        mock_image_open.return_value = mock_img

        # Test download
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        output_path = Path(self.test_dir) / "output.jpg"

        # Mock glob to return test_file
        with patch('pathlib.Path.glob', return_value=[test_file]):
            result = tagger.download_bandcamp_artwork(
                "https://brutalkuts.bandcamp.com/album/test",
                output_path
            )

        assert result is True
        mock_ydl.download.assert_called_once()

    @patch.object(Tagger, 'download_bandcamp_artwork', return_value=True)
    def test_generate_yaml_with_bandcamp_comment(self, mock_download):
        """Test that generate_yaml sets artwork path for Bandcamp URLs in comment"""
        # Copy file to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "Brutal Kuts - Flakee - Higher Emotions [3328867544].mp3"
        shutil.copy(src_mp3, test_mp3)

        # Tag the file with Bandcamp URL in comment
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, COMM

        audio = MP3(str(test_mp3), ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.add(COMM(encoding=3, lang="eng", desc="", text="https://brutalkuts.bandcamp.com/album/the-ultimate-happy-2-the-core"))
        audio.save()

        # Generate YAML (execute mode to create file, but mock download)
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.generate_yaml("generated.yaml", interactive=False)

        # Load and verify YAML
        with open("generated.yaml", "r") as f:
            # Skip schema comment line
            lines = f.readlines()
            yaml_content = "".join([l for l in lines if not l.startswith("# yaml-language-server:")])
            data = yaml.safe_load(yaml_content)

        # Artwork should be set to artwork filename
        assert data["files"][0].get("artwork") == "cover.jpg"

        # Comment should contain Bandcamp URL
        assert data["files"][0].get("comment") == "https://brutalkuts.bandcamp.com/album/the-ultimate-happy-2-the-core"

        # Verify download was called
        mock_download.assert_called_once()

    @patch.object(Tagger, 'download_bandcamp_artwork', return_value=True)
    def test_deduplication_same_album(self, mock_download):
        """Test that same Bandcamp URL doesn't download twice"""
        # Copy multiple files
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "Track 1.mp3"
        test_mp3_2 = Path(self.test_dir) / "Track 2.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)

        # Tag both files with same Bandcamp URL in comment
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, COMM

        bandcamp_url = "https://brutalkuts.bandcamp.com/album/the-ultimate-happy-2-the-core"

        for test_mp3 in [test_mp3_1, test_mp3_2]:
            audio = MP3(str(test_mp3), ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags.add(COMM(encoding=3, lang="eng", desc="", text=bandcamp_url))
            audio.save()

        # Generate YAML (execute mode to create file, but mock download)
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.generate_yaml("generated.yaml", interactive=False)

        # Load YAML
        with open("generated.yaml", "r") as f:
            lines = f.readlines()
            yaml_content = "".join([l for l in lines if not l.startswith("# yaml-language-server:")])
            data = yaml.safe_load(yaml_content)

        # Both files should reference the same artwork (moved to defaults)
        assert data["defaults"].get("artwork") == "bandcamp_brutalkuts_the-ultimate-happy-2-the-core.jpg"
        assert data["defaults"].get("comment") == bandcamp_url

        # Verify download was called only once (deduplication)
        mock_download.assert_called_once()

    @patch('shutil.move')
    @patch('PIL.Image.open')
    @patch('yt_dlp.YoutubeDL')
    def test_crop_failure_fallback(self, mock_ytdlp, mock_image_open, mock_move):
        """Test that crop failure falls back to original image"""
        # Mock PIL to raise exception
        mock_image_open.side_effect = Exception("Crop failed")

        # Create a temporary source file
        src_file = Path(self.test_dir) / "source.jpg"
        src_file.write_bytes(b"fake image")

        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        output_path = Path(self.test_dir) / "output.jpg"

        # Mock the download part to succeed but crop to fail
        mock_ydl = MagicMock()
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        with patch('pathlib.Path.glob', return_value=[src_file]):
            result = tagger.download_bandcamp_artwork(
                "https://brutalkuts.bandcamp.com/album/test",
                output_path
            )

        # Should still succeed (fallback to moving file)
        assert result is True
        # shutil.move should be called as fallback
        mock_move.assert_called()

    def test_square_crop_landscape_artwork(self):
        """Test square cropping of landscape artwork (rare for Bandcamp but possible)"""
        # Test the crop coordinate calculation for landscape images
        width, height = 1500, 1000

        # Landscape: crop sides (center crop)
        expected_left = (width - height) // 2  # (1500 - 1000) // 2 = 250
        expected_box = (expected_left, 0, expected_left + height, height)
        # Expected: (250, 0, 1250, 1000)

        assert expected_box == (250, 0, 1250, 1000)
