"""Pytest configuration and fixtures"""
import sys
from pathlib import Path
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

# Get the project root directory
project_root = Path(__file__).parent.parent

# Add project root to sys.path
sys.path.insert(0, str(project_root))

# Import tagger module using SourceFileLoader (works with files without .py extension)
tagger_path = project_root / "tagger"
loader = SourceFileLoader("tagger_module", str(tagger_path))
spec = spec_from_loader(loader.name, loader)
tagger_module = module_from_spec(spec)
sys.modules['tagger_module'] = tagger_module
spec.loader.exec_module(tagger_module)

# Make tagger module available to all tests
pytest_plugins = []
