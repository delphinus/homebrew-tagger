"""
Mock implementation of the acoustid module for testing.

This allows tests to run without making actual API calls to acoustid.org.
"""

from typing import Iterator, Tuple, Optional, Dict, Any
import hashlib
from pathlib import Path


class MockAcoustID:
    """
    Mock for the acoustid module.

    Simulates AcoustID responses based on pre-configured metadata.
    """

    def __init__(self, track_metadata: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize mock AcoustID.

        Args:
            track_metadata: Dictionary mapping "fingerprints" to track metadata
                           Format: {
                               "fingerprint_id": {
                                   "artist": "Artist Name",
                                   "title": "Track Title",
                                   "score": 0.95,
                                   "recording_id": "mb-recording-id"
                               }
                           }
        """
        self.track_metadata = track_metadata or {}
        self.call_count = 0

    def match(
        self,
        api_key: str,
        audio_path: str,
        parse: bool = True
    ) -> Iterator[Tuple[float, str, str, str]]:
        """
        Mock of acoustid.match() function.

        Args:
            api_key: AcoustID API key (ignored in mock)
            audio_path: Path to audio file
            parse: Whether to parse metadata (ignored in mock)

        Yields:
            Tuples of (score, recording_id, title, artist)
        """
        self.call_count += 1

        # Generate a deterministic "fingerprint" from the audio file path
        # In real usage, this would be the actual audio fingerprint
        fingerprint = self._generate_fingerprint(audio_path)

        # Look up metadata for this fingerprint
        if fingerprint in self.track_metadata:
            metadata = self.track_metadata[fingerprint]
            yield (
                metadata.get("score", 0.95),
                metadata.get("recording_id", f"mock-recording-{fingerprint[:8]}"),
                metadata.get("title", "Unknown Title"),
                metadata.get("artist", "Unknown Artist")
            )
        else:
            # Return empty iterator for unknown tracks (no match)
            return iter([])

    def _generate_fingerprint(self, audio_path: str) -> str:
        """
        Generate a deterministic fingerprint ID from audio file path.

        In real usage, this would be the actual AcoustID fingerprint.
        For testing, we use a hash of the file path.

        Args:
            audio_path: Path to audio file

        Returns:
            Fingerprint string
        """
        # Use file path basename to create deterministic fingerprint
        basename = Path(audio_path).name
        fingerprint_hash = hashlib.md5(basename.encode()).hexdigest()
        return fingerprint_hash

    def reset_stats(self):
        """Reset call statistics"""
        self.call_count = 0


def create_mock_from_ncs_metadata(metadata: dict) -> MockAcoustID:
    """
    Create a MockAcoustID instance from NCS metadata.

    Args:
        metadata: NCS metadata dictionary (from metadata.json)

    Returns:
        Configured MockAcoustID instance

    Example:
        >>> from tests.helpers.mix_creator import load_ncs_metadata
        >>> metadata = load_ncs_metadata()
        >>> mock_acoustid = create_mock_from_ncs_metadata(metadata)
    """
    track_metadata = {}

    for track_info in metadata["tracks"]:
        # Generate fingerprint from filename
        basename = track_info["filename"]
        fingerprint = hashlib.md5(basename.encode()).hexdigest()

        # Store metadata
        track_metadata[fingerprint] = {
            "artist": track_info["artist"],
            "title": track_info["title"],
            "score": 0.95,  # High confidence for test data
            "recording_id": track_info.get("musicbrainz_id", f"mock-mb-{fingerprint[:8]}")
        }

    return MockAcoustID(track_metadata)


# Module-level API to mimic acoustid module structure
_global_mock = None


def match(api_key: str, audio_path: str, parse: bool = True):
    """
    Module-level match function that mimics acoustid.match()

    This allows the mock to be used as a drop-in replacement:
        import tests.mocks.mock_acoustid as acoustid
        results = acoustid.match(api_key, path)
    """
    global _global_mock
    if _global_mock is None:
        raise RuntimeError(
            "MockAcoustID not configured. "
            "Use configure_global_mock() or install_mock() first."
        )
    return _global_mock.match(api_key, audio_path, parse)


def configure_global_mock(metadata: dict):
    """
    Configure the global mock instance with NCS metadata.

    Args:
        metadata: NCS metadata dictionary

    Example:
        >>> from tests.helpers.mix_creator import load_ncs_metadata
        >>> import tests.mocks.mock_acoustid as acoustid
        >>> acoustid.configure_global_mock(load_ncs_metadata())
    """
    global _global_mock
    _global_mock = create_mock_from_ncs_metadata(metadata)


def install_mock():
    """
    Install mock into sys.modules so it can be imported as 'acoustid'.

    Example:
        >>> import sys
        >>> from tests.mocks.mock_acoustid import install_mock
        >>> from tests.helpers.mix_creator import load_ncs_metadata
        >>> install_mock()
        >>> configure_global_mock(load_ncs_metadata())
        >>> # Now 'import acoustid' will use the mock
    """
    import sys
    from types import ModuleType

    # Use the current module (not re-import)
    current_module = sys.modules[__name__]
    sys.modules['acoustid'] = current_module

    # Also mock chromaprint module (required by MusicRecognizer._check_dependencies)
    chromaprint_mock = ModuleType('chromaprint')
    chromaprint_mock.__version__ = '1.0.0'  # Fake version
    sys.modules['chromaprint'] = chromaprint_mock
