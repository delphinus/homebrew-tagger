"""Pytest configuration and fixtures"""

import os
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

# Prevent numba from importing coverage module which conflicts with pytest-cov
# This must be set before segmenter.py is imported
os.environ["NUMBA_DISABLE_JIT"] = "0"  # Keep JIT enabled
os.environ["NUMBA_COVERAGE"] = "0"  # Disable coverage integration

# Preserve current directory to avoid issues with librosa lazy loading + coverage
# On Python 3.12, coverage module initialization can fail if cwd is deleted
_original_cwd = os.getcwd()

# Get the project root directory
project_root = Path(__file__).parent.parent

# Add project root to sys.path
sys.path.insert(0, str(project_root))

# Import tagger module using SourceFileLoader (works with files without .py extension)
tagger_path = project_root / "tagger"
loader = SourceFileLoader("tagger_module", str(tagger_path))
spec = spec_from_loader(loader.name, loader)
tagger_module = module_from_spec(spec)
sys.modules["tagger_module"] = tagger_module
spec.loader.exec_module(tagger_module)

# Make tagger module available to all tests
pytest_plugins = []


def pytest_runtest_setup(item):
    """
    Ensure current directory exists before each test.

    This fixes Python 3.12 + pytest-cov + librosa lazy loading issues where
    coverage module initialization fails if the current directory was deleted.
    """
    # Only change directory if current one doesn't exist
    try:
        os.getcwd()
    except (FileNotFoundError, OSError):
        # Current directory was deleted, restore to original
        os.chdir(_original_cwd)
