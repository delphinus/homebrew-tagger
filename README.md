# Tagger

Audio file tag and filename manager using [mutagen](https://mutagen.readthedocs.io/).

## Features

- Manage tags for `.mp3` and `.m4a` files
- Update tags from YAML configuration
- Automatically rename files based on tags
- Generate YAML from existing audio files
- Dry-run mode by default to preview changes

## Installation

### Using Homebrew (Recommended)

First, create a GitHub release for this project, then update the `tagger.rb` formula with the correct URL and SHA256.

```bash
# Add the tap (if you have a homebrew tap)
brew tap delphinus/tagger

# Install tagger
brew install tagger
```

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

## Usage

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
files:
  - filename: 01-artist-title.mp3
    track: 1
    artist: Artist Name
    title: Title Name
    album: Album Name
    albumartist: Album Artist Name
    genre: Rock
    year: 2023
    artwork: cover.jpg
    compilation: false

  - filename: 02-artist-another-title.mp3
    track: 2
    artist: Artist Name
    title: Another Title
    album: Album Name
    albumartist: Album Artist Name
    genre: Rock
    year: 2023
    artwork: cover.jpg
    compilation: false
```

### Required Fields

- `filename`: Original filename (required)
- `track`: Track number (required)
- `artist`: Artist name (required)
- `title`: Track title (required)

### Optional Fields

- `album`: Album name
- `albumartist`: Album artist (for compilations)
- `genre`: Music genre
- `year`: Release year
- `artwork`: Path to artwork image file (JPG or PNG)
- `compilation`: Boolean flag for compilation albums

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

When applying tags, files will be automatically renamed based on their tags:

- With track number: `01-Artist-Title.mp3`
- Without track number: `Artist-Title.mp3`

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
- Compilation (cpil)
- Artwork (covr)

## Command-line Options

```
usage: tagger [-h] [-e] [-o OUTPUT] [yaml_file]

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
```

## License

MIT License

## Author

delphinus

## Repository

https://github.com/delphinus/homebrew-tagger
