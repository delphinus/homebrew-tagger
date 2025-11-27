"""
Mock implementation of the shazamio module for testing.

This allows tests to run without making actual API calls to Shazam.
"""

from typing import Optional, Dict, Any
import hashlib
from pathlib import Path
import asyncio


class MockShazam:
    """
    Mock for the shazamio.Shazam class.

    Simulates Shazam responses based on pre-configured metadata.
    """

    def __init__(self, track_metadata: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize mock Shazam.

        Args:
            track_metadata: Dictionary mapping "fingerprints" to track metadata
                           Format: {
                               "fingerprint_id": {
                                   "artist": "Artist Name",
                                   "title": "Track Title"
                               }
                           }
        """
        self.track_metadata = track_metadata or {}
        self.call_count = 0

    async def recognize(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Mock of Shazam.recognize() method.

        Args:
            audio_path: Path to audio file (can be str or bytes for actual data)

        Returns:
            Shazam-style response dictionary or None
        """
        self.call_count += 1

        # If audio_path is bytes (actual audio data), convert to path-like string
        # For our tests, it will be a file path
        if isinstance(audio_path, bytes):
            # In real usage with audio data, we'd need different logic
            # For now, treat as path
            audio_path = str(audio_path)

        # Generate fingerprint from file path
        fingerprint = self._generate_fingerprint(audio_path)

        # Look up metadata
        if fingerprint in self.track_metadata:
            metadata = self.track_metadata[fingerprint]
            return {
                "track": {
                    "title": metadata.get("title", "Unknown Title"),
                    "subtitle": metadata.get("artist", "Unknown Artist"),
                    "key": f"mock-shazam-{fingerprint[:8]}",
                    "sections": [
                        {
                            "type": "SONG",
                            "metapages": [
                                {
                                    "caption": metadata.get("artist", "Unknown Artist")
                                }
                            ]
                        }
                    ]
                },
                "matches": [
                    {
                        "id": f"match-{fingerprint[:8]}",
                        "offset": 0.0,
                        "channel": "mock"
                    }
                ]
            }
        else:
            # No match found
            return None

    def _generate_fingerprint(self, audio_path: str) -> str:
        """
        Generate a deterministic fingerprint from audio file path.

        Args:
            audio_path: Path to audio file

        Returns:
            Fingerprint string
        """
        basename = Path(audio_path).name
        fingerprint_hash = hashlib.md5(basename.encode()).hexdigest()
        return fingerprint_hash

    def reset_stats(self):
        """Reset call statistics"""
        self.call_count = 0


class MockShazamIO:
    """
    Mock for the shazamio module structure.
    """

    def __init__(self):
        """Initialize MockShazamIO module"""
        self.Shazam = MockShazam


def create_mock_from_ncs_metadata(metadata: dict) -> MockShazam:
    """
    Create a MockShazam instance from NCS metadata.

    Args:
        metadata: NCS metadata dictionary (from metadata.json)

    Returns:
        Configured MockShazam instance

    Example:
        >>> from tests.helpers.mix_creator import load_ncs_metadata
        >>> metadata = load_ncs_metadata()
        >>> mock_shazam = create_mock_from_ncs_metadata(metadata)
    """
    track_metadata = {}

    for track_info in metadata["tracks"]:
        # Generate fingerprint from filename
        basename = track_info["filename"]
        fingerprint = hashlib.md5(basename.encode()).hexdigest()

        # Store metadata
        track_metadata[fingerprint] = {
            "artist": track_info["artist"],
            "title": track_info["title"]
        }

    return MockShazam(track_metadata)


# Global mock instance
_global_mock_shazam = None


class Shazam:
    """
    Module-level Shazam class that mimics shazamio.Shazam

    This allows the mock to be used as a drop-in replacement:
        from tests.mocks import mock_shazam as shazamio
        shazam = shazamio.Shazam()
        result = await shazam.recognize(path)
    """

    def __init__(self):
        global _global_mock_shazam
        if _global_mock_shazam is None:
            raise RuntimeError(
                "MockShazam not configured. "
                "Use configure_global_mock() or install_mock() first."
            )
        self._mock = _global_mock_shazam

    async def recognize(self, audio_path: str):
        """Forward to global mock"""
        return await self._mock.recognize(audio_path)


def configure_global_mock(metadata: dict):
    """
    Configure the global mock instance with NCS metadata.

    Args:
        metadata: NCS metadata dictionary

    Example:
        >>> from tests.helpers.mix_creator import load_ncs_metadata
        >>> from tests.mocks import mock_shazam as shazamio
        >>> shazamio.configure_global_mock(load_ncs_metadata())
    """
    global _global_mock_shazam
    _global_mock_shazam = create_mock_from_ncs_metadata(metadata)


def install_mock():
    """
    Install mock into sys.modules so it can be imported as 'shazamio'.

    Example:
        >>> import sys
        >>> from tests.mocks.mock_shazam import install_mock
        >>> from tests.helpers.mix_creator import load_ncs_metadata
        >>> install_mock()
        >>> configure_global_mock(load_ncs_metadata())
        >>> # Now 'import shazamio' will use the mock
    """
    import sys
    # Use the current module (not re-import)
    current_module = sys.modules[__name__]
    sys.modules['shazamio'] = current_module


# Convenience function to install both mocks
def install_all_mocks(ncs_metadata: dict = None):
    """
    Install both AcoustID and Shazam mocks.

    Args:
        ncs_metadata: Optional NCS metadata. If not provided, loads from fixtures.

    Example:
        >>> from tests.mocks.mock_shazam import install_all_mocks
        >>> install_all_mocks()  # Auto-loads NCS metadata
    """
    if ncs_metadata is None:
        from tests.helpers.mix_creator import load_ncs_metadata
        ncs_metadata = load_ncs_metadata()

    # Install AcoustID mock
    from tests.mocks import mock_acoustid
    mock_acoustid.install_mock()
    mock_acoustid.configure_global_mock(ncs_metadata)

    # Install Shazam mock
    install_mock()
    configure_global_mock(ncs_metadata)
