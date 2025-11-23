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

# Enable parallel processing for numerical libraries and scikit-learn
# This significantly speeds up similarity matrix computation
import multiprocessing

cpu_count = multiprocessing.cpu_count()
# Apple Accelerate (used by numpy/scipy on macOS)
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", str(cpu_count))
# OpenBLAS/MKL (used on Linux/other platforms)
os.environ.setdefault("OMP_NUM_THREADS", str(cpu_count))
os.environ.setdefault("MKL_NUM_THREADS", str(cpu_count))
os.environ.setdefault("OPENBLAS_NUM_THREADS", str(cpu_count))
os.environ.setdefault("NUMEXPR_NUM_THREADS", str(cpu_count))
# joblib/scikit-learn parallelization (used by librosa's recurrence_matrix)
os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(cpu_count))

# Also set threadpoolctl to use all cores
try:
    import threadpoolctl
    # This will affect BLAS/LAPACK libraries after they're loaded
    threadpoolctl.threadpool_limits(limits=cpu_count)
except ImportError:
    pass

try:
    import librosa
    import numpy as np
    import sklearn.neighbors
except ImportError:
    print(
        "Error: librosa is not installed. Please install it with: pip install librosa",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    # Fallback: simple progress indicator
    class tqdm:
        def __init__(self, iterable=None, desc=None, total=None, disable=False, **kwargs):
            self.iterable = iterable
            self.desc = desc
            self.total = total
            self.disable = disable
            self.n = 0
            if desc and not disable:
                print(f"{desc}...", file=sys.stderr, flush=True)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            if not self.disable:
                print(" Done.", file=sys.stderr, flush=True)

        def __iter__(self):
            return iter(self.iterable)

        def update(self, n=1):
            self.n += n

        def set_postfix(self, **kwargs):
            pass

        def set_postfix_str(self, s):
            pass


# Spinner utility for showing progress during long operations
class Spinner:
    """Displays a spinning animation during long operations"""

    def __init__(self, message: str):
        self.message = message
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.i = 0
        self.stop_spinner = False
        self.thread = None

    def __enter__(self):
        import threading
        import time

        def show_spinner():
            while not self.stop_spinner:
                print(
                    f"\r{self.spinner_chars[self.i % len(self.spinner_chars)]} {self.message}...",
                    end="",
                    file=sys.stderr,
                    flush=True,
                )
                self.i += 1
                time.sleep(0.1)
            print(f"\r✓ {self.message}" + " " * 30, file=sys.stderr, flush=True)

        self.stop_spinner = False
        self.thread = threading.Thread(target=show_spinner, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop_spinner = True
        if self.thread:
            self.thread.join(timeout=0.5)


# Helper function for track matching/similarity
def calculate_string_similarity(str1: Optional[str], str2: Optional[str]) -> float:
    """
    Calculate similarity between two strings using a simple word-based approach.

    Returns a value between 0.0 (completely different) and 1.0 (identical).
    """
    if str1 is None or str2 is None:
        return 0.0

    # Normalize strings: lowercase and split into words
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())

    if not words1 and not words2:
        return 1.0  # Both empty
    if not words1 or not words2:
        return 0.0  # One empty

    # Calculate Jaccard similarity (intersection over union)
    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def calculate_track_match_score(
    recognized_artist: Optional[str],
    recognized_title: Optional[str],
    tracklist_artist: Optional[str],
    tracklist_title: Optional[str],
) -> float:
    """
    Calculate overall match score between recognized track and tracklist entry.

    Returns a value between 0.0 (no match) and 1.0 (perfect match).
    """
    artist_similarity = calculate_string_similarity(recognized_artist, tracklist_artist)
    title_similarity = calculate_string_similarity(recognized_title, tracklist_title)

    # Weight title more heavily (0.6) than artist (0.4)
    # since titles are more specific
    return (artist_similarity * 0.4) + (title_similarity * 0.6)


# Monkey-patch sklearn.neighbors.NearestNeighbors to use all CPU cores
# This makes librosa's recurrence_matrix use parallel processing
_original_nn_init = sklearn.neighbors.NearestNeighbors.__init__


def _parallel_nn_init(self, n_neighbors=5, *, radius=1.0, algorithm="auto", leaf_size=30, metric="minkowski", p=2, metric_params=None, n_jobs=None, **kwargs):
    """Patched __init__ that defaults n_jobs to all CPU cores"""
    if n_jobs is None:
        n_jobs = cpu_count
    _original_nn_init(self, n_neighbors=n_neighbors, radius=radius, algorithm=algorithm, leaf_size=leaf_size, metric=metric, p=p, metric_params=metric_params, n_jobs=n_jobs, **kwargs)


# Replace the __init__ method
sklearn.neighbors.NearestNeighbors.__init__ = _parallel_nn_init

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
            import warnings

            # Capture warnings to provide user-friendly messages
            warning_list = []
            def warning_handler(message, category, filename, lineno, file=None, line=None):
                warning_list.append((str(message), category.__name__))

            old_showwarning = warnings.showwarning
            warnings.showwarning = warning_handler

            try:
                y, sr = librosa.load(filepath, sr=None, mono=True)
            finally:
                warnings.showwarning = old_showwarning

            # Show user-friendly messages for any warnings that occurred
            file_ext = Path(filepath).suffix.lower()
            for msg, category in warning_list:
                if "PySoundFile failed" in msg or "audioread" in msg.lower():
                    if file_ext in ['.m4a', '.aac', '.mp4']:
                        print(f"Info: Using audioread backend for {file_ext} file (native format not supported by soundfile)", file=sys.stderr)
                    else:
                        print(f"Info: Using audioread backend (soundfile couldn't load this file)", file=sys.stderr)
                    break

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

        For large files, uses chunked processing to reduce memory usage.

        Args:
            y: Audio time series
            sr: Sample rate
            sensitivity: Detection sensitivity (0.0-1.0). Higher = more sensitive
            expected_count: Expected number of tracks (if known from tracklist)

        Returns:
            List of boundary timestamps in seconds
        """
        duration = len(y) / sr
        # Use chunked processing for files longer than 10 minutes
        chunk_duration = 10 * 60  # 10 minutes in seconds

        if duration > chunk_duration:
            return self._detect_boundaries_chunked(y, sr, sensitivity, expected_count, chunk_duration)
        else:
            return self._detect_boundaries_full(y, sr, sensitivity, expected_count)

    def _detect_boundaries_full(
        self,
        y: np.ndarray,
        sr: int,
        sensitivity: float = 0.5,
        expected_count: Optional[int] = None,
    ) -> List[float]:
        """Process entire audio file at once (for smaller files)."""
        print("Analyzing audio features:", file=sys.stderr)

        # 1. Spectral contrast - detects changes in frequency balance
        with Spinner("[1/5] Extracting spectral contrast"):
            contrast = librosa.feature.spectral_contrast(
                y=y, sr=sr, hop_length=self.hop_length, n_bands=6
            )
            contrast_mean = np.mean(contrast, axis=0)

        # 2. Chroma features - detects key/tonality changes
        with Spinner("[2/5] Extracting chroma features"):
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=self.hop_length)

        # 3. MFCC - detects timbral changes
        with Spinner("[3/5] Extracting MFCC"):
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=self.hop_length)

        # Compute self-similarity matrix for chroma
        with Spinner("[4/5] Computing similarity matrix"):
            # Use sparse matrix with limited k-neighbors to reduce memory usage
            # k should be small enough to avoid memory issues but large enough for detection
            chroma_similarity = librosa.segment.recurrence_matrix(
                chroma, k=100, mode="affinity", metric="cosine", width=9, sparse=True
            )

        # Compute novelty curve from similarity matrix
        with Spinner("[5/5] Detecting boundaries"):
            # Use sparse-friendly novelty computation
            # For sparse matrices, compute novelty as sum of dissimilarities
            if hasattr(chroma_similarity, 'toarray'):
                # Sparse matrix: compute novelty without full dense conversion
                # For affinity matrices (values 0-1), dissimilarity = max_value - similarity
                # Since sparse matrices store only non-zero values, we need a different approach
                # Compute novelty as the negative sum of similarities (lower similarity = higher novelty)
                novelty = -np.asarray(chroma_similarity.sum(axis=0)).flatten()
            else:
                # Dense matrix (small files)
                novelty = np.sqrt(
                    librosa.segment.lag_to_recurrence(1 - chroma_similarity, axis=1).sum(
                        axis=0
                    )
                )

            # Normalize novelty curve
            novelty = (novelty - novelty.min()) / (novelty.max() - novelty.min() + 1e-8)

        return self._find_peaks(novelty, sr, sensitivity, expected_count)

    def _process_single_chunk(
        self,
        chunk_data: Tuple[int, np.ndarray, int, int, int],
    ) -> Tuple[int, np.ndarray]:
        """
        Process a single audio chunk to extract novelty curve.
        This method is designed to be called by multiprocessing workers.

        Args:
            chunk_data: Tuple of (chunk_index, audio_chunk, sample_rate, start_idx, total_chunks)

        Returns:
            Tuple of (start_idx, novelty_curve)
        """
        chunk_index, chunk, sr, start_idx, total_chunks = chunk_data

        # Extract chroma for this chunk
        chroma = librosa.feature.chroma_cqt(y=chunk, sr=sr, hop_length=self.hop_length)

        # Compute similarity matrix for this chunk
        # Use sparse matrix with limited k-neighbors to reduce memory usage
        chroma_similarity = librosa.segment.recurrence_matrix(
            chroma, k=100, mode="affinity", metric="cosine", width=9, sparse=True
        )

        # Compute novelty curve
        # Use sparse-friendly novelty computation
        if hasattr(chroma_similarity, 'toarray'):
            # Sparse matrix: compute novelty without full dense conversion
            # Compute novelty as the negative sum of similarities (lower similarity = higher novelty)
            novelty_chunk = -np.asarray(chroma_similarity.sum(axis=0)).flatten()
        else:
            # Dense matrix
            novelty_chunk = np.sqrt(
                librosa.segment.lag_to_recurrence(1 - chroma_similarity, axis=1).sum(axis=0)
            )

        return (start_idx, novelty_chunk)

    def _detect_boundaries_chunked(
        self,
        y: np.ndarray,
        sr: int,
        sensitivity: float = 0.5,
        expected_count: Optional[int] = None,
        chunk_duration: float = 30 * 60,
    ) -> List[float]:
        """
        Process audio in overlapping chunks to reduce memory usage.
        Uses multiprocessing to process chunks in parallel.

        Args:
            y: Audio time series
            sr: Sample rate
            sensitivity: Detection sensitivity (0.0-1.0)
            expected_count: Expected number of tracks
            chunk_duration: Duration of each chunk in seconds
        """
        print(f"Large file detected ({len(y)/sr:.1f}s), using chunked processing with {cpu_count} workers", file=sys.stderr)

        chunk_samples = int(chunk_duration * sr)
        overlap_samples = int(60 * sr)  # 1 minute overlap between chunks
        stride_samples = chunk_samples - overlap_samples

        total_chunks = int(np.ceil((len(y) - overlap_samples) / stride_samples))

        # Prepare chunk data for parallel processing
        chunk_tasks = []
        for i in range(total_chunks):
            start_idx = i * stride_samples
            end_idx = min(start_idx + chunk_samples, len(y))
            chunk = y[start_idx:end_idx]
            chunk_tasks.append((i, chunk, sr, start_idx, total_chunks))

        # Process chunks in parallel using multiprocessing
        print(f"Processing {total_chunks} chunks in parallel...", file=sys.stderr)

        all_novelty = []
        with multiprocessing.Pool(processes=cpu_count) as pool:
            # Use imap_unordered for better performance with progress tracking
            with tqdm(total=total_chunks, desc="Processing chunks", disable=False, file=sys.stderr) as pbar:
                for result in pool.imap_unordered(self._process_single_chunk, chunk_tasks):
                    all_novelty.append(result)
                    pbar.update(1)

        # Combine novelty curves from all chunks
        print("Combining results from chunks...", file=sys.stderr)
        total_frames = librosa.time_to_frames(len(y) / sr, sr=sr, hop_length=self.hop_length)
        combined_novelty = np.zeros(total_frames)
        weights = np.zeros(total_frames)

        for start_idx, novelty_chunk in all_novelty:
            # Convert sample index to frame index
            start_frame = librosa.time_to_frames(start_idx / sr, sr=sr, hop_length=self.hop_length)
            end_frame = min(start_frame + len(novelty_chunk), total_frames)
            chunk_len = end_frame - start_frame

            # Use triangular weighting to blend overlapping regions
            weight = np.ones(chunk_len)
            fade_len = min(overlap_samples // self.hop_length, chunk_len // 4)
            if fade_len > 0:
                weight[:fade_len] = np.linspace(0, 1, fade_len)
                weight[-fade_len:] = np.linspace(1, 0, fade_len)

            combined_novelty[start_frame:end_frame] += novelty_chunk[:chunk_len] * weight
            weights[start_frame:end_frame] += weight

        # Normalize by weights
        weights[weights == 0] = 1  # Avoid division by zero
        novelty = combined_novelty / weights

        # Normalize novelty curve
        novelty = (novelty - novelty.min()) / (novelty.max() - novelty.min() + 1e-8)

        return self._find_peaks(novelty, sr, sensitivity, expected_count)

    def _find_peaks(
        self,
        novelty: np.ndarray,
        sr: int,
        sensitivity: float,
        expected_count: Optional[int],
    ) -> List[float]:
        """Find peaks in novelty curve to identify boundaries."""
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

    def convert_to_aac(self, filepath: str) -> str:
        """
        Convert M4A/MP4 to raw ADTS AAC format for mp3DirectCut compatibility.

        Args:
            filepath: Path to audio file

        Returns:
            Path to converted AAC file (or original if already AAC/MP3)
        """
        import subprocess
        import shutil

        path = Path(filepath)
        ext = path.suffix.lower()

        # Check if conversion is needed
        if ext in [".mp3", ".wav"]:
            # No conversion needed
            return filepath

        # Check file format
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-of", "default=noprint_wrappers=1", str(filepath)],
                capture_output=True,
                text=True,
                check=True,
            )

            # Check if it's MP4/M4A container
            is_mp4_container = "mov,mp4,m4a" in result.stdout or "format_name=mov,mp4,m4a" in result.stdout

            if is_mp4_container or ext in [".m4a", ".mp4", ".aac"]:
                # Convert to raw ADTS AAC
                output_path = path.with_suffix(".aac")
                if output_path.stem.endswith("_converted"):
                    # Already converted
                    return str(output_path)

                # Add _converted suffix to avoid overwriting
                output_path = path.with_name(f"{path.stem}_converted.aac")

                if output_path.exists():
                    print(f"Using existing converted file: {output_path}", file=sys.stderr)
                    return str(output_path)

                print(f"Converting {ext} to raw AAC format for mp3DirectCut compatibility...", file=sys.stderr)
                subprocess.run(
                    ["ffmpeg", "-i", str(filepath), "-c", "copy", "-f", "adts", "-y", str(output_path)],
                    check=True,
                    capture_output=True,
                )
                print(f"Converted: {output_path}", file=sys.stderr)
                return str(output_path)

        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not check format, using original file: {e}", file=sys.stderr)
        except FileNotFoundError:
            print("Warning: ffmpeg/ffprobe not found, using original file", file=sys.stderr)

        return filepath

    def analyze_mix(
        self,
        filepath: str,
        sensitivity: float = 0.5,
        tracklist: Optional[List[Track]] = None,
    ) -> Tuple[List[float], str]:
        """
        Analyze a DJ mix and detect track boundaries.

        Args:
            filepath: Path to the DJ mix audio file
            sensitivity: Detection sensitivity (0.0-1.0)
            tracklist: Optional tracklist to guide detection

        Returns:
            Tuple of (List of boundary timestamps in seconds, path to processed audio file)
        """
        # Convert M4A/MP4 to AAC if needed
        processed_filepath = self.convert_to_aac(filepath)

        with Spinner("Loading audio"):
            y, sr = self.load_audio(processed_filepath)

        duration = librosa.get_duration(y=y, sr=sr)
        print(f"Duration: {duration:.1f} seconds", file=sys.stderr)

        # If tracklist has timestamps, use them directly
        if tracklist and any(t.timestamp is not None for t in tracklist):
            print("Using timestamps from tracklist", file=sys.stderr)
            boundaries = [t.timestamp for t in tracklist[1:] if t.timestamp is not None]
            print(f"Found {len(boundaries)} boundaries from tracklist", file=sys.stderr)
            return sorted(boundaries), processed_filepath

        # Otherwise, detect boundaries with optional track count constraint
        expected_count = len(tracklist) if tracklist else None
        boundaries = self.detect_boundaries(y, sr, sensitivity, expected_count)
        return boundaries, processed_filepath


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
        elif ext == ".m4a":
            file_type = "MP4"
        elif ext == ".aac":
            # Raw ADTS AAC - use WAVE for mp3DirectCut compatibility
            file_type = "WAVE"
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
    recognize_tracks: bool = False,
    verify_boundaries: bool = False,
) -> str:
    """
    Segment a DJ mix and generate a CUE sheet.

    Args:
        audio_filepath: Path to the DJ mix audio file
        output_filepath: Path to save the CUE sheet (optional)
        sensitivity: Detection sensitivity (0.0-1.0, default 0.5)
        tracklist: Optional tracklist to guide segmentation
        recognize_tracks: Whether to use music recognition to identify tracks
        verify_boundaries: If True, verify boundaries using music recognition and adjust if needed

    Returns:
        CUE sheet content as string
    """
    # Analyze the mix (returns boundaries and processed filepath)
    segmenter = DJMixSegmenter()

    # Convert M4A/MP4 to AAC if needed
    processed_filepath = segmenter.convert_to_aac(audio_filepath)

    # Load audio for boundary detection and potential retries
    with Spinner("Loading audio"):
        y, sr = segmenter.load_audio(processed_filepath)

    duration = librosa.get_duration(y=y, sr=sr)
    print(f"Duration: {duration:.1f} seconds", file=sys.stderr)

    # If tracklist has timestamps, use them directly
    if tracklist and any(t.timestamp is not None for t in tracklist):
        print("Using timestamps from tracklist", file=sys.stderr)
        boundaries = [t.timestamp for t in tracklist[1:] if t.timestamp is not None]
        print(f"Found {len(boundaries)} boundaries from tracklist", file=sys.stderr)
    else:
        # Otherwise, detect boundaries with optional track count constraint
        expected_count = len(tracklist) if tracklist else None
        boundaries = segmenter.detect_boundaries(y, sr, sensitivity, expected_count)

    # If verify_boundaries is True and tracklist is provided, force recognition
    if verify_boundaries and tracklist and not recognize_tracks:
        print("Note: Boundary verification requires music recognition, enabling automatically...", file=sys.stderr)
        recognize_tracks = True

    # Recognize tracks if requested
    recognized_tracklist = None
    if recognize_tracks:
        try:
            from music_recognizer import MusicRecognizer, RecognitionResult

            recognizer = MusicRecognizer()
            recognized_tracklist = []

            print("\nRecognizing tracks...", file=sys.stderr)

            # Create list of boundaries with start of mix (0.0)
            all_boundaries = [0.0] + boundaries

            for i in range(len(all_boundaries) - 1):
                start_time = all_boundaries[i]
                end_time = all_boundaries[i + 1]
                track_num = i + 1

                print(f"\nTrack {track_num}: {start_time:.1f}s - {end_time:.1f}s", file=sys.stderr)

                with Spinner(f"Recognizing track {track_num}"):
                    result = recognizer.extract_and_recognize_segment(
                        processed_filepath, start_time, end_time, track_num
                    )

                    if result and tracklist:
                        # Try to match with provided tracklist
                        matched_num = MusicRecognizer.match_with_tracklist(result, tracklist)
                        if matched_num and matched_num <= len(tracklist):
                            # Use tracklist info but keep recognition confidence
                            track = tracklist[matched_num - 1]
                            result.artist = track.artist
                            result.title = track.title
                            result.source = "tracklist+acoustid"

                if result:
                    recognized_tracklist.append(result)
                    print(f"  ✓ {result}", file=sys.stderr)
                else:
                    print(f"  ✗ No match found", file=sys.stderr)

            # Verify boundaries if requested and tracklist is provided
            if verify_boundaries and tracklist and recognized_tracklist:
                print("\nVerifying boundaries against tracklist...", file=sys.stderr)

                # Calculate match scores for each recognized track
                # Try matching with current position and nearby positions (±2 tracks)
                mismatches = []

                for i, result in enumerate(recognized_tracklist):
                    track_num = result.track_number
                    best_score = 0.0
                    best_match_pos = track_num

                    # Check current position and ±2 positions in tracklist
                    search_range = range(
                        max(1, track_num - 2),
                        min(len(tracklist) + 1, track_num + 3)
                    )

                    for pos in search_range:
                        tracklist_track = tracklist[pos - 1]
                        score = calculate_track_match_score(
                            result.artist,
                            result.title,
                            tracklist_track.artist,
                            tracklist_track.title
                        )

                        if score > best_score:
                            best_score = score
                            best_match_pos = pos

                    # Consider it a mismatch if best score is low (< 0.5)
                    # or if best match is not at expected position
                    if best_score < 0.5:
                        mismatches.append({
                            'track_num': track_num,
                            'recognized': f"{result.artist} - {result.title}",
                            'expected': f"{tracklist[track_num - 1].artist} - {tracklist[track_num - 1].title}",
                            'score': best_score,
                            'issue': 'low_confidence'
                        })
                    elif best_match_pos != track_num:
                        offset = best_match_pos - track_num
                        mismatches.append({
                            'track_num': track_num,
                            'recognized': f"{result.artist} - {result.title}",
                            'expected': f"{tracklist[track_num - 1].artist} - {tracklist[track_num - 1].title}",
                            'best_match': f"{tracklist[best_match_pos - 1].artist} - {tracklist[best_match_pos - 1].title}",
                            'offset': offset,
                            'score': best_score,
                            'issue': 'position_mismatch'
                        })

                # If significant mismatches found, show them and prompt user
                if mismatches:
                    mismatch_rate = len(mismatches) / len(recognized_tracklist)

                    print(f"\n⚠️  Found {len(mismatches)} mismatch(es) out of {len(recognized_tracklist)} tracks ({mismatch_rate*100:.1f}%)", file=sys.stderr)
                    print("\nMismatches detected:", file=sys.stderr)

                    for m in mismatches:
                        print(f"\n  Track {m['track_num']}:", file=sys.stderr)
                        print(f"    Recognized: {m['recognized']}", file=sys.stderr)
                        print(f"    Expected:   {m['expected']}", file=sys.stderr)

                        if m['issue'] == 'position_mismatch':
                            offset_str = f"+{m['offset']}" if m['offset'] > 0 else str(m['offset'])
                            print(f"    Best match: {m['best_match']} (offset: {offset_str})", file=sys.stderr)
                            print(f"    → Boundary may be shifted {'forward' if m['offset'] > 0 else 'backward'}", file=sys.stderr)
                        else:
                            print(f"    Match score: {m['score']:.2f} (low confidence)", file=sys.stderr)

                    # Interactive prompt for retry
                    print("\n" + "="*60, file=sys.stderr)
                    print("What would you like to do?", file=sys.stderr)
                    print("  1. Continue with current boundaries (default)", file=sys.stderr)
                    print("  2. Adjust sensitivity and retry boundary detection", file=sys.stderr)
                    print("  3. Abort", file=sys.stderr)
                    print("="*60, file=sys.stderr)

                    max_retries = 3
                    retry_count = 0

                    while retry_count < max_retries:
                        try:
                            choice = input("\nEnter your choice (1/2/3) [1]: ").strip()

                            if choice == "" or choice == "1":
                                # Continue with current boundaries
                                print("Continuing with current boundaries...", file=sys.stderr)
                                break
                            elif choice == "2":
                                # Retry with new sensitivity
                                new_sensitivity_str = input(f"Enter new sensitivity value (0.0-1.0) [current: {sensitivity}]: ").strip()

                                if new_sensitivity_str == "":
                                    print("No sensitivity change, continuing...", file=sys.stderr)
                                    break

                                try:
                                    new_sensitivity = float(new_sensitivity_str)
                                    if not 0.0 <= new_sensitivity <= 1.0:
                                        print("Error: Sensitivity must be between 0.0 and 1.0", file=sys.stderr)
                                        continue

                                    # Re-detect boundaries with new sensitivity
                                    print(f"\nRe-detecting boundaries with sensitivity={new_sensitivity}...", file=sys.stderr)
                                    boundaries = segmenter.detect_boundaries(y, sr, new_sensitivity, len(tracklist))

                                    # Re-run recognition on new boundaries
                                    print("\nRe-recognizing tracks with new boundaries...", file=sys.stderr)
                                    recognized_tracklist = []
                                    all_boundaries = [0.0] + boundaries

                                    for i in range(len(all_boundaries) - 1):
                                        start_time = all_boundaries[i]
                                        end_time = all_boundaries[i + 1]
                                        track_num = i + 1

                                        print(f"\nTrack {track_num}: {start_time:.1f}s - {end_time:.1f}s", file=sys.stderr)

                                        with Spinner(f"Recognizing track {track_num}"):
                                            result = recognizer.extract_and_recognize_segment(
                                                processed_filepath, start_time, end_time, track_num
                                            )

                                            if result and tracklist:
                                                matched_num = MusicRecognizer.match_with_tracklist(result, tracklist)
                                                if matched_num and matched_num <= len(tracklist):
                                                    track = tracklist[matched_num - 1]
                                                    result.artist = track.artist
                                                    result.title = track.title
                                                    result.source = "tracklist+acoustid"

                                            if result:
                                                recognized_tracklist.append(result)
                                                print(f"  ✓ {result}", file=sys.stderr)
                                            else:
                                                print(f"  ✗ No match found", file=sys.stderr)

                                    # Update sensitivity for next iteration
                                    sensitivity = new_sensitivity
                                    retry_count += 1

                                    # Re-check for mismatches (loop will continue)
                                    # Reset mismatches list and re-verify
                                    mismatches = []
                                    for i, result in enumerate(recognized_tracklist):
                                        track_num = result.track_number
                                        best_score = 0.0
                                        best_match_pos = track_num

                                        search_range = range(
                                            max(1, track_num - 2),
                                            min(len(tracklist) + 1, track_num + 3)
                                        )

                                        for pos in search_range:
                                            tracklist_track = tracklist[pos - 1]
                                            score = calculate_track_match_score(
                                                result.artist,
                                                result.title,
                                                tracklist_track.artist,
                                                tracklist_track.title
                                            )

                                            if score > best_score:
                                                best_score = score
                                                best_match_pos = pos

                                        if best_score < 0.5:
                                            mismatches.append({
                                                'track_num': track_num,
                                                'recognized': f"{result.artist} - {result.title}",
                                                'expected': f"{tracklist[track_num - 1].artist} - {tracklist[track_num - 1].title}",
                                                'score': best_score,
                                                'issue': 'low_confidence'
                                            })
                                        elif best_match_pos != track_num:
                                            offset = best_match_pos - track_num
                                            mismatches.append({
                                                'track_num': track_num,
                                                'recognized': f"{result.artist} - {result.title}",
                                                'expected': f"{tracklist[track_num - 1].artist} - {tracklist[track_num - 1].title}",
                                                'best_match': f"{tracklist[best_match_pos - 1].artist} - {tracklist[best_match_pos - 1].title}",
                                                'offset': offset,
                                                'score': best_score,
                                                'issue': 'position_mismatch'
                                            })

                                    if not mismatches:
                                        print("\n✓ All tracks now match the tracklist!", file=sys.stderr)
                                        break
                                    else:
                                        print(f"\n⚠️  Still found {len(mismatches)} mismatch(es)", file=sys.stderr)
                                        if retry_count >= max_retries:
                                            print(f"Maximum retries ({max_retries}) reached.", file=sys.stderr)
                                            break
                                        # Show mismatches again and continue loop
                                        for m in mismatches:
                                            print(f"\n  Track {m['track_num']}:", file=sys.stderr)
                                            print(f"    Recognized: {m['recognized']}", file=sys.stderr)
                                            print(f"    Expected:   {m['expected']}", file=sys.stderr)
                                            if m['issue'] == 'position_mismatch':
                                                offset_str = f"+{m['offset']}" if m['offset'] > 0 else str(m['offset'])
                                                print(f"    Best match: {m['best_match']} (offset: {offset_str})", file=sys.stderr)
                                        continue

                                except ValueError:
                                    print("Error: Invalid sensitivity value. Please enter a number between 0.0 and 1.0", file=sys.stderr)
                                    continue

                            elif choice == "3":
                                # Abort
                                print("Aborting...", file=sys.stderr)
                                sys.exit(0)
                            else:
                                print("Invalid choice. Please enter 1, 2, or 3.", file=sys.stderr)
                                continue

                        except EOFError:
                            # Handle Ctrl+D
                            print("\nAborted by user", file=sys.stderr)
                            sys.exit(0)
                        except KeyboardInterrupt:
                            # Handle Ctrl+C
                            print("\nAborted by user", file=sys.stderr)
                            sys.exit(0)
                else:
                    print("✓ All tracks match the tracklist!", file=sys.stderr)

            # Convert RecognitionResult objects to Track objects for CUE generation
            if recognized_tracklist:
                from tracklist_parser import Track as TrackObj
                tracklist = []
                for r in recognized_tracklist:
                    tracklist.append(TrackObj(
                        number=r.track_number,
                        artist=r.artist,
                        title=r.title,
                        timestamp=None
                    ))

        except ImportError as e:
            print(f"Warning: Music recognition not available: {e}", file=sys.stderr)
            print("Install with: pip install pyacoustid", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Music recognition failed: {e}", file=sys.stderr)

    # Generate CUE sheet
    generator = CueSheetGenerator()

    # Default output path if not specified
    if output_filepath is None:
        # Use the original audio filepath for the output filename
        audio_path = Path(audio_filepath)
        output_filepath = str(audio_path.with_suffix(".cue"))

    # Use the processed filepath (converted AAC if applicable) for the CUE sheet
    cue_content = generator.generate_cue(
        processed_filepath, boundaries, output_filepath, tracklist
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

  # Use tracklist for track count guidance
  python segmenter.py mix.mp3 --tracklist tracklist.txt

Sensitivity Parameter:
  The --sensitivity parameter controls boundary detection (range: 0.0-1.0, default: 0.5).

  How it works:
  - Converts to detection threshold: threshold = 0.9 - (sensitivity × 0.6)
  - sensitivity 0.0 → threshold 0.9 (very strict, fewer boundaries)
  - sensitivity 0.5 → threshold 0.6 (balanced, default)
  - sensitivity 1.0 → threshold 0.3 (very loose, more boundaries)

  When to adjust:
  - Too few tracks detected → increase sensitivity (e.g., 0.7-0.8)
  - Too many false boundaries → decrease sensitivity (e.g., 0.3-0.4)

  Important notes:
  - Minimum 60 seconds between boundaries (prevents too-close tracks)
  - Ignored when tracklist is provided (uses expected track count instead)
  - Works best for mixes with clear transitions
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
        help="Detection sensitivity: 0.0 (strict, fewer boundaries) to 1.0 (loose, more boundaries). Default: 0.5. Ignored when tracklist is provided.",
    )
    parser.add_argument(
        "--recognize",
        action="store_true",
        help="Use music recognition to identify tracks (requires pyacoustid)",
    )

    args = parser.parse_args()

    # Validate sensitivity
    if not 0.0 <= args.sensitivity <= 1.0:
        print("Error: Sensitivity must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)

    try:
        segment_mix(args.audio_file, args.output, args.sensitivity, recognize_tracks=args.recognize)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
