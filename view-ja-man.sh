#!/bin/bash
# View Japanese man page in browser
# Usage: view-ja-man.sh

set -e

# Determine man page location
# Try Homebrew location first, then development location
if [ -n "${HOMEBREW_PREFIX}" ] && [ -f "${HOMEBREW_PREFIX}/share/man/ja/man1/tagger.1" ]; then
    MAN_FILE="${HOMEBREW_PREFIX}/share/man/ja/man1/tagger.1"
elif [ -f "$(brew --prefix 2>/dev/null)/share/man/ja/man1/tagger.1" ]; then
    MAN_FILE="$(brew --prefix)/share/man/ja/man1/tagger.1"
elif [ -f "man/ja/tagger.1" ]; then
    MAN_FILE="man/ja/tagger.1"
else
    echo "Error: Japanese man page not found" >&2
    echo "Tried:" >&2
    echo "  - \${HOMEBREW_PREFIX}/share/man/ja/man1/tagger.1" >&2
    echo "  - man/ja/tagger.1 (development)" >&2
    exit 1
fi

HTML_FILE="/tmp/tagger_ja_$(date +%s).html"

# Convert to HTML with better styling
mandoc -T html "$MAN_FILE" | sed '
/<\/head>/i\
  <style>\
    body { max-width: 900px; margin: 40px auto; padding: 0 20px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; }\
    h1, h2 { border-bottom: 1px solid #eee; padding-bottom: 0.3em; }\
    dd { margin-left: 2em; margin-bottom: 1em; }\
    dt { font-weight: bold; margin-top: 1em; }\
  </style>
' > "$HTML_FILE"

# Open in default browser
open "$HTML_FILE"

echo "Japanese man page opened in browser: $HTML_FILE"
