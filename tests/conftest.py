"""Pytest configuration and fixtures"""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent

# Add project root to sys.path
sys.path.insert(0, str(project_root))

# Import tagger module from the package
from tagger import cli as tagger_module

# Make tagger module available in sys.modules for backward compatibility
sys.modules["tagger_module"] = tagger_module

# Make tagger module available to all tests
pytest_plugins = []
