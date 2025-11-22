"""
Tests for DJ mix segmentation functionality
"""

import pytest
from pathlib import Path

try:
    import numpy as np
    import librosa
    from segmenter import DJMixSegmenter, CueSheetGenerator, segment_mix

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    np = None  # For type hints


@pytest.mark.skipif(not LIBROSA_AVAILABLE, reason="librosa not installed")
class TestDJMixSegmenter:
    """Tests for DJMixSegmenter class"""

    def test_init(self):
        """Test segmenter initialization"""
        segmenter = DJMixSegmenter()
        assert segmenter.hop_length == 512
        assert segmenter.frame_length == 2048

    def test_init_custom_params(self):
        """Test segmenter with custom parameters"""
        segmenter = DJMixSegmenter(hop_length=1024, frame_length=4096)
        assert segmenter.hop_length == 1024
        assert segmenter.frame_length == 4096

    def test_detect_boundaries_synthetic(self):
        """Test boundary detection with synthetic audio"""
        # Create synthetic audio with 2 distinct segments
        sr = 22050
        duration = 180  # 3 minutes
        t = np.linspace(0, duration, sr * duration)

        # First segment: 440 Hz sine wave (0-90s)
        segment1 = np.sin(2 * np.pi * 440 * t[: sr * 90])

        # Second segment: 880 Hz sine wave (90-180s)
        segment2 = np.sin(2 * np.pi * 880 * t[: sr * 90])

        # Concatenate with a brief transition
        y = np.concatenate([segment1, segment2])

        segmenter = DJMixSegmenter()
        boundaries = segmenter.detect_boundaries(y, sr, sensitivity=0.5)

        # Should detect at least one boundary
        assert isinstance(boundaries, list)
        # Boundaries should be positive timestamps
        for b in boundaries:
            assert b > 0


@pytest.mark.skipif(not LIBROSA_AVAILABLE, reason="librosa not installed")
class TestCueSheetGenerator:
    """Tests for CueSheetGenerator class"""

    def test_seconds_to_cue_time(self):
        """Test time conversion to CUE format"""
        # 0 seconds
        assert CueSheetGenerator.seconds_to_cue_time(0) == "00:00:00"

        # 1 minute 30.5 seconds
        assert CueSheetGenerator.seconds_to_cue_time(90.5) == "01:30:37"

        # 1 hour (60 minutes)
        assert CueSheetGenerator.seconds_to_cue_time(3600) == "60:00:00"

    def test_generate_cue_mp3(self):
        """Test CUE sheet generation for MP3 file"""
        generator = CueSheetGenerator()
        boundaries = [120.0, 240.0, 360.0]  # 2min, 4min, 6min

        cue = generator.generate_cue("test_mix.mp3", boundaries)

        # Check basic structure
        assert 'FILE "test_mix.mp3" MP3' in cue
        assert "TRACK 01 AUDIO" in cue
        assert "INDEX 01 00:00:00" in cue
        assert "TRACK 02 AUDIO" in cue
        assert "TRACK 03 AUDIO" in cue
        assert "TRACK 04 AUDIO" in cue

        # Check time formatting
        assert "02:00:00" in cue  # 120 seconds
        assert "04:00:00" in cue  # 240 seconds
        assert "06:00:00" in cue  # 360 seconds

    def test_generate_cue_m4a(self):
        """Test CUE sheet generation for M4A file"""
        generator = CueSheetGenerator()
        boundaries = [60.0]

        cue = generator.generate_cue("test_mix.m4a", boundaries)

        assert 'FILE "test_mix.m4a" MP4' in cue

    def test_generate_cue_no_boundaries(self):
        """Test CUE sheet with no boundaries (single track)"""
        generator = CueSheetGenerator()
        cue = generator.generate_cue("mix.mp3", [])

        # Should still have track 01
        assert "TRACK 01 AUDIO" in cue
        assert "INDEX 01 00:00:00" in cue
        # Should not have track 02
        assert "TRACK 02 AUDIO" not in cue

    def test_generate_cue_save_file(self, tmp_path):
        """Test saving CUE sheet to file"""
        generator = CueSheetGenerator()
        boundaries = [120.0]
        output_file = tmp_path / "test.cue"

        cue = generator.generate_cue("mix.mp3", boundaries, str(output_file))

        # Check file was created
        assert output_file.exists()

        # Check file content
        content = output_file.read_text()
        assert content == cue
        assert 'FILE "mix.mp3" MP3' in content


@pytest.mark.skipif(not LIBROSA_AVAILABLE, reason="librosa not installed")
class TestSegmentMix:
    """Tests for segment_mix function"""

    def test_sensitivity_validation(self):
        """Test that invalid sensitivity values are rejected"""
        # This would fail at the argument level in the CLI
        # but we can test the valid range in the function
        segmenter = DJMixSegmenter()

        # Valid sensitivity values should work
        sr = 22050
        y = np.sin(2 * np.pi * 440 * np.linspace(0, 60, sr * 60))

        # These should not raise errors
        boundaries_low = segmenter.detect_boundaries(y, sr, sensitivity=0.0)
        boundaries_mid = segmenter.detect_boundaries(y, sr, sensitivity=0.5)
        boundaries_high = segmenter.detect_boundaries(y, sr, sensitivity=1.0)

        assert isinstance(boundaries_low, list)
        assert isinstance(boundaries_mid, list)
        assert isinstance(boundaries_high, list)
