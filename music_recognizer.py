#!/usr/bin/env python3
"""
Music Recognition Module

Identifies tracks in DJ mixes using audio fingerprinting services:
- AcoustID (free, open-source)
- Shazam API (optional, higher accuracy)
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class RecognitionResult:
    """Represents a music recognition result"""

    track_number: int
    artist: Optional[str] = None
    title: Optional[str] = None
    album: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0
    source: str = "unknown"  # "acoustid", "shazam", "tracklist", etc.
    acoustid: Optional[str] = None  # AcoustID fingerprint ID
    musicbrainz_id: Optional[str] = None  # MusicBrainz recording ID

    def __str__(self) -> str:
        parts = [f"Track {self.track_number:02d}"]
        if self.artist and self.title:
            parts.append(f"{self.artist} - {self.title}")
        elif self.title:
            parts.append(self.title)
        if self.confidence > 0:
            parts.append(f"({self.confidence:.0%} confidence)")
        parts.append(f"[{self.source}]")
        return " ".join(parts)


class MusicRecognizer:
    """Identifies music tracks using various recognition services"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_shazam: bool = True,  # Enable Shazam fallback by default
        shazam_only: bool = False,  # Manual override to use only Shazam
        acoustid_only: bool = False,  # Manual override to use only AcoustID
    ):
        """
        Initialize the music recognizer.

        Args:
            api_key: Optional API key (currently unused, kept for compatibility)
            use_shazam: Whether to use Shazam as fallback (default: True)
            shazam_only: Use only Shazam API (skip AcoustID)
            acoustid_only: Use only AcoustID (skip Shazam)
        """
        self.api_key = api_key
        self.use_shazam = use_shazam and not acoustid_only
        self.shazam_only = shazam_only
        self.acoustid_only = acoustid_only
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required libraries are installed and raise error if missing"""
        try:
            import acoustid
            import chromaprint

            self.acoustid_available = True
        except ImportError:
            self.acoustid_available = False

        try:
            import shazamio

            self.shazam_available = True
        except ImportError:
            self.shazam_available = False

        # If shazam_only mode but Shazam is not available, error
        if self.shazam_only and not self.shazam_available:
            print(
                "Error: shazamio is not installed. Install with: pip install shazamio",
                file=sys.stderr,
            )
            sys.exit(1)

        # If acoustid_only mode but AcoustID is not available, error
        if self.acoustid_only and not self.acoustid_available:
            print(
                "Error: acoustid/chromaprint is not installed. Install with: pip install pyacoustid",
                file=sys.stderr,
            )
            sys.exit(1)

        # If neither service is available, error
        if not self.acoustid_available and not self.shazam_available:
            print(
                "Error: No music recognition services available.",
                file=sys.stderr,
            )
            print(
                "Install at least one of the following:",
                file=sys.stderr,
            )
            print(
                "  - AcoustID: pip install pyacoustid",
                file=sys.stderr,
            )
            print(
                "  - Shazam: pip install shazamio",
                file=sys.stderr,
            )
            sys.exit(1)

    def recognize_file(
        self, audio_path: str, duration: int = 30
    ) -> Optional[RecognitionResult]:
        """
        Recognize a music file using available services.

        Args:
            audio_path: Path to audio file
            duration: Duration in seconds to analyze (default: 30s from middle)

        Returns:
            RecognitionResult or None if recognition failed
        """
        # If shazam_only mode, skip AcoustID
        if self.shazam_only:
            if self.shazam_available:
                print("  Using Shazam only mode...", file=sys.stderr)
                result = self._recognize_shazam(audio_path)
                if result:
                    return result
            return None

        # Try AcoustID first (free, fast)
        if self.acoustid_available and not self.shazam_only:
            result = self._recognize_acoustid(audio_path, duration)
            if result:
                return result

        # Fall back to Shazam if AcoustID failed and Shazam is enabled
        if self.use_shazam and self.shazam_available:
            print("  AcoustID failed, trying Shazam fallback...", file=sys.stderr)
            result = self._recognize_shazam(audio_path)
            if result:
                return result

        return None

    def _recognize_acoustid(
        self, audio_path: str, duration: int = 30
    ) -> Optional[RecognitionResult]:
        """
        Recognize music using AcoustID/MusicBrainz.

        Args:
            audio_path: Path to audio file
            duration: Duration to analyze (seconds)

        Returns:
            RecognitionResult or None
        """
        try:
            import acoustid

            # AcoustID API key (public test key - replace with your own for production)
            # Get your free API key at: https://acoustid.org/new-application
            api_key = os.environ.get("ACOUSTID_API_KEY", "8XaBELgH")

            print(
                f"Recognizing with AcoustID: {Path(audio_path).name}...",
                file=sys.stderr,
            )

            # Match the audio file
            # Note: This will analyze the entire file unless we extract a segment
            results = acoustid.match(api_key, audio_path)

            for score, recording_id, title, artist in results:
                print(
                    f"  Match: {artist} - {title} (score: {score:.2f})", file=sys.stderr
                )
                if score > 0.5:  # Threshold for acceptable match
                    return RecognitionResult(
                        track_number=0,  # Will be set by caller
                        artist=artist,
                        title=title,
                        confidence=score,
                        source="acoustid",
                        musicbrainz_id=recording_id,
                    )

            print("  No confident matches found", file=sys.stderr)
            return None

        except Exception as e:
            print(f"AcoustID recognition error: {e}", file=sys.stderr)
            return None

    def _recognize_shazam(self, audio_path: str) -> Optional[RecognitionResult]:
        """
        Recognize music using Shazam API (via ShazamIO).

        Args:
            audio_path: Path to audio file

        Returns:
            RecognitionResult or None
        """
        try:
            from shazamio import Shazam
            import asyncio

            print(
                f"Recognizing with Shazam: {Path(audio_path).name}...",
                file=sys.stderr,
            )

            # ShazamIO is async, so we need to run it in an event loop
            async def recognize_async():
                shazam = Shazam()
                result = await shazam.recognize(audio_path)
                return result

            # Run async function in sync context
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            shazam_result = loop.run_until_complete(recognize_async())

            # Parse Shazam response
            if shazam_result and "track" in shazam_result:
                track = shazam_result["track"]
                artist = track.get("subtitle", "")  # Artist name
                title = track.get("title", "")  # Track title

                if artist and title:
                    print(
                        f"  Match: {artist} - {title} (Shazam)", file=sys.stderr
                    )
                    return RecognitionResult(
                        track_number=0,  # Will be set by caller
                        artist=artist,
                        title=title,
                        confidence=0.95,  # Shazam generally has high confidence
                        source="shazam",
                    )

            print("  No confident matches found", file=sys.stderr)
            return None

        except Exception as e:
            print(f"Shazam recognition error: {e}", file=sys.stderr)
            return None

    @staticmethod
    def match_with_tracklist(
        recognition_result: RecognitionResult, tracklist: List, fuzzy_threshold: float = 0.6
    ) -> Optional[int]:
        """
        Match a recognition result with a provided tracklist.

        Args:
            recognition_result: Result from recognition service
            tracklist: List of Track objects from tracklist_parser
            fuzzy_threshold: Minimum similarity ratio (0.0 to 1.0)

        Returns:
            Track number (1-indexed) of best match, or None
        """
        if not recognition_result.artist or not recognition_result.title:
            return None

        recognized = f"{recognition_result.artist} {recognition_result.title}".lower()
        best_match = None
        best_ratio = 0.0

        for track in tracklist:
            if not track.artist or not track.title:
                continue

            track_str = f"{track.artist} {track.title}".lower()
            ratio = SequenceMatcher(None, recognized, track_str).ratio()

            if ratio > best_ratio and ratio >= fuzzy_threshold:
                best_ratio = ratio
                best_match = track.number

        if best_match:
            print(
                f"  Matched to tracklist track #{best_match} (similarity: {best_ratio:.0%})",
                file=sys.stderr,
            )

        return best_match

    def extract_and_recognize_segment(
        self, audio_path: str, start_time: float, end_time: float, track_number: int
    ) -> Optional[RecognitionResult]:
        """
        Extract a segment from audio file and recognize it.

        Args:
            audio_path: Path to source audio file
            start_time: Start time in seconds
            end_time: End time in seconds
            track_number: Track number for result

        Returns:
            RecognitionResult or None
        """
        # Calculate segment duration and middle point
        duration = end_time - start_time
        if duration < 10:
            print(
                f"  Segment too short ({duration:.1f}s), skipping recognition",
                file=sys.stderr,
            )
            return None

        # Sample from the middle third of the segment (less likely to have crossfade)
        sample_start = start_time + duration * 0.35
        sample_duration = min(30, duration * 0.3)  # Max 30 seconds

        # Create temporary file for segment
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Extract segment using ffmpeg
            import subprocess

            print(
                f"  Extracting {sample_duration:.1f}s sample from {sample_start:.1f}s...",
                file=sys.stderr,
            )

            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    audio_path,
                    "-ss",
                    str(sample_start),
                    "-t",
                    str(sample_duration),
                    "-ar",
                    "44100",  # Standard sample rate
                    "-ac",
                    "2",  # Stereo
                    "-y",  # Overwrite
                    temp_path,
                ],
                check=True,
                capture_output=True,
            )

            # Recognize the extracted segment
            result = self.recognize_file(temp_path)

            if result:
                result.track_number = track_number
                return result

            return None

        except subprocess.CalledProcessError as e:
            print(f"  Failed to extract segment: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"  Recognition error: {e}", file=sys.stderr)
            return None
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Recognize music tracks in audio files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Recognize a single audio file
  python music_recognizer.py track.mp3

  # Recognize with Shazam API (requires API key)
  python music_recognizer.py --shazam --api-key YOUR_KEY track.mp3
        """,
    )

    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument(
        "--shazam", action="store_true", help="Use Shazam API (requires API key)"
    )
    parser.add_argument("--api-key", help="API key for Shazam")
    parser.add_argument(
        "--duration", type=int, default=30, help="Duration to analyze (seconds)"
    )

    args = parser.parse_args()

    recognizer = MusicRecognizer(api_key=args.api_key, use_shazam=args.shazam)
    result = recognizer.recognize_file(args.audio_file, args.duration)

    if result:
        print(f"\nRecognized: {result}")
        if result.album:
            print(f"Album: {result.album}")
        if result.musicbrainz_id:
            print(f"MusicBrainz ID: {result.musicbrainz_id}")
    else:
        print("\nNo match found", file=sys.stderr)
        sys.exit(1)
