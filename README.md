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
- **NEW:** YouTube thumbnail auto-fetching - automatically download and embed thumbnails from YouTube URLs

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
- Command-line options (`--execute`, etc.)
- File types (YAML files, audio files)

To enable completions:
- **Bash**: Completions are automatically loaded if you have bash-completion installed
- **Zsh**: Completions are automatically loaded (ensure `compinit` is called in your `.zshrc`)
- **Fish**: Completions are automatically loaded

**Man Pages**: When installed via Homebrew, comprehensive man pages are automatically installed:
- English: `man tagger`
- Japanese: `LANG=ja_JP.UTF-8 man tagger`

The man pages include detailed documentation for all command-line options, workflow examples, and troubleshooting guides.

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
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (automatically installed, for YouTube thumbnail fetching)
- [requests](https://requests.readthedocs.io/) (automatically installed, for HTTP requests)
- [Pillow](https://pillow.readthedocs.io/) (automatically installed, for YouTube thumbnail cropping)
- [ffmpeg](https://ffmpeg.org/) (optional, required for .aac to .m4a conversion)

### YouTube Thumbnail Auto-Fetching

Tagger automatically downloads and embeds YouTube thumbnails when generating YAML files.

#### How it works

When generating YAML from audio files with YouTube URLs in the comment field (e.g., files named `Artist - Song [VIDEO_ID].mp3`):

1. Tagger extracts the YouTube video ID from the filename
2. Stores the full YouTube URL in the comment tag
3. Automatically downloads the video thumbnail
4. Crops the thumbnail to a square aspect ratio (center crop)
5. Saves it as `cover.jpg` (single file) or `youtube_VIDEO_ID.jpg` (multiple files)
6. Sets the artwork field in the YAML to reference the thumbnail

**Example:**

```bash
# File: Artist - Song [dQw4w9WgXcQ].mp3
tagger --execute

# Results:
# - Creates cover.jpg (cropped to square)
# - Generated YAML includes:
#   - comment: https://www.youtube.com/watch?v=dQw4w9WgXcQ
#   - artwork: cover.jpg
```

**Features:**
- **Smart cropping**: Thumbnails are automatically cropped to square aspect ratio
- **Deduplication**: Same video ID across multiple files downloads only once
- **Graceful degradation**: Works without yt-dlp (uses direct URL with lower quality)
- **No override**: Won't replace existing artwork

### Bandcamp Artwork Auto-Fetching

Tagger automatically downloads and embeds Bandcamp album/track artwork when generating YAML files.

#### How it works

When generating YAML from audio files with Bandcamp URLs in the comment field:

1. Tagger detects the Bandcamp URL in the comment tag
2. Automatically downloads the album/track artwork using yt-dlp
3. Optionally crops the artwork to square aspect ratio (center crop)
4. Saves it as `cover.jpg` (single file) or `bandcamp_{label}_{album}.jpg` (multiple albums)
5. Sets the artwork field in the YAML to reference the artwork

**Example:**

```bash
# 1. Download from Bandcamp using yt-dlp
yt-dlp https://brutalkuts.bandcamp.com/album/the-ultimate-happy-2-the-core

# 2. Generate YAML
tagger --execute

# 3. Edit tagger.yaml and add Bandcamp URL to defaults.comment:
# defaults:
#   comment: https://brutalkuts.bandcamp.com/album/the-ultimate-happy-2-the-core

# 4. Apply YAML - artwork downloads automatically
tagger --execute tagger.yaml

# Results:
# - Creates cover.jpg (artwork from Bandcamp album)
# - All files get the artwork embedded
```

**Features:**
- **Automatic detection**: Scans comment field for Bandcamp URLs
- **Smart naming**: Same album shares artwork, different albums get unique files
- **Same cropping options**: Uses `--thumbnail-crop` flag (auto/square/none)
- **Deduplication**: Same URL across multiple files downloads only once
- **No override**: Won't replace existing artwork

**Supported Bandcamp URL formats:**
- `https://LABEL.bandcamp.com/album/ALBUM-SLUG`
- `https://LABEL.bandcamp.com/track/TRACK-SLUG`

**Setting Bandcamp URLs:**

You can set Bandcamp URLs in the comment field in the YAML file:

```yaml
defaults:
  comment: https://label.bandcamp.com/album/album-name

# Or per-file:
files:
- filename: "Label - Artist - Title [ID].mp3"
  comment: https://label.bandcamp.com/track/track-name
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

## Command-line Options

```
usage: tagger [-h] [-e] [-o OUTPUT] [--no-color] [--prefer-filename] [-v]
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
