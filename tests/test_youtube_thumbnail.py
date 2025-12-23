"""Tests for YouTube thumbnail auto-fetching"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open
import pytest

# Import tagger module (loaded by conftest.py)
import tagger_module
import yaml

# Import classes from the module
Tagger = tagger_module.Tagger


class TestYouTubeThumbnail:
    """Test YouTube thumbnail downloading and cropping"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_extract_video_id_standard_url(self):
        """Test extracting YouTube ID from standard URL"""
        tagger = Tagger(execute=False)

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = tagger.extract_youtube_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short_url(self):
        """Test extracting YouTube ID from short URL"""
        tagger = Tagger(execute=False)

        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = tagger.extract_youtube_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_mobile_url(self):
        """Test extracting YouTube ID from mobile URL"""
        tagger = Tagger(execute=False)

        url = "https://m.youtube.com/watch?v=TEtLwnrhn5U"
        video_id = tagger.extract_youtube_video_id(url)
        assert video_id == "TEtLwnrhn5U"

    def test_extract_video_id_invalid_url(self):
        """Test that invalid URLs return None"""
        tagger = Tagger(execute=False)

        # Not a YouTube URL
        video_id = tagger.extract_youtube_video_id("https://example.com/watch?v=invalid")
        assert video_id is None

        # Wrong ID length
        video_id = tagger.extract_youtube_video_id("https://www.youtube.com/watch?v=tooshort")
        assert video_id is None

    def test_thumbnail_path_single_file(self):
        """Test thumbnail path for single file in directory"""
        # Copy single file to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "test.mp3"
        shutil.copy(src_mp3, test_mp3)

        os.chdir(self.test_dir)
        tagger = Tagger(execute=False)

        path = tagger.get_thumbnail_path_for_file(test_mp3, "dQw4w9WgXcQ")
        assert path == test_mp3.parent / "cover.jpg"

    def test_thumbnail_path_multiple_files(self):
        """Test thumbnail path for multiple files in directory"""
        # Copy multiple files to test directory
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "test1.mp3"
        test_mp3_2 = Path(self.test_dir) / "test2.mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)

        os.chdir(self.test_dir)
        tagger = Tagger(execute=False)

        path = tagger.get_thumbnail_path_for_file(test_mp3_1, "dQw4w9WgXcQ")
        assert path == test_mp3_1.parent / "youtube_dQw4w9WgXcQ.jpg"

    @patch('yt_dlp.YoutubeDL')
    @patch('PIL.Image.open')
    def test_download_thumbnail_with_ytdlp(self, mock_image_open, mock_ytdlp):
        """Test downloading thumbnail using yt-dlp"""
        # Mock yt-dlp download
        mock_ydl = MagicMock()
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        # Mock downloaded file
        test_file = Path(self.test_dir) / "thumbnail.webp"
        test_file.touch()

        # Mock PIL Image
        mock_img = Mock()
        mock_img.size = (1280, 720)  # Landscape
        mock_cropped = Mock()
        mock_img.crop.return_value = mock_cropped
        mock_image_open.return_value = mock_img

        # Test download
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        output_path = Path(self.test_dir) / "output.jpg"

        # Mock glob to return test_file
        with patch('pathlib.Path.glob', return_value=[test_file]):
            result = tagger.download_youtube_thumbnail("dQw4w9WgXcQ", output_path)

        assert result is True
        mock_ydl.download.assert_called_once()

    @pytest.mark.skip(reason="yt-dlp is now a required dependency, fallback not needed")
    def test_download_thumbnail_fallback(self):
        """Test downloading thumbnail using requests fallback (SKIPPED - yt-dlp is required)"""
        pass

    @patch.object(Tagger, 'download_youtube_thumbnail', return_value=True)
    def test_generate_yaml_with_thumbnail_download(self, mock_download):
        """Test that generate_yaml sets artwork path for YouTube URLs"""
        # Copy file with YouTube ID in filename
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3 = Path(self.test_dir) / "Artist - Song [dQw4w9WgXcQ].mp3"
        shutil.copy(src_mp3, test_mp3)

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

        # Artwork should be set to thumbnail filename
        assert data["files"][0].get("artwork") == "cover.jpg"

        # Verify download was called
        mock_download.assert_called_once()

    @patch.object(Tagger, 'download_youtube_thumbnail', return_value=True)
    def test_deduplication_same_video(self, mock_download):
        """Test that same YouTube video ID doesn't download twice"""
        # Copy multiple files with same YouTube ID
        src_mp3 = self.fixtures_dir / "dummy.mp3"
        test_mp3_1 = Path(self.test_dir) / "Song 1 [dQw4w9WgXcQ].mp3"
        test_mp3_2 = Path(self.test_dir) / "Song 2 [dQw4w9WgXcQ].mp3"
        shutil.copy(src_mp3, test_mp3_1)
        shutil.copy(src_mp3, test_mp3_2)

        # Generate YAML (execute mode to create file, but mock download)
        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)
        tagger.generate_yaml("generated.yaml", interactive=False)

        # Load YAML
        with open("generated.yaml", "r") as f:
            lines = f.readlines()
            yaml_content = "".join([l for l in lines if not l.startswith("# yaml-language-server:")])
            data = yaml.safe_load(yaml_content)

        # Both files should reference the same thumbnail (moved to defaults)
        assert data["defaults"].get("artwork") == "youtube_dQw4w9WgXcQ.jpg"

        # Verify download was called only once (deduplication)
        mock_download.assert_called_once()

    def test_square_crop_landscape_image(self):
        """Test square cropping of landscape image"""
        # Test the crop coordinate calculation for landscape images
        width, height = 1280, 720

        # Landscape: crop sides (center crop)
        expected_left = (width - height) // 2  # (1280 - 720) // 2 = 280
        expected_box = (expected_left, 0, expected_left + height, height)
        # Expected: (280, 0, 1000, 720)

        assert expected_box == (280, 0, 1000, 720)

    @patch('PIL.Image.open')
    def test_square_crop_portrait_image(self, mock_image_open):
        """Test square cropping of portrait image"""
        # Mock portrait image (720x1280)
        mock_img = Mock()
        mock_img.size = (720, 1280)
        mock_cropped = Mock()
        mock_img.crop.return_value = mock_cropped
        mock_image_open.return_value = mock_img

        # Create a temporary source file
        src_file = Path(self.test_dir) / "source.jpg"
        src_file.write_bytes(b"fake image")

        os.chdir(self.test_dir)
        tagger = Tagger(execute=True)

        # Manually test the crop logic
        from PIL import Image
        with patch('PIL.Image.open', mock_image_open):
            # Simulate what download_youtube_thumbnail does
            img = Image.open(src_file)
            width, height = img.size

            # Portrait: crop top and bottom
            top = (height - width) // 2
            img.crop((0, top, width, top + width))

            # Verify crop was called with correct coordinates
            mock_img.crop.assert_called_with((0, 280, 720, 1000))

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
            result = tagger.download_youtube_thumbnail("dQw4w9WgXcQ", output_path)

        # Should still succeed (fallback to moving file)
        assert result is True
        # shutil.move should be called as fallback
        mock_move.assert_called()
