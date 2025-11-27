#!/usr/bin/env python3
"""
Setup script for tagger
"""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tagger",
    version="1.16.0",
    description="Audio file tag and filename manager using mutagen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="delphinus",
    url="https://github.com/delphinus/tagger",
    py_modules=["segmenter", "tracklist_parser", "music_recognizer"],
    scripts=["tagger"],
    install_requires=[
        "mutagen>=1.45.0",
        "PyYAML>=6.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "segmentation": [
            "librosa>=0.10.0",
            "numpy>=1.24.0",
            "pyperclip>=1.8.0",  # For clipboard support
            "requests>=2.31.0",  # For SoundCloud URL fetching
            "beautifulsoup4>=4.12.0",  # For HTML parsing
            "tqdm>=4.66.0",  # For progress bars
            "pyacoustid>=1.3.0",  # For music recognition (AcoustID)
            "shazamio>=0.8.0",  # For music recognition (Shazam fallback)
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "psutil>=5.9.0",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Multimedia :: Sound/Audio",
    ],
)
