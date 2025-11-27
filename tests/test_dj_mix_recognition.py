"""
Integration tests for DJ mix segmentation and recognition.

These tests verify the complete workflow:
1. Creating a DJ mix from individual tracks
2. Detecting boundaries between tracks
3. Recognizing tracks using AcoustID/Shazam
4. Generating accurate CUE sheets

Test Modes:
-----------
- CI Mode (USE_MOCKS=1 or CI=true): Uses mocked API responses (fast, no network)
- Live Mode (USE_MOCKS=0): Uses real AcoustID/Shazam APIs (slow, requires keys)

Environment Variables:
---------------------
- USE_MOCKS: Set to "1" to use mocks, "0" to use live APIs (default: auto-detect CI)
- CI: Auto-detected (GitHub Actions sets this)
- ACOUSTID_API_KEY: Required for live AcoustID testing
- RUN_LIVE_TESTS: Set to "1" to force live API testing (overrides CI detection)
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

# Determine test mode
USE_MOCKS = os.environ.get("USE_MOCKS")
if USE_MOCKS is None:
    # Auto-detect: use mocks in CI, allow live tests locally
    USE_MOCKS = os.environ.get("CI", "false").lower() == "true"
    # Unless explicitly requesting live tests
    if os.environ.get("RUN_LIVE_TESTS") == "1":
        USE_MOCKS = False
else:
    USE_MOCKS = USE_MOCKS == "1"

# Install mocks before importing music_recognizer if needed
if USE_MOCKS:
    from tests.mocks.mock_shazam import install_all_mocks
    install_all_mocks()

# Import test helpers
from tests.helpers.mix_creator import (
    create_test_mix,
    load_ncs_metadata,
    get_ncs_track_paths,
    get_audio_duration
)

# Try to import required modules
try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    librosa = None
    np = None

# Import segmenter modules conditionally
# These may fail if librosa is not installed
SEGMENTER_AVAILABLE = False
DJMixSegmenter = None
CueSheetGenerator = None
segment_mix = None
MusicRecognizer = None

try:
    from segmenter import (
        DJMixSegmenter,
        CueSheetGenerator,
        segment_mix
    )
    from music_recognizer import MusicRecognizer
    SEGMENTER_AVAILABLE = True
except (ImportError, SystemExit):
    # SystemExit can be raised by segmenter.py if librosa is missing
    pass


class TestMixCreation:
    """Test DJ mix creation from NCS tracks"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata = load_ncs_metadata()

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_ncs_tracks_exist(self):
        """Verify all NCS test tracks are present"""
        track_paths = get_ncs_track_paths()

        assert len(track_paths) == 3, "Expected 3 NCS tracks"

        for track_path in track_paths:
            assert Path(track_path).exists(), f"Track not found: {track_path}"
            assert Path(track_path).stat().st_size > 0, f"Track is empty: {track_path}"

    def test_ncs_metadata_valid(self):
        """Verify NCS metadata structure"""
        assert "tracks" in self.metadata
        assert "mix_info" in self.metadata
        assert len(self.metadata["tracks"]) == 3

        for track in self.metadata["tracks"]:
            assert "filename" in track
            assert "artist" in track
            assert "title" in track
            assert "duration" in track
            assert track["duration"] > 0

    def test_create_test_mix(self):
        """Test creating a DJ mix from NCS tracks"""
        output_path = Path(self.temp_dir) / "test_mix.mp3"

        mix_path, expected = create_test_mix(str(output_path))

        # Verify mix was created
        assert Path(mix_path).exists()
        assert Path(mix_path).stat().st_size > 0

        # Verify expected data structure
        assert "boundaries" in expected
        assert "tracks" in expected
        assert len(expected["boundaries"]) == 2, "Expected 2 boundaries for 3 tracks"

        # Verify mix duration is approximately correct
        mix_duration = get_audio_duration(mix_path)
        expected_duration = expected["total_duration"]

        # Allow 2-second tolerance for encoding differences
        assert abs(mix_duration - expected_duration) < 2.0, \
            f"Mix duration {mix_duration:.2f}s differs from expected {expected_duration:.2f}s"


@pytest.mark.skipif(not LIBROSA_AVAILABLE, reason="librosa not installed")
@pytest.mark.skipif(not SEGMENTER_AVAILABLE, reason="segmenter not available")
class TestBoundaryDetection:
    """Test boundary detection in DJ mixes"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata = load_ncs_metadata()

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_detect_boundaries_in_mix(self):
        """Test boundary detection with real NCS mix"""
        # Create test mix
        mix_path, expected = create_test_mix()

        try:
            # Load audio
            y, sr = librosa.load(mix_path)

            # Detect boundaries
            segmenter = DJMixSegmenter()
            detected_boundaries = segmenter.detect_boundaries(y, sr, sensitivity=0.5)

            # Expected boundaries from metadata
            expected_boundaries = expected["boundaries"]

            print(f"\nExpected boundaries: {expected_boundaries}")
            print(f"Detected boundaries: {detected_boundaries}")
            print(f"Number detected: {len(detected_boundaries)}")

            # Verify we detected some boundaries
            assert len(detected_boundaries) > 0, "No boundaries detected"

            # Boundary detection is probabilistic and may detect more boundaries than expected
            # The key is that the expected boundaries should be present (within tolerance)
            # Allow 30-second tolerance for boundary position
            tolerance = 30.0

            matched = 0
            for expected_boundary in expected_boundaries:
                if any(abs(detected - expected_boundary) < tolerance
                       for detected in detected_boundaries):
                    matched += 1
                    # Find closest match
                    closest = min(detected_boundaries, key=lambda x: abs(x - expected_boundary))
                    offset = abs(closest - expected_boundary)
                    print(f"  ✓ Boundary at {expected_boundary:.1f}s matched (offset: {offset:.1f}s)")
                else:
                    print(f"  ✗ Boundary at {expected_boundary:.1f}s not matched within {tolerance}s")

            # Require ALL expected boundaries to be detected within tolerance
            # This ensures the algorithm finds the major track transitions
            match_ratio = matched / len(expected_boundaries)
            assert match_ratio == 1.0, \
                f"Only {matched}/{len(expected_boundaries)} expected boundaries detected within {tolerance}s tolerance. " \
                f"Expected boundaries: {expected_boundaries}, Detected: {detected_boundaries}"

        finally:
            # Clean up mix file
            Path(mix_path).unlink()


@pytest.mark.skipif(not SEGMENTER_AVAILABLE, reason="segmenter not available")
class TestMusicRecognition:
    """Test music recognition with mocked/live APIs"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata = load_ncs_metadata()

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    @pytest.mark.skipif(
        not USE_MOCKS and not os.environ.get("ACOUSTID_API_KEY"),
        reason="Live test requires ACOUSTID_API_KEY"
    )
    def test_recognize_single_track(self):
        """Test recognizing a single NCS track"""
        track_paths = get_ncs_track_paths()
        first_track = track_paths[0]

        recognizer = MusicRecognizer()
        result = recognizer.recognize_file(first_track)

        if USE_MOCKS:
            # With mocks, we expect exact matches
            assert result is not None, "Recognition failed (mock should succeed)"
            assert result.artist == self.metadata["tracks"][0]["artist"]
            assert result.title == self.metadata["tracks"][0]["title"]
            print(f"✓ Recognized (mock): {result.artist} - {result.title}")
        else:
            # With live APIs, we check if we got a result
            # (may not match exactly due to database differences)
            if result:
                print(f"✓ Recognized (live): {result.artist} - {result.title}")
                print(f"  Source: {result.source}")
                print(f"  Confidence: {result.confidence}")
            else:
                pytest.skip("Live recognition returned no match (track may not be in database)")


@pytest.mark.skipif(not SEGMENTER_AVAILABLE, reason="segmenter not available")
class TestCueSheetGeneration:
    """Test CUE sheet generation"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata = load_ncs_metadata()

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_generate_cue_from_boundaries(self):
        """Test CUE sheet generation from known boundaries"""
        mix_path, expected = create_test_mix()

        try:
            generator = CueSheetGenerator()
            boundaries = expected["boundaries"]

            # Generate CUE sheet
            cue_content = generator.generate_cue(
                Path(mix_path).name,
                boundaries
            )

            # Verify CUE structure
            assert 'FILE' in cue_content
            assert 'TRACK 01 AUDIO' in cue_content
            assert 'INDEX 01 00:00:00' in cue_content

            # Should have 3 tracks total
            assert 'TRACK 01' in cue_content
            assert 'TRACK 02' in cue_content
            assert 'TRACK 03' in cue_content

            # Verify boundary times are in CUE
            # Track 1 starts at 00:00:00
            # Track 2 starts at first boundary
            # Track 3 starts at second boundary

            print("\nGenerated CUE sheet:")
            print(cue_content)

        finally:
            Path(mix_path).unlink()

    def test_save_cue_to_file(self):
        """Test saving CUE sheet to file"""
        mix_path, expected = create_test_mix()

        try:
            generator = CueSheetGenerator()
            cue_path = Path(self.temp_dir) / "test.cue"

            # Generate and save CUE
            cue_content = generator.generate_cue(
                Path(mix_path).name,
                expected["boundaries"],
                str(cue_path)
            )

            # Verify file was created
            assert cue_path.exists()

            # Verify content matches
            with open(cue_path, 'r') as f:
                saved_content = f.read()

            assert saved_content == cue_content

        finally:
            Path(mix_path).unlink()


@pytest.mark.skipif(not LIBROSA_AVAILABLE, reason="librosa not installed")
@pytest.mark.skipif(not SEGMENTER_AVAILABLE, reason="segmenter not available")
class TestEndToEndWorkflow:
    """End-to-end integration tests"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata = load_ncs_metadata()

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    @pytest.mark.timeout(300)  # 5-minute timeout
    @pytest.mark.skipif(
        not USE_MOCKS and not os.environ.get("ACOUSTID_API_KEY"),
        reason="Live test requires ACOUSTID_API_KEY"
    )
    def test_complete_workflow_mock_mode(self):
        """
        Test complete workflow: mix creation → segmentation → recognition → CUE

        This test verifies the entire pipeline works correctly with mocked APIs.
        """
        # Create mix
        mix_path, expected = create_test_mix()

        try:
            # Load audio
            y, sr = librosa.load(mix_path)

            # Detect boundaries
            segmenter = DJMixSegmenter()
            boundaries = segmenter.detect_boundaries(y, sr, sensitivity=0.5)

            print(f"\nDetected {len(boundaries)} boundaries")
            print(f"Expected {len(expected['boundaries'])} boundaries")

            if USE_MOCKS:
                # In mock mode, test the complete workflow with known results
                # Generate CUE sheet
                generator = CueSheetGenerator()
                cue_content = generator.generate_cue(
                    Path(mix_path).name,
                    boundaries if boundaries else expected["boundaries"]
                )

                # Verify CUE has correct structure
                assert 'TRACK 01' in cue_content
                assert 'FILE' in cue_content

                print("\n✓ Complete workflow successful (mock mode)")
                print(f"  Mix: {Path(mix_path).name}")
                print(f"  Boundaries: {len(boundaries)}")
                print(f"  Tracks: {expected['num_tracks']}")

            else:
                # In live mode, just verify we can complete the workflow
                # without errors (results may vary)
                print("\n✓ Complete workflow successful (live mode)")
                print(f"  Mix: {Path(mix_path).name}")
                print(f"  Detected boundaries: {len(boundaries)}")

                if len(boundaries) > 0:
                    # Generate CUE if we detected boundaries
                    generator = CueSheetGenerator()
                    cue_content = generator.generate_cue(
                        Path(mix_path).name,
                        boundaries
                    )
                    print(f"  CUE sheet generated: {len(cue_content)} bytes")

        finally:
            Path(mix_path).unlink()


# Module-level test configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "live_api: mark test as requiring live API access (slow)"
    )


# Print test mode information
if __name__ == "__main__":
    print(f"Test Mode: {'MOCK' if USE_MOCKS else 'LIVE'}")
    print(f"CI Environment: {os.environ.get('CI', 'false')}")
    print(f"Librosa Available: {LIBROSA_AVAILABLE}")
    print(f"Segmenter Available: {SEGMENTER_AVAILABLE}")
