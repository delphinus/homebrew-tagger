# NCS (NoCopyrightSounds) Test Fixtures

This directory contains test audio files from NoCopyrightSounds for integration testing.

## Files

- `track1_tobu_candyland.mp3` - Tobu - Candyland [NCS Release]
- `track2_spektrem_shine.mp3` - Spektrem - Shine [NCS Release]
- `track3_different_heaven_my_heart.mp3` - Different Heaven & EH!DE - My Heart [NCS Release]
- `metadata.json` - Track metadata and expected test results

## License

All tracks are NCS (NoCopyrightSounds) releases and are free to use with proper attribution.

**License**: NCS Release - Free to use with credit
**Commercial Use**: Allowed with attribution
**Modification**: Allowed
**Test Purpose**: These files are used exclusively for automated testing

## Attribution

- **Tobu - Candyland**: [ncs.io/candyland](https://ncs.io/candyland)
- **Spektrem - Shine**: [ncs.io/shine](https://ncs.io/shine)
- **Different Heaven & EH!DE - My Heart**: [ncs.io/myheart](https://ncs.io/myheart)

## Source

Downloaded from Internet Archive:
- [Tobu - Candyland](https://archive.org/details/tobu-candyland-ncs-release-audio)
- [Spektrem - Shine](https://archive.org/details/SpektremShineNCSRelease_201612)
- [Different Heaven - My Heart](https://archive.org/details/DifferentHeavenEHDEMyHeartNCSRelease)

## Usage in Tests

These tracks are used to create test DJ mixes for verifying:
1. Boundary detection between concatenated tracks
2. Music recognition with AcoustID/Shazam APIs
3. CUE sheet generation

See `tests/test_dj_mix_recognition.py` for usage examples.
