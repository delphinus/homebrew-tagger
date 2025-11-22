#!/usr/bin/env python3
"""
DJ Mix Segmentation Module

Analyzes DJ mixes to detect track boundaries using audio feature analysis.
Outputs CUE sheets compatible with mp3DirectCut.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Enable parallel processing for numerical libraries
# This significantly speeds up similarity matrix computation
import multiprocessing

cpu_count = multiprocessing.cpu_count()
os.environ.setdefault("OMP_NUM_THREADS", str(cpu_count))
os.environ.setdefault("MKL_NUM_THREADS", str(cpu_count))
os.environ.setdefault("OPENBLAS_NUM_THREADS", str(cpu_count))
os.environ.setdefault("NUMEXPR_NUM_THREADS", str(cpu_count))

try:
    import librosa
    import numpy as np
except ImportError:
    print(
        "Error: librosa is not installed. Please install it with: pip install librosa",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from tracklist_parser import Track
except ImportError:
    # Define minimal Track class if tracklist_parser not available
    from dataclasses import dataclass

    @dataclass
    class Track:
        number: int
        artist: Optional[str] = None
        title: Optional[str] = None
        timestamp: Optional[float] = None


class DJMixSegmenter:
    """Analyzes DJ mixes to detect track boundaries"""

    def __init__(self, hop_length: int = 512, frame_length: int = 2048):
        """
        Initialize the segmenter.

        Args:
            hop_length: Number of samples between successive frames
            frame_length: Number of samples per frame
        """
        self.hop_length = hop_length
        self.frame_length = frame_length

    def load_audio(self, filepath: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file.

        Args:
            filepath: Path to audio file (.mp3, .m4a, .aac)

        Returns:
            Tuple of (audio data, sample rate)
        """
        try:
            y, sr = librosa.load(filepath, sr=None, mono=True)
            return y, sr
        except Exception as e:
            raise RuntimeError(f"Failed to load audio file: {e}")

    def detect_boundaries(
        self,
        y: np.ndarray,
        sr: int,
        sensitivity: float = 0.5,
        expected_count: Optional[int] = None,
    ) -> List[float]:
        """
        Detect track boundaries in the audio.

        This method uses multiple audio features to detect potential track transitions:
        - Spectral contrast: Detects changes in frequency distribution
        - Chroma features: Detects key/tonality changes
        - Temporal features: Detects rhythm/tempo changes

        Args:
            y: Audio time series
            sr: Sample rate
            sensitivity: Detection sensitivity (0.0-1.0). Higher = more sensitive
            expected_count: Expected number of tracks (if known from tracklist)

        Returns:
            List of boundary timestamps in seconds
        """
        print("Analyzing audio features...", file=sys.stderr)

        # 1. Spectral contrast - detects changes in frequency balance
        contrast = librosa.feature.spectral_contrast(
            y=y, sr=sr, hop_length=self.hop_length, n_bands=6
        )
        contrast_mean = np.mean(contrast, axis=0)

        # 2. Chroma features - detects key/tonality changes
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=self.hop_length)

        # 3. MFCC - detects timbral changes
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=self.hop_length)

        # Compute self-similarity matrix for chroma
        print("Computing similarity matrices...", file=sys.stderr)
        chroma_similarity = librosa.segment.recurrence_matrix(
            chroma, mode="affinity", metric="cosine", width=9
        )

        # Compute novelty curve from similarity matrix
        novelty = np.sqrt(
            librosa.segment.lag_to_recurrence(1 - chroma_similarity, axis=1).sum(
                axis=0
            )
        )

        # Normalize novelty curve
        novelty = (novelty - novelty.min()) / (novelty.max() - novelty.min() + 1e-8)

        # Detect peaks in novelty curve
        print("Detecting boundaries...", file=sys.stderr)

        # Adjust threshold based on sensitivity
        # Lower sensitivity = higher threshold = fewer boundaries
        threshold = 0.9 - (sensitivity * 0.6)  # Range: 0.3 to 0.9

        # Find peaks with minimum distance constraint (avoid too close boundaries)
        min_distance_frames = int(
            60 * sr / self.hop_length
        )  # Minimum 60 seconds between tracks

        # If expected_count is provided, use adaptive threshold
        if expected_count:
            print(
                f"Expected {expected_count} tracks, adjusting detection...",
                file=sys.stderr,
            )
            # We need (expected_count - 1) boundaries
            target_boundaries = expected_count - 1

            # Collect all potential peaks with their novelty values
            potential_peaks = []
            for i in range(1, len(novelty) - 1):
                if novelty[i] > novelty[i - 1] and novelty[i] > novelty[i + 1]:
                    potential_peaks.append((i, novelty[i]))

            # Sort by novelty value (descending)
            potential_peaks.sort(key=lambda x: x[1], reverse=True)

            # Select top N peaks, respecting minimum distance
            peaks = []
            for peak_idx, peak_val in potential_peaks:
                # Check minimum distance from all selected peaks
                too_close = False
                for selected_peak in peaks:
                    if abs(peak_idx - selected_peak) < min_distance_frames:
                        too_close = True
                        break

                if not too_close:
                    peaks.append(peak_idx)

                # Stop when we have enough boundaries
                if len(peaks) >= target_boundaries:
                    break

            # Sort peaks by time
            peaks.sort()
        else:
            # Original threshold-based detection
            peaks = []
            for i in range(1, len(novelty) - 1):
                if (
                    novelty[i] > threshold
                    and novelty[i] > novelty[i - 1]
                    and novelty[i] > novelty[i + 1]
                ):
                    # Check minimum distance from previous peak
                    if not peaks or (i - peaks[-1]) > min_distance_frames:
                        peaks.append(i)

        # Convert frame indices to timestamps
        boundaries = librosa.frames_to_time(
            peaks, sr=sr, hop_length=self.hop_length
        ).tolist()

        print(f"Found {len(boundaries)} boundaries", file=sys.stderr)
        return boundaries

    def analyze_mix(
        self,
        filepath: str,
        sensitivity: float = 0.5,
        tracklist: Optional[List[Track]] = None,
    ) -> List[float]:
        """
        Analyze a DJ mix and detect track boundaries.

        Args:
            filepath: Path to the DJ mix audio file
            sensitivity: Detection sensitivity (0.0-1.0)
            tracklist: Optional tracklist to guide detection

        Returns:
            List of boundary timestamps in seconds
        """
        print(f"Loading audio: {filepath}", file=sys.stderr)
        y, sr = self.load_audio(filepath)

        duration = librosa.get_duration(y=y, sr=sr)
        print(f"Duration: {duration:.1f} seconds", file=sys.stderr)

        # If tracklist has timestamps, use them directly
        if tracklist and any(t.timestamp is not None for t in tracklist):
            print("Using timestamps from tracklist", file=sys.stderr)
            boundaries = [t.timestamp for t in tracklist[1:] if t.timestamp is not None]
            print(f"Found {len(boundaries)} boundaries from tracklist", file=sys.stderr)
            return sorted(boundaries)

        # Otherwise, detect boundaries with optional track count constraint
        expected_count = len(tracklist) if tracklist else None
        boundaries = self.detect_boundaries(y, sr, sensitivity, expected_count)
        return boundaries


class CueSheetGenerator:
    """Generates CUE sheets compatible with mp3DirectCut"""

    @staticmethod
    def seconds_to_cue_time(seconds: float) -> str:
        """
        Convert seconds to CUE time format (MM:SS:FF).

        Args:
            seconds: Time in seconds

        Returns:
            String in format "MM:SS:FF" where FF is frames (1/75th of a second)
        """
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        secs = int(remaining_seconds)
        frames = int((remaining_seconds - secs) * 75)
        return f"{minutes:02d}:{secs:02d}:{frames:02d}"

    def generate_cue(
        self,
        audio_filepath: str,
        boundaries: List[float],
        output_filepath: str | None = None,
        tracklist: Optional[List[Track]] = None,
    ) -> str:
        """
        Generate a CUE sheet from boundary timestamps.

        Args:
            audio_filepath: Path to the audio file
            boundaries: List of boundary timestamps in seconds
            output_filepath: Optional path to save the CUE sheet
            tracklist: Optional tracklist with track names

        Returns:
            CUE sheet content as string
        """
        audio_path = Path(audio_filepath)
        audio_filename = audio_path.name

        # Detect file type
        ext = audio_path.suffix.lower()
        if ext == ".mp3":
            file_type = "MP3"
        elif ext in [".m4a", ".aac"]:
            file_type = "MP4"
        elif ext == ".wav":
            file_type = "WAVE"
        else:
            file_type = "MP3"  # Default

        # Start CUE sheet
        lines = []
        lines.append(f'FILE "{audio_filename}" {file_type}')

        # Get track info from tracklist if available
        def get_track_info(track_num: int) -> Tuple[Optional[str], Optional[str]]:
            """Get performer and title for track number"""
            if tracklist and track_num <= len(tracklist):
                track = tracklist[track_num - 1]
                return track.artist, track.title
            return None, None

        # Always start with track 01 at 00:00:00
        track_num = 1
        performer, title = get_track_info(track_num)

        lines.append(f"  TRACK {track_num:02d} AUDIO")
        if performer:
            lines.append(f'    PERFORMER "{performer}"')
        if title:
            lines.append(f'    TITLE "{title}"')
        elif not performer:
            lines.append(f'    TITLE "Track {track_num:02d}"')
        lines.append(f"    INDEX 01 00:00:00")

        # Add boundaries as subsequent tracks
        for boundary in boundaries:
            track_num += 1
            performer, title = get_track_info(track_num)
            cue_time = self.seconds_to_cue_time(boundary)

            lines.append(f"  TRACK {track_num:02d} AUDIO")
            if performer:
                lines.append(f'    PERFORMER "{performer}"')
            if title:
                lines.append(f'    TITLE "{title}"')
            elif not performer:
                lines.append(f'    TITLE "Track {track_num:02d}"')
            lines.append(f"    INDEX 01 {cue_time}")

        cue_content = "\n".join(lines) + "\n"

        # Save to file if requested
        if output_filepath:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(cue_content)
            print(f"CUE sheet saved to: {output_filepath}", file=sys.stderr)

        return cue_content


def segment_mix(
    audio_filepath: str,
    output_filepath: str | None = None,
    sensitivity: float = 0.5,
    tracklist: Optional[List[Track]] = None,
) -> str:
    """
    Segment a DJ mix and generate a CUE sheet.

    Args:
        audio_filepath: Path to the DJ mix audio file
        output_filepath: Path to save the CUE sheet (optional)
        sensitivity: Detection sensitivity (0.0-1.0, default 0.5)
        tracklist: Optional tracklist to guide segmentation

    Returns:
        CUE sheet content as string
    """
    # Analyze the mix
    segmenter = DJMixSegmenter()
    boundaries = segmenter.analyze_mix(audio_filepath, sensitivity, tracklist)

    # Generate CUE sheet
    generator = CueSheetGenerator()

    # Default output path if not specified
    if output_filepath is None:
        audio_path = Path(audio_filepath)
        output_filepath = str(audio_path.with_suffix(".cue"))

    cue_content = generator.generate_cue(
        audio_filepath, boundaries, output_filepath, tracklist
    )

    return cue_content


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Segment DJ mixes and generate CUE sheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a mix and generate CUE sheet
  python segmenter.py mix.mp3

  # Specify output file
  python segmenter.py mix.mp3 -o output.cue

  # Adjust sensitivity (0.0-1.0, default 0.5)
  python segmenter.py mix.mp3 --sensitivity 0.7

Note:
  Higher sensitivity values will detect more boundaries (more tracks).
  Lower sensitivity values will detect fewer boundaries (fewer tracks).
        """,
    )

    parser.add_argument("audio_file", help="Path to the DJ mix audio file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output CUE sheet file path (default: same as input with .cue extension)",
    )
    parser.add_argument(
        "-s",
        "--sensitivity",
        type=float,
        default=0.5,
        help="Detection sensitivity (0.0-1.0, default 0.5)",
    )

    args = parser.parse_args()

    # Validate sensitivity
    if not 0.0 <= args.sensitivity <= 1.0:
        print("Error: Sensitivity must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)

    try:
        segment_mix(args.audio_file, args.output, args.sensitivity)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
