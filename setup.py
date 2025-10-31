#!/usr/bin/env python3
"""
Setup script for tagger
"""

from setuptools import setup

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tagger',
    version='1.1.0',
    description='Audio file tag and filename manager using mutagen',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='delphinus',
    url='https://github.com/delphinus/tagger',
    py_modules=[],
    scripts=['tagger'],
    install_requires=[
        'mutagen>=1.45.0',
        'PyYAML>=6.0',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)
