"""
Tagger - Audio file tag and filename manager using mutagen

This script manages tags and filenames for .mp3 and .m4a files.
It can also convert .aac files to .m4a format (lossless container conversion).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

try:
    from mutagen.id3 import (
        APIC,
        ID3,
        TALB,
        TCMP,
        TCON,
        TDRC,
        TIT2,
        TPE1,
        TPE2,
        TRCK,
        TXXX,
    )
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4, MP4Cover
except ImportError:
    print(
        "Error: mutagen is not installed. Please install it with: pip install mutagen",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from pydantic import BaseModel, Field, ValidationError, field_validator
except ImportError:
    print(
        "Error: pydantic is not installed. Please install it with: pip install pydantic",
        file=sys.stderr,
    )
    sys.exit(1)


# Pydantic models for YAML schema validation
class Defaults(BaseModel):
    """Default values applied to all files"""

    model_config = {"extra": "forbid"}

    album: str | None = None
    albumartist: str | None = None
    genre: str | None = None
    year: int | None = None
    artwork: str | None = None
    compilation: bool | None = None
    label: str | None = None
    bandcamp_id: str | None = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int | None) -> int | None:
        """Validate year is reasonable"""
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError("Year must be between 1900 and 2100")
        return v


class FileEntry(BaseModel):
    """Schema for a single file entry in the YAML"""

    model_config = {"extra": "forbid"}

    filename: str = Field(..., description="Original filename")
    track: int | None = None
    artist: str | None = None
    title: str | None = None
    album: str | None = None
    albumartist: str | None = None
    genre: str | None = None
    year: int | None = None
    artwork: str | None = None
    compilation: bool | None = None
    label: str | None = None
    bandcamp_id: str | None = None

    @field_validator("track")
    @classmethod
    def validate_track(cls, v: int | None) -> int | None:
        """Validate track number is positive"""
        if v is not None and v < 1:
            raise ValueError("Track number must be positive")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int | None) -> int | None:
        """Validate year is reasonable"""
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError("Year must be between 1900 and 2100")
        return v


class TaggerConfig(BaseModel):
    """Schema for the complete YAML configuration"""

    model_config = {"extra": "forbid"}

    defaults: Defaults | None = None
    files: list[FileEntry] = Field(..., min_length=1, description="List of audio files")

    @field_validator("files")
    @classmethod
    def validate_files_not_empty(cls, v: list[FileEntry]) -> list[FileEntry]:
        """Ensure files list is not empty"""
        if not v:
            raise ValueError("Files list cannot be empty")
        return v


class Tagger:
    """Main class for managing audio file tags and filenames"""

    SUPPORTED_EXTENSIONS = {".mp3", ".m4a"}

    def __init__(self, execute: bool = False):
        self.execute = execute
        self.dry_run = not execute

    def log(self, message: str):
        """Print log message"""
        prefix = "[DRY-RUN] " if self.dry_run else ""
        print(f"{prefix}{message}")

    def find_audio_files(self, directory: str = ".") -> list[Path]:
        """Find all supported audio files in the directory"""
        path = Path(directory)
        files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            files.extend(path.glob(f"*{ext}"))
        return sorted(files)

    def check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        return shutil.which("ffmpeg") is not None

    def convert_aac_to_m4a(self, aac_file: Path) -> Path | None:
        """Convert AAC file to M4A format without re-encoding (lossless container conversion)"""
        if not self.check_ffmpeg():
            self.log("Warning: ffmpeg not found. Cannot convert .aac files to .m4a")
            return None

        m4a_file = aac_file.with_suffix(".m4a")

        if self.dry_run:
            self.log(f"Would convert: {aac_file.name} -> {m4a_file.name}")
            return m4a_file

        try:
            # Convert container without re-encoding (lossless)
            subprocess.run(
                ["ffmpeg", "-i", str(aac_file), "-c", "copy", "-y", str(m4a_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.log(f"Converted: {aac_file.name} -> {m4a_file.name}")

            # Remove original .aac file after successful conversion
            aac_file.unlink()
            self.log(f"Removed original: {aac_file.name}")

            return m4a_file
        except subprocess.CalledProcessError as e:
            self.log(f"Error: Failed to convert {aac_file}: {e.stderr}")
            return None
        except Exception as e:
            self.log(f"Error: Could not convert {aac_file}: {e}")
            return None

    def find_and_convert_aac_files(self, directory: str = ".") -> list[Path]:
        """Find all .aac files and convert them to .m4a"""
        path = Path(directory)
        aac_files = list(path.glob("*.aac"))

        if not aac_files:
            return []

        self.log(f"Found {len(aac_files)} .aac file(s) to convert")

        converted_files = []
        for aac_file in aac_files:
            m4a_file = self.convert_aac_to_m4a(aac_file)
            if m4a_file:
                converted_files.append(m4a_file)

        return converted_files

    def parse_filename(self, filename: str) -> dict[str, any]:
        """Parse metadata from filename

        Supported patterns (spaces are flexible, 1+ spaces allowed):
        - Label - Artist - Title [ID].mp3 -> label="Label", artist="Artist", title="Title", bandcamp_id="ID"
        - 01 Artist - Title.mp3 -> track=1, artist="Artist", title="Title"
        - 01  - Title.mp3 -> track=1, artist="", title="Title"
        - 01 Title.mp3 -> track=1, artist="", title="Title"
        - Artist - Title.mp3 -> artist="Artist", title="Title"
        - Title.mp3 -> title="Title"
        """
        # Remove extension
        name = Path(filename).stem

        track = None
        artist = None
        title = None
        label = None
        bandcamp_id = None

        # Try patterns in order of specificity (spaces: 1+ allowed)
        # Pattern 0: "Label - Artist - Title [ID]" (Bandcamp format)
        match = re.match(r"^(.+?)\s+-\s+(.+?)\s+-\s+(.+?)\s+\[(\d+)\]$", name)
        if match:
            label = match.group(1).strip()
            artist = match.group(2).strip()
            title = match.group(3).strip()
            bandcamp_id = match.group(4).strip()
            return {
                "track": None,
                "artist": artist if artist else None,
                "title": title if title else None,
                "label": label if label else None,
                "bandcamp_id": bandcamp_id if bandcamp_id else None,
            }

        # Pattern 1: "01 Artist - Title" (track + artist + title)
        match = re.match(r"^(\d+)\s+(.+?)\s+-\s+(.+)$", name)
        if match:
            track = int(match.group(1))
            artist = match.group(2).strip()
            title = match.group(3).strip()
            return {
                "track": track,
                "artist": artist if artist else None,
                "title": title if title else None,
            }

        # Pattern 2: "01  - Title" (track + title, no artist)
        match = re.match(r"^(\d+)\s+-\s+(.+)$", name)
        if match:
            track = int(match.group(1))
            artist = ""
            title = match.group(2).strip()
            return {
                "track": track,
                "artist": None,
                "title": title if title else None,
            }

        # Pattern 3: "01 Title" (track + title, no separator)
        match = re.match(r"^(\d+)\s+(.+)$", name)
        if match:
            track = int(match.group(1))
            artist = ""
            title = match.group(2).strip()
            return {
                "track": track,
                "artist": None,
                "title": title if title else None,
            }

        # Pattern 4: "Artist - Title" (artist + title, no track)
        match = re.match(r"^(.+?)\s+-\s+(.+)$", name)
        if match:
            track = None
            artist = match.group(1).strip()
            title = match.group(2).strip()
            return {
                "track": track,
                "artist": artist if artist else None,
                "title": title if title else None,
            }

        # Pattern 5: "Title" (title only)
        title = name.strip()
        return {
            "track": None,
            "artist": None,
            "title": title if title else None,
        }

    def read_tags(self, filepath: Path) -> dict[str, any]:
        """Read tags from an audio file"""
        ext = filepath.suffix.lower()
        tags = {
            "filename": filepath.name,
            "track": None,
            "artist": None,
            "title": None,
            "album": None,
            "albumartist": None,
            "genre": None,
            "year": None,
            "artwork": None,
            "compilation": None,
            "label": None,
            "bandcamp_id": None,
        }

        try:
            if ext == ".mp3":
                audio = MP3(str(filepath), ID3=ID3)
                if audio.tags:
                    # Track number
                    if "TRCK" in audio.tags:
                        track_str = str(audio.tags["TRCK"])
                        tags["track"] = (
                            int(track_str.split("/")[0])
                            if "/" in track_str
                            else int(track_str)
                        )

                    # Text fields
                    if "TIT2" in audio.tags:
                        tags["title"] = str(audio.tags["TIT2"])
                    if "TPE1" in audio.tags:
                        tags["artist"] = str(audio.tags["TPE1"])
                    if "TALB" in audio.tags:
                        tags["album"] = str(audio.tags["TALB"])
                    if "TPE2" in audio.tags:
                        tags["albumartist"] = str(audio.tags["TPE2"])
                    if "TCON" in audio.tags:
                        tags["genre"] = str(audio.tags["TCON"])
                    if "TDRC" in audio.tags:
                        tags["year"] = int(str(audio.tags["TDRC"]))
                    if "TCMP" in audio.tags:
                        tags["compilation"] = str(audio.tags["TCMP"]) == "1"

                    # Artwork
                    if "APIC:" in audio.tags:
                        tags["artwork"] = "<embedded>"

                    # Custom tags (TXXX frames)
                    if "TXXX:LABEL" in audio.tags:
                        tags["label"] = str(audio.tags["TXXX:LABEL"])
                    if "TXXX:BANDCAMP_ID" in audio.tags:
                        tags["bandcamp_id"] = str(audio.tags["TXXX:BANDCAMP_ID"])

            elif ext == ".m4a":
                audio = MP4(str(filepath))
                if audio.tags:
                    # Track number
                    if "\xa9nam" in audio.tags:
                        tags["title"] = audio.tags["\xa9nam"][0]
                    if "\xa9ART" in audio.tags:
                        tags["artist"] = audio.tags["\xa9ART"][0]
                    if "\xa9alb" in audio.tags:
                        tags["album"] = audio.tags["\xa9alb"][0]
                    if "aART" in audio.tags:
                        tags["albumartist"] = audio.tags["aART"][0]
                    if "\xa9gen" in audio.tags:
                        tags["genre"] = audio.tags["\xa9gen"][0]
                    if "\xa9day" in audio.tags:
                        tags["year"] = int(audio.tags["\xa9day"][0])
                    if "trkn" in audio.tags:
                        tags["track"] = audio.tags["trkn"][0][0]
                    if "cpil" in audio.tags:
                        tags["compilation"] = bool(audio.tags["cpil"][0])

                    # Artwork
                    if "covr" in audio.tags:
                        tags["artwork"] = "<embedded>"

                    # Custom tags (freeform)
                    if "----:com.apple.iTunes:LABEL" in audio.tags:
                        tags["label"] = audio.tags["----:com.apple.iTunes:LABEL"][
                            0
                        ].decode("utf-8")
                    if "----:com.apple.iTunes:BANDCAMP_ID" in audio.tags:
                        tags["bandcamp_id"] = audio.tags[
                            "----:com.apple.iTunes:BANDCAMP_ID"
                        ][0].decode("utf-8")

        except Exception as e:
            self.log(f"Warning: Could not read tags from {filepath}: {e}")

        # If track, artist, title, label, or bandcamp_id is missing, try to parse from filename
        if (
            tags["track"] is None
            or tags["artist"] is None
            or tags["title"] is None
            or tags["label"] is None
            or tags["bandcamp_id"] is None
        ):
            parsed = self.parse_filename(filepath.name)

            if tags["track"] is None and parsed.get("track") is not None:
                tags["track"] = parsed["track"]
            if tags["artist"] is None and parsed.get("artist") is not None:
                tags["artist"] = parsed["artist"]
            if tags["title"] is None and parsed.get("title") is not None:
                tags["title"] = parsed["title"]
            if tags["label"] is None and parsed.get("label") is not None:
                tags["label"] = parsed["label"]
            if tags["bandcamp_id"] is None and parsed.get("bandcamp_id") is not None:
                tags["bandcamp_id"] = parsed["bandcamp_id"]

        return tags

    def write_tags(self, filepath: Path, tags: dict[str, any]) -> bool:
        """Write tags to an audio file"""
        ext = filepath.suffix.lower()

        if self.dry_run:
            self.log(f"Would update tags for: {filepath}")
            return True

        try:
            if ext == ".mp3":
                audio = MP3(str(filepath), ID3=ID3)

                # Create ID3 tag if it doesn't exist
                if audio.tags is None:
                    audio.add_tags()

                # Set tags
                if tags.get("title"):
                    audio.tags.add(TIT2(encoding=3, text=tags["title"]))
                if tags.get("artist"):
                    audio.tags.add(TPE1(encoding=3, text=tags["artist"]))
                if tags.get("album"):
                    audio.tags.add(TALB(encoding=3, text=tags["album"]))
                if tags.get("albumartist"):
                    audio.tags.add(TPE2(encoding=3, text=tags["albumartist"]))
                if tags.get("genre"):
                    audio.tags.add(TCON(encoding=3, text=tags["genre"]))
                if tags.get("year"):
                    audio.tags.add(TDRC(encoding=3, text=str(tags["year"])))
                if tags.get("track"):
                    audio.tags.add(TRCK(encoding=3, text=str(tags["track"])))
                if tags.get("compilation") is not None:
                    audio.tags.add(
                        TCMP(encoding=3, text="1" if tags["compilation"] else "0")
                    )

                # Custom tags
                if tags.get("label"):
                    audio.tags.add(TXXX(encoding=3, desc="LABEL", text=tags["label"]))
                if tags.get("bandcamp_id"):
                    audio.tags.add(
                        TXXX(encoding=3, desc="BANDCAMP_ID", text=tags["bandcamp_id"])
                    )

                # Artwork
                if tags.get("artwork") and tags["artwork"] != "<embedded>":
                    artwork_path = Path(tags["artwork"])
                    if artwork_path.exists():
                        with open(artwork_path, "rb") as f:
                            audio.tags.add(
                                APIC(
                                    encoding=3,
                                    mime=(
                                        "image/jpeg"
                                        if artwork_path.suffix.lower()
                                        in [".jpg", ".jpeg"]
                                        else "image/png"
                                    ),
                                    type=3,  # Cover (front)
                                    desc="Cover",
                                    data=f.read(),
                                )
                            )

                audio.save()

            elif ext == ".m4a":
                audio = MP4(str(filepath))

                # Set tags
                if tags.get("title"):
                    audio.tags["\xa9nam"] = tags["title"]
                if tags.get("artist"):
                    audio.tags["\xa9ART"] = tags["artist"]
                if tags.get("album"):
                    audio.tags["\xa9alb"] = tags["album"]
                if tags.get("albumartist"):
                    audio.tags["aART"] = tags["albumartist"]
                if tags.get("genre"):
                    audio.tags["\xa9gen"] = tags["genre"]
                if tags.get("year"):
                    audio.tags["\xa9day"] = str(tags["year"])
                if tags.get("track"):
                    audio.tags["trkn"] = [(tags["track"], 0)]
                if tags.get("compilation") is not None:
                    audio.tags["cpil"] = [tags["compilation"]]

                # Custom tags
                if tags.get("label"):
                    audio.tags["----:com.apple.iTunes:LABEL"] = tags["label"].encode(
                        "utf-8"
                    )
                if tags.get("bandcamp_id"):
                    audio.tags["----:com.apple.iTunes:BANDCAMP_ID"] = tags[
                        "bandcamp_id"
                    ].encode("utf-8")

                # Artwork
                if tags.get("artwork") and tags["artwork"] != "<embedded>":
                    artwork_path = Path(tags["artwork"])
                    if artwork_path.exists():
                        with open(artwork_path, "rb") as f:
                            cover_data = f.read()
                            if artwork_path.suffix.lower() == ".png":
                                audio.tags["covr"] = [
                                    MP4Cover(
                                        cover_data, imageformat=MP4Cover.FORMAT_PNG
                                    )
                                ]
                            else:
                                audio.tags["covr"] = [
                                    MP4Cover(
                                        cover_data, imageformat=MP4Cover.FORMAT_JPEG
                                    )
                                ]

                audio.save()

            self.log(f"Updated tags for: {filepath}")
            return True

        except Exception as e:
            self.log(f"Error: Could not write tags to {filepath}: {e}")
            return False

    def sanitize_filename(self, name: str) -> str:
        """Sanitize filename by removing invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        return name

    def generate_filename(self, tags: dict[str, any]) -> str:
        """Generate filename from tags"""
        track = tags.get("track", "")
        artist = tags.get("artist", "")
        title = tags.get("title", "Unknown Title")

        # Get original extension
        original_filename = tags.get("filename", ".mp3")
        ext = Path(original_filename).suffix

        # Build filename based on available metadata
        # Hyphens use 1 space before and after, except track-only uses 2 spaces before hyphen
        if track and artist:
            # Format: 01 Artist - Title.mp3
            filename = f"{track:02d} {artist} - {title}{ext}"
        elif track:
            # Format: 01  - Title.mp3 (no artist, 2 spaces before hyphen)
            filename = f"{track:02d}  - {title}{ext}"
        elif artist:
            # Format: Artist - Title.mp3 (no track)
            filename = f"{artist} - {title}{ext}"
        else:
            # Format: Title.mp3 (no track, no artist)
            filename = f"{title}{ext}"

        return self.sanitize_filename(filename)

    def rename_file(self, old_path: Path, new_filename: str) -> Path | None:
        """Rename a file"""
        new_path = old_path.parent / new_filename

        if old_path == new_path:
            return old_path

        if self.dry_run:
            self.log(f"Would rename: {old_path.name} -> {new_filename}")
            return new_path

        try:
            old_path.rename(new_path)
            self.log(f"Renamed: {old_path.name} -> {new_filename}")
            return new_path
        except Exception as e:
            self.log(f"Error: Could not rename {old_path}: {e}")
            return None

    def generate_yaml(self, output_file: str = "tagger.yaml"):
        """Generate YAML file from current directory audio files"""
        # First, convert any .aac files to .m4a
        self.find_and_convert_aac_files()

        files = self.find_audio_files()

        if not files:
            self.log("No audio files found in current directory")
            return

        self.log(f"Found {len(files)} audio file(s)")

        # Read tags from all files
        entries = []
        for filepath in files:
            tags = self.read_tags(filepath)
            # Remove None values
            entry = {k: v for k, v in tags.items() if v is not None}
            entries.append(entry)

        # Extract common fields to defaults
        common_fields = [
            "album",
            "albumartist",
            "genre",
            "year",
            "artwork",
            "compilation",
            "label",
            "bandcamp_id",
        ]
        defaults = {}

        if len(entries) > 1:  # Only extract defaults if there are multiple files
            for field in common_fields:
                # Get all values for this field (excluding None)
                values = [entry.get(field) for entry in entries if field in entry]

                # If all files have the same non-None value, move to defaults
                if (
                    values
                    and len(values) == len(entries)
                    and len(set(str(v) for v in values)) == 1
                ):
                    defaults[field] = values[0]

            # Remove common fields from individual entries
            if defaults:
                for entry in entries:
                    for field in defaults:
                        entry.pop(field, None)

        # Create YAML structure
        yaml_data = {}
        if defaults:
            yaml_data["defaults"] = defaults
        yaml_data["files"] = entries

        # Validate YAML structure
        try:
            config = TaggerConfig(**yaml_data)
            # Convert back to dict for YAML serialization
            yaml_data = config.model_dump(exclude_none=True, mode="python")
        except ValidationError as e:
            self.log(f"Error: Generated YAML validation failed:")
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                self.log(f"  {field}: {error['msg']}")
            sys.exit(1)

        # Generate YAML string
        yaml_str = yaml.dump(
            yaml_data, allow_unicode=True, default_flow_style=False, sort_keys=False
        )

        if self.dry_run:
            self.log(f"Would create {output_file} with content:")
            print("\n" + "=" * 60)
            print(yaml_str)
            print("=" * 60)
        else:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(yaml_str)
            self.log(f"Created {output_file}")

    def apply_yaml(self, yaml_file: str):
        """Apply tags and filenames from YAML file"""
        # First, convert any .aac files to .m4a
        self.find_and_convert_aac_files()

        if not os.path.exists(yaml_file):
            self.log(f"Error: YAML file not found: {yaml_file}")
            sys.exit(1)

        # Load YAML
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Validate YAML structure
        try:
            config = TaggerConfig(**data)
            self.log("YAML validation successful")
        except ValidationError as e:
            self.log(f"Error: YAML validation failed for {yaml_file}:")
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                self.log(f"  {field}: {error['msg']}")
            self.log("\nCommon issues:")
            self.log(
                "  - Check for typos in field names (e.g., 'default' should be 'defaults')"
            )
            self.log("  - Ensure all required fields are present")
            self.log(
                "  - Verify data types (e.g., year should be a number, not a string)"
            )
            sys.exit(1)

        # Get defaults if present
        defaults = (
            config.defaults.model_dump(exclude_none=True, mode="python")
            if config.defaults
            else {}
        )

        files_data = [
            f.model_dump(exclude_none=True, mode="python") for f in config.files
        ]
        self.log(f"Processing {len(files_data)} file(s) from {yaml_file}")

        for file_data in files_data:
            if "filename" not in file_data:
                self.log("Warning: Skipping entry without 'filename'")
                continue

            original_filename = file_data["filename"]
            filepath = Path(original_filename)

            if not filepath.exists():
                self.log(f"Warning: File not found: {original_filename}")
                continue

            # Merge defaults with file-specific data (file-specific takes priority)
            merged_data = defaults | file_data

            # Write tags
            self.write_tags(filepath, merged_data)

            # Generate new filename
            new_filename = self.generate_filename(merged_data)

            # Rename file if needed
            new_path = self.rename_file(filepath, new_filename)

            # Update YAML entry with new filename for future reference
            if new_path and not self.dry_run:
                file_data["filename"] = new_path.name

        # Update YAML file with new filenames
        if not self.dry_run:
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
            self.log(f"Updated {yaml_file} with new filenames")


def main():
    parser = argparse.ArgumentParser(
        description="Manage audio file tags and filenames using mutagen",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate YAML from current directory (dry-run)
  tagger

  # Generate YAML and save it
  tagger --execute

  # Apply tags from YAML (dry-run)
  tagger tagger.yaml

  # Apply tags from YAML and execute
  tagger --execute tagger.yaml
        """,
    )

    parser.add_argument(
        "yaml_file",
        nargs="?",
        help="YAML file with tag information (if not provided, generates YAML from current directory)",
    )

    parser.add_argument(
        "-e",
        "--execute",
        action="store_true",
        help="Execute changes (default is dry-run mode)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="tagger.yaml",
        help="Output YAML file name when generating (default: tagger.yaml)",
    )

    args = parser.parse_args()

    tagger = Tagger(execute=args.execute)

    if args.yaml_file:
        # Apply mode
        tagger.apply_yaml(args.yaml_file)
    else:
        # Generate mode
        tagger.generate_yaml(args.output)


if __name__ == "__main__":
    main()
