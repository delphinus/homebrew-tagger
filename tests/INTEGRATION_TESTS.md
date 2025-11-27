# Integration Tests Guide

This document describes the integration tests for DJ mix segmentation and recognition.

## Overview

The integration tests verify the complete workflow:

1. **Mix Creation**: Concatenate NCS tracks into a test DJ mix
2. **Boundary Detection**: Detect track boundaries using librosa
3. **Music Recognition**: Recognize tracks using AcoustID/Shazam
4. **CUE Generation**: Generate CUE sheets with correct timing

## Test Modes

### CI Mode (Mocked APIs)

In CI environments, tests use mocked API responses for fast, deterministic testing.

**Activated when:**
- `CI=true` environment variable (automatic in GitHub Actions)
- `USE_MOCKS=1` environment variable

**Behavior:**
- No network calls to external APIs
- Deterministic results based on NCS metadata
- Fast execution (~30-60 seconds)

### Live Mode (Real APIs)

For local development, tests can use real AcoustID and Shazam APIs.

**Activated when:**
- `USE_MOCKS=0` environment variable
- `RUN_LIVE_TESTS=1` environment variable

**Requirements:**
- `ACOUSTID_API_KEY` environment variable must be set
- Internet connection required
- Slower execution (~2-5 minutes)

## Running Tests

### Quick Start (Mocked APIs)

```bash
# Run all integration tests with mocks
USE_MOCKS=1 pytest tests/test_dj_mix_recognition.py -v

# Run specific test class
USE_MOCKS=1 pytest tests/test_dj_mix_recognition.py::TestMixCreation -v

# Run with timeout protection
USE_MOCKS=1 pytest tests/test_dj_mix_recognition.py --timeout=300 -v
```

### Live API Testing

```bash
# Set your AcoustID API key (get from https://acoustid.org/new-application)
export ACOUSTID_API_KEY="your-key-here"

# Run tests with live APIs
USE_MOCKS=0 pytest tests/test_dj_mix_recognition.py -v

# Or force live testing
RUN_LIVE_TESTS=1 pytest tests/test_dj_mix_recognition.py -v
```

### CI Environment

Tests run automatically in GitHub Actions via `.github/workflows/integration-tests.yml`:

```yaml
# Triggered on:
# - Push to main branch
# - Pull requests to main
# - Manual workflow dispatch
```

## Test Structure

### Test Classes

1. **TestMixCreation**
   - Verify NCS tracks exist and are valid
   - Test mix creation from individual tracks
   - Validate mix duration and metadata

2. **TestBoundaryDetection**
   - Test boundary detection with real audio
   - Verify detected boundaries match expected positions (±10s tolerance)
   - Requires at least 50% accuracy for boundaries

3. **TestMusicRecognition**
   - Test single track recognition
   - Mock mode: Expect exact matches with NCS metadata
   - Live mode: Accept any valid recognition result

4. **TestCueSheetGeneration**
   - Test CUE sheet generation from boundaries
   - Verify CUE structure and track positions
   - Test saving CUE to file

5. **TestEndToEndWorkflow**
   - Complete pipeline test: mix → segment → recognize → CUE
   - Timeout: 5 minutes
   - Full workflow verification

## Test Data

### NCS Tracks

Located in `tests/fixtures/ncs/`:

| Track | Artist | Title | Duration | Size |
|-------|--------|-------|----------|------|
| track1 | Tobu | Candyland | 3:18 | 3.0 MB |
| track2 | Spektrem | Shine | 4:19 | 5.9 MB |
| track3 | Different Heaven & EH!DE | My Heart | 4:27 | 6.1 MB |

**Total**: ~15 MB, ~12 minutes of audio

### Expected Results

When tracks are concatenated:
- **Boundary 1**: ~198 seconds (after track 1)
- **Boundary 2**: ~457 seconds (after track 2)
- **Total Duration**: ~724 seconds

See `tests/fixtures/ncs/metadata.json` for complete metadata.

## Helper Modules

### tests/helpers/mix_creator.py

Provides utilities for mix creation and metadata management:

```python
from tests.helpers.mix_creator import create_test_mix, load_ncs_metadata

# Create a test mix
mix_path, expected = create_test_mix()

# Load NCS metadata
metadata = load_ncs_metadata()
tracks = metadata["tracks"]
```

**Functions:**
- `create_test_mix()` - Create DJ mix from NCS tracks
- `load_ncs_metadata()` - Load track metadata
- `get_ncs_track_paths()` - Get paths to NCS tracks
- `get_audio_duration()` - Get audio file duration

### tests/mocks/mock_acoustid.py

Mock implementation of the acoustid module:

```python
from tests.mocks.mock_shazam import install_all_mocks

# Install both mocks (AcoustID + Shazam)
install_all_mocks()

# Now import music_recognizer (will use mocks)
from music_recognizer import MusicRecognizer
```

### tests/mocks/mock_shazam.py

Mock implementation of the shazamio module with helper function to install all mocks at once.

## Troubleshooting

### Tests Skip with "librosa not installed"

Install librosa:
```bash
pip install librosa numpy
```

### Tests Skip with "segmenter not available"

Ensure you're in the project directory and segmenter.py is accessible:
```bash
export PYTHONPATH=$PWD
```

### Live Tests Skip with "requires ACOUSTID_API_KEY"

Get an API key from https://acoustid.org/new-application and set it:
```bash
export ACOUSTID_API_KEY="your-key-here"
```

### Boundary Detection Fails

This is expected in some cases:
- Boundary detection is probabilistic
- Tests allow ±10 second tolerance
- Only require 50% accuracy
- Adjust `sensitivity` parameter in `DJMixSegmenter` if needed

### Mock Import Errors

Ensure mocks are installed before importing music_recognizer:
```python
# Correct order
if USE_MOCKS:
    from tests.mocks.mock_shazam import install_all_mocks
    install_all_mocks()

# Then import
from music_recognizer import MusicRecognizer
```

## Extending Tests

### Adding New Test Tracks

1. Download copyright-free music (preferably NCS)
2. Add to `tests/fixtures/ncs/`
3. Update `metadata.json` with track info
4. Regenerate expected boundaries
5. Update mocks to include new metadata

### Adding New Test Cases

```python
@pytest.mark.skipif(not LIBROSA_AVAILABLE, reason="librosa not installed")
def test_custom_scenario(self):
    """Test custom boundary detection scenario"""
    # Your test logic here
    pass
```

### Testing with Different Audio Formats

Currently supports MP3. To add M4A/FLAC:

1. Download test tracks in desired format
2. Update `create_dj_mix()` to handle format
3. Update CUE generator for format detection
4. Add format-specific tests

## Performance Benchmarks

Typical execution times (Apple M1, Python 3.13):

| Test Mode | Duration | Network | API Calls |
|-----------|----------|---------|-----------|
| Mock | ~30-45s | No | 0 |
| Live (AcoustID) | ~2-3 min | Yes | 3-6 |
| Live (Shazam) | ~3-5 min | Yes | 3-6 |

## Continuous Integration

Integration tests run on every PR and push to main:

**Workflow**: `.github/workflows/integration-tests.yml`

**Steps:**
1. Install system dependencies (ffmpeg, libchromaprint)
2. Install Python dependencies
3. Verify NCS test fixtures exist
4. Run tests with mocks
5. Upload artifacts on failure

**Timeout**: 5 minutes per test
**Retention**: Test artifacts kept for 7 days

## License & Attribution

Test audio from NoCopyrightSounds:
- License: Free to use with credit
- Commercial use: Allowed
- See: `tests/fixtures/ncs/README.md`

Sources:
- [Tobu - Candyland](https://ncs.io/candyland)
- [Spektrem - Shine](https://ncs.io/shine)
- [Different Heaven & EH!DE - My Heart](https://ncs.io/myheart)
