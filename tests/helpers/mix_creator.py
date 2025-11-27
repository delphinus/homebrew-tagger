"""
Helper module for creating test DJ mixes by concatenating audio files.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple
import json


def create_dj_mix(
    track_paths: List[str],
    output_path: str = None,
    crossfade: float = 0.0
) -> Tuple[str, List[float]]:
    """
    Create a DJ mix by concatenating audio files.

    Args:
        track_paths: List of paths to audio files to concatenate
        output_path: Output path for the mix (default: temp file)
        crossfade: Crossfade duration in seconds (default: 0.0 = no crossfade)

    Returns:
        Tuple of (mix_path, boundary_times)
        - mix_path: Path to the created mix file
        - boundary_times: List of boundary times in seconds (track start positions)

    Example:
        >>> mix_path, boundaries = create_dj_mix([
        ...     "track1.mp3",
        ...     "track2.mp3",
        ...     "track3.mp3"
        ... ])
        >>> print(f"Mix created at: {mix_path}")
        >>> print(f"Boundaries: {boundaries}")
    """
    if not track_paths:
        raise ValueError("At least one track path is required")

    for path in track_paths:
        if not Path(path).exists():
            raise FileNotFoundError(f"Track not found: {path}")

    # Create output file if not specified
    if output_path is None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_path = temp_file.name
        temp_file.close()

    # Get durations of each track
    durations = []
    for track_path in track_paths:
        duration = get_audio_duration(track_path)
        durations.append(duration)

    # Calculate boundary positions
    boundaries = []
    current_position = 0.0
    for i, duration in enumerate(durations[:-1]):  # Exclude last track
        current_position += duration - crossfade
        boundaries.append(current_position)

    # Create mix using ffmpeg
    if crossfade > 0:
        _create_mix_with_crossfade(track_paths, output_path, crossfade)
    else:
        _create_mix_simple_concat(track_paths, output_path)

    return output_path, boundaries


def _create_mix_simple_concat(track_paths: List[str], output_path: str) -> None:
    """
    Create mix by simple concatenation (no crossfade).

    Uses ffmpeg concat demuxer for fast, lossless concatenation.
    """
    # Create concat list file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        concat_file = f.name
        for track_path in track_paths:
            # Convert to absolute path for ffmpeg
            abs_path = Path(track_path).resolve()
            # Escape special characters for ffmpeg concat
            escaped_path = str(abs_path).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")

    try:
        # Use ffmpeg concat demuxer
        subprocess.run(
            [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",  # Copy codec (lossless)
                "-y",  # Overwrite output
                output_path
            ],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to create mix: {e.stderr}"
        ) from e
    finally:
        # Clean up concat file
        Path(concat_file).unlink()


def _create_mix_with_crossfade(
    track_paths: List[str],
    output_path: str,
    crossfade: float
) -> None:
    """
    Create mix with crossfade between tracks.

    Uses ffmpeg audio filters for crossfading.
    """
    if len(track_paths) < 2:
        # No crossfade needed for single track
        return _create_mix_simple_concat(track_paths, output_path)

    # Build complex filter for crossfading
    # This is more complex but creates smooth transitions
    filter_parts = []
    inputs = []

    for i, track_path in enumerate(track_paths):
        inputs.extend(["-i", track_path])
        if i == 0:
            filter_parts.append(f"[0:a]")
        else:
            filter_parts.append(
                f"[{i}:a]acrossfade=d={crossfade}:c1=tri:c2=tri[a{i}]"
            )
            if i < len(track_paths) - 1:
                filter_parts[-1] = f"[a{i-1}][{i}:a]acrossfade=d={crossfade}[a{i}]"

    # Construct ffmpeg command
    cmd = ["ffmpeg"] + inputs + [
        "-filter_complex",
        ";".join(filter_parts),
        "-y",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to create mix with crossfade: {e.stderr}"
        ) from e


def get_audio_duration(audio_path: str) -> float:
    """
    Get duration of an audio file in seconds.

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds

    Raises:
        RuntimeError: If ffprobe fails
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                audio_path
            ],
            check=True,
            capture_output=True,
            text=True
        )

        data = json.loads(result.stdout)
        return float(data["format"]["duration"])

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to get duration for {audio_path}: {e.stderr}"
        ) from e
    except (KeyError, ValueError) as e:
        raise RuntimeError(
            f"Failed to parse duration from {audio_path}"
        ) from e


def load_ncs_metadata() -> dict:
    """
    Load NCS track metadata from the fixtures directory.

    Returns:
        Dictionary containing track metadata

    Example:
        >>> metadata = load_ncs_metadata()
        >>> tracks = metadata["tracks"]
        >>> print(f"Track 1: {tracks[0]['artist']} - {tracks[0]['title']}")
    """
    metadata_path = Path(__file__).parent.parent / "fixtures/ncs/metadata.json"

    with open(metadata_path, "r") as f:
        return json.load(f)


def get_ncs_track_paths() -> List[str]:
    """
    Get paths to all NCS test tracks.

    Returns:
        List of absolute paths to NCS tracks in order

    Example:
        >>> track_paths = get_ncs_track_paths()
        >>> print(f"Found {len(track_paths)} tracks")
    """
    fixtures_dir = Path(__file__).parent.parent / "fixtures/ncs"
    metadata = load_ncs_metadata()

    tracks = []
    for track_info in metadata["tracks"]:
        track_path = fixtures_dir / track_info["filename"]
        if not track_path.exists():
            raise FileNotFoundError(
                f"NCS track not found: {track_path}"
            )
        tracks.append(str(track_path.resolve()))

    return tracks


def create_test_mix(output_path: str = None) -> Tuple[str, dict]:
    """
    Create a complete test DJ mix from NCS tracks.

    This is a convenience function that:
    1. Loads NCS track metadata
    2. Gets track paths
    3. Creates the mix
    4. Returns mix path and expected metadata

    Args:
        output_path: Optional output path (default: temp file)

    Returns:
        Tuple of (mix_path, expected_data)
        - mix_path: Path to created mix
        - expected_data: Dictionary with expected boundaries and track info

    Example:
        >>> mix_path, expected = create_test_mix()
        >>> print(f"Mix: {mix_path}")
        >>> print(f"Expected boundaries: {expected['boundaries']}")
        >>> print(f"Expected tracks: {len(expected['tracks'])}")
    """
    metadata = load_ncs_metadata()
    track_paths = get_ncs_track_paths()

    # Create the mix
    mix_path, boundaries = create_dj_mix(track_paths, output_path)

    # Prepare expected data for testing
    expected_data = {
        "mix_path": mix_path,
        "boundaries": boundaries,
        "tracks": metadata["tracks"],
        "total_duration": metadata["mix_info"]["total_duration"],
        "num_tracks": len(metadata["tracks"])
    }

    return mix_path, expected_data
