#!/usr/bin/env python3
"""
Setup script for tagger
"""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tagger",
    version="1.25.1",
    description="Audio file tag and filename manager using mutagen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="delphinus",
    url="https://github.com/delphinus/tagger",
    packages=[],  # No Python packages, only script
    scripts=["tagger"],
    install_requires=[
        "mutagen>=1.45.0",
        "PyYAML>=6.0",
        "pydantic>=2.0.0",
        "yt-dlp>=2024.0.0",  # For YouTube thumbnail fetching
        "requests>=2.31.0",  # For direct URL downloads (YouTube fallback, SoundCloud)
        "Pillow>=10.0.0",  # For YouTube thumbnail cropping
    ],
    extras_require={
        "youtube": [
            # Pillow is now in install_requires (required dependency)
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "psutil>=5.9.0",
            # Pillow is now in install_requires (required dependency)
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
