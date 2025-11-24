# Tagger

Audio file tag and filename manager using [mutagen](https://mutagen.readthedocs.io/).

## Features

- Manage tags for `.mp3` and `.m4a` files
- Automatically convert `.aac` files to `.m4a` format (lossless container conversion)
- Update tags from YAML configuration with `defaults` section for album-wide metadata
- Automatically extract common metadata to `defaults` when generating YAML
- Automatically rename files based on tags
- Generate YAML from existing audio files
- Dry-run mode by default to preview changes
- **NEW:** DJ mix segmentation - automatically detect track boundaries and generate CUE sheets

## Installation

### Using Homebrew (Recommended)

First, create a GitHub release for this project, then update the `tagger.rb` formula with the correct URL and SHA256.

```bash
# Add the tap (if you have a homebrew tap)
brew tap delphinus/tagger

# Install tagger
brew install tagger
```

**Shell Completion**: When installed via Homebrew, shell completions are automatically set up for Bash, Zsh, and Fish. Completions provide intelligent tab-completion for:
- Command-line options (`--execute`, `--segment`, etc.)
- File types (YAML files, audio files, CUE sheets)
- Tracklist sources (clipboard, text files, URLs)

To enable completions:
- **Bash**: Completions are automatically loaded if you have bash-completion installed
- **Zsh**: Completions are automatically loaded (ensure `compinit` is called in your `.zshrc`)
- **Fish**: Completions are automatically loaded

### Using pip

```bash
pip install -e .
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/delphinus/homebrew-tagger.git
cd homebrew-tagger

# Install dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x tagger

# Optionally, symlink to a directory in your PATH
ln -s $(pwd)/tagger /usr/local/bin/tagger
```

## Requirements

- Python 3.10 or later
- [mutagen](https://mutagen.readthedocs.io/) (automatically installed)
- [PyYAML](https://pyyaml.org/) (automatically installed)
- [pydantic](https://docs.pydantic.dev/) (automatically installed)
- [ffmpeg](https://ffmpeg.org/) (optional, required for .aac to .m4a conversion)

### Optional: DJ Mix Segmentation

For DJ mix segmentation features, install additional dependencies:

```bash
pip install librosa numpy pyperclip requests beautifulsoup4
```

Or install the segmentation extras:

```bash
pip install -e ".[segmentation]"
```

With Homebrew, these can be installed separately:

```bash
# After installing tagger via Homebrew
pip3 install librosa numpy pyperclip requests beautifulsoup4
```

## Usage

### AAC to M4A Conversion

If you have `.aac` files in your directory, tagger will automatically convert them to `.m4a` format before processing. This conversion is lossless - it only changes the container format without re-encoding the audio.

**Note:** ffmpeg must be installed for this feature to work. With Homebrew, ffmpeg is automatically installed as a dependency.

### Generate YAML from existing audio files

This will scan the current directory for `.mp3` and `.m4a` files and generate a YAML file:

```bash
# Dry-run mode (shows what would be generated)
tagger

# Execute and create the YAML file
tagger --execute
```

### Apply tags from YAML file

This will read the YAML file, update tags, and rename files according to the configuration:

```bash
# Dry-run mode (preview changes)
tagger tagger.yaml

# Execute changes
tagger --execute tagger.yaml
```

## YAML Format

The YAML file should have the following structure:

```yaml
defaults:
  album: Album Name
  albumartist: Album Artist Name
  genre: Rock
  year: 2023
  artwork: cover.jpg
  compilation: false

files:
  - filename: 01-artist-title.mp3
    track: 1
    artist: Artist Name
    title: Title Name

  - filename: 02-artist-another-title.mp3
    track: 2
    artist: Artist Name
    title: Another Title
```

### Defaults Section

The `defaults` section is optional and allows you to specify common metadata that applies to all files. This is useful for album-wide information like:

- `album`: Album name
- `albumartist`: Album artist
- `genre`: Music genre
- `year`: Release year
- `disc`: Disc number (for multi-disc albums)
- `artwork`: Path to artwork image file
- `compilation`: Boolean flag for compilation albums

**Automatic Optimization**: When generating YAML from audio files, tagger automatically detects common values across all files and moves them to the `defaults` section. This keeps your YAML files clean and concise.

**Overriding Defaults**: File-specific values always take priority over defaults. For example:

```yaml
defaults:
  album: Greatest Hits
  genre: Rock

files:
  - filename: 01-special-track.mp3
    track: 1
    artist: Artist Name
    title: Special Track
    genre: Pop  # Overrides the default "Rock" for this file only
```

### Required Fields

- `filename`: Original filename (required)
- `title`: Track title (required)

### Optional Fields

- `track`: Track number
- `disc`: Disc number (for multi-disc albums)
- `artist`: Artist name (can be empty or omitted for artist-less tracks)
- `album`: Album name
- `albumartist`: Album artist (for compilations)
- `genre`: Music genre
- `year`: Release year
- `artwork`: Path to artwork image file (JPG or PNG)
- `compilation`: Boolean flag for compilation albums

### Filename Parsing

When generating YAML from audio files, if tags are missing, tagger will automatically parse metadata from filenames.

**Parsing is flexible** - any number of spaces (1 or more) is accepted:

- `01 Artist - Title.mp3` → track=1, artist="Artist", title="Title"
- `01  - Title.mp3` → track=1, artist="", title="Title"
- `01    -    Title.mp3` → track=1, artist="", title="Title" (extra spaces are OK)
- `01 Title.mp3` → track=1, artist="", title="Title"
- `Artist - Title.mp3` → artist="Artist", title="Title"
- `Title.mp3` → title="Title"

This is especially useful for files without embedded tags. The parsed values are used as fallbacks when actual ID3/MP4 tags are not present.

## Examples

### Example 1: Organize a music album

1. Put all your music files in a directory
2. Generate a YAML template:

```bash
cd ~/Music/MyAlbum
tagger --execute
```

3. Edit `tagger.yaml` to correct any tag information
4. Apply the changes:

```bash
tagger --execute tagger.yaml
```

### Example 2: Add artwork to all tracks

1. Place your `cover.jpg` in the music directory
2. Edit the YAML file and add `artwork: cover.jpg` to each entry
3. Apply changes:

```bash
tagger --execute tagger.yaml
```

### Example 3: Preview changes before applying

Always run without `--execute` first to preview:

```bash
# Preview what would be generated
tagger

# Preview what would be changed
tagger tagger.yaml

# Only execute if everything looks good
tagger --execute tagger.yaml
```

## Filename Generation

When applying tags, files will be automatically renamed based on their tags using strict spacing rules:

- Track + Artist: `01 Artist - Title.mp3` (1 space after track, 1 space before hyphen, 1 space after hyphen)
- Track only: `01  - Title.mp3` (2 spaces before hyphen when no artist, 1 space after hyphen)
- Artist only: `Artist - Title.mp3` (1 space before hyphen, 1 space after hyphen)
- Title only: `Title.mp3`

**Note**: When there's no artist but there is a track number, use 2 spaces before the hyphen to distinguish it from the track+artist format.

Invalid filename characters (`<>:"/\|?*`) are replaced with underscores.

## Supported Tag Fields

### MP3 (ID3 tags)

- Title (TIT2)
- Artist (TPE1)
- Album (TALB)
- Album Artist (TPE2)
- Genre (TCON)
- Year (TDRC)
- Track Number (TRCK)
- Disc Number (TPOS)
- Compilation (TCMP)
- Artwork (APIC)

### M4A (MP4 tags)

- Title (©nam)
- Artist (©ART)
- Album (©alb)
- Album Artist (aART)
- Genre (©gen)
- Year (©day)
- Track Number (trkn)
- Disc Number (disk)
- Compilation (cpil)
- Artwork (covr)

## DJ Mix Segmentation

Tagger can automatically analyze DJ mixes and detect track boundaries using audio feature analysis. This is useful for splitting long DJ sets into individual tracks.

### How It Works

The segmentation algorithm analyzes:
- **Spectral features**: Changes in frequency distribution
- **Chroma features**: Key and tonality changes
- **Timbral features**: Changes in sound texture (MFCC)

It detects transition points where these features change significantly, indicating a new track.

### Basic Usage

```bash
# Analyze a DJ mix and generate a CUE sheet
tagger --segment mix.mp3

# Specify output file
tagger --segment mix.mp3 -o custom.cue

# Adjust sensitivity (0.0-1.0, default 0.5)
# Higher = more sensitive = more boundaries detected
tagger --segment mix.mp3 --sensitivity 0.7

# Lower sensitivity = fewer boundaries
tagger --segment mix.mp3 --sensitivity 0.3
```

### Using Tracklists

Tracklists significantly improve segmentation accuracy by:
- Providing the exact number of tracks (constraint for boundary detection)
- Including track names and artists in the CUE sheet
- Using timestamps if available (skips detection entirely)

#### From Clipboard

Copy the tracklist to your clipboard, then:

```bash
tagger --segment mix.mp3 --tracklist-clipboard
```

#### From a File

Save the tracklist to a text file:

```bash
tagger --segment mix.mp3 --tracklist-file tracklist.txt
```

#### From SoundCloud URL

Extract tracklist directly from a SoundCloud page:

```bash
tagger --segment mix.mp3 --tracklist "https://soundcloud.com/user/track"
```

#### Tracklist Formats

The parser supports various formats:

```
1. Artist - Title
2. Another Artist - Another Title [5:30]
3. Third Artist - Third Title

01 Artist - Title
02 Artist - Title

Artist - Title
Another Artist - Another Title

1. Title Only
2. Another Title
```

If timestamps are provided (e.g., `[5:30]`), they will be used directly instead of audio analysis.

### Output Format

The tool generates a CUE sheet compatible with mp3DirectCut and other audio tools.

Without tracklist:

```cue
FILE "mix.mp3" MP3
  TRACK 01 AUDIO
    TITLE "Track 01"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    TITLE "Track 02"
    INDEX 01 03:45:23
  TRACK 03 AUDIO
    TITLE "Track 03"
    INDEX 01 07:12:51
```

With tracklist:

```cue
FILE "mix.mp3" MP3
  TRACK 01 AUDIO
    PERFORMER "Fracus & Darwin"
    TITLE "Groove Control"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    PERFORMER "Stompy & Flyin'"
    TITLE "Come Follow Me (DJ Storm & Bananaman Remix)"
    INDEX 01 03:45:23
  TRACK 03 AUDIO
    PERFORMER "J.D.S."
    TITLE "Higher Love (Fracus & Darwin's Electrified Mix)"
    INDEX 01 07:12:51
```

### Notes

- Works best with **non-stop mixes** where tracks blend together
- Designed for electronic music (Trance, House, Techno, Hardcore, etc.)
- **Not based on silence detection** - uses musical feature analysis
- Results are **candidate boundaries** - manual verification recommended
- Minimum 60 seconds between detected boundaries to avoid false positives
- Adjust `--sensitivity` based on your mix:
  - Tracks with **clear transitions**: use lower sensitivity (0.3-0.4)
  - **Heavily blended mixes**: use higher sensitivity (0.6-0.8)

### Example Workflows

#### Workflow 1: With Tracklist from SoundCloud

1. Find your mix on SoundCloud (e.g., https://soundcloud.com/alstorm/happy-hardcore-mix)

2. Generate CUE sheet with tracklist:
   ```bash
   tagger --segment "Happy Hardcore Mix.mp3" \
          --tracklist "https://soundcloud.com/alstorm/happy-hardcore-mix" \
          --sensitivity 0.6
   ```

3. Open the mix in mp3DirectCut

4. Load the generated CUE sheet (File → Open CUE sheet)

5. Review the detected boundaries and adjust as needed

6. Split the mix - track names are already filled in!

#### Workflow 2: With Tracklist from Clipboard

1. Copy tracklist from mix description (on SoundCloud, Mixcloud, etc.)

2. Generate CUE sheet:
   ```bash
   tagger --segment "DJ Mix.mp3" --tracklist-clipboard
   ```

3. Open in mp3DirectCut and split

#### Workflow 3: Without Tracklist

1. Generate CUE sheet with audio analysis only:
   ```bash
   tagger --segment "DJ Mix.mp3" --sensitivity 0.5
   ```

2. Open in mp3DirectCut, review, and manually add track names

## Command-line Options

```
usage: tagger [-h] [-e] [-o OUTPUT] [--segment AUDIO_FILE] [--sensitivity SENSITIVITY]
              [--tracklist TRACKLIST] [--tracklist-file TRACKLIST_FILE]
              [--tracklist-clipboard] [--no-color] [--prefer-filename] [-v]
              [yaml_file]

Manage audio file tags and filenames using mutagen

positional arguments:
  yaml_file             YAML file with tag information (if not provided,
                        generates YAML from current directory)

optional arguments:
  -h, --help            show this help message and exit
  -e, --execute         Execute changes (default is dry-run mode)
  -o OUTPUT, --output OUTPUT
                        Output YAML file name when generating (default:
                        tagger.yaml)
  --segment AUDIO_FILE  Segment a DJ mix and generate CUE sheet
  --sensitivity SENSITIVITY
                        Detection sensitivity for DJ mix segmentation
                        (0.0-1.0, default: 0.5)
  --tracklist TRACKLIST
                        Tracklist source: 'clipboard', file path, or SoundCloud URL
  --tracklist-file TRACKLIST_FILE
                        Read tracklist from a text file
  --tracklist-clipboard
                        Read tracklist from clipboard
  --no-color            Disable colored output
  --prefer-filename     Prefer metadata from filenames over embedded tags
  -v, --version         Show version number
```

## License

MIT License

## Author

delphinus

## Repository

https://github.com/delphinus/homebrew-tagger
