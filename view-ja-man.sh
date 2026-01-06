#!/bin/bash
# View Japanese man page in browser
# Usage: ./view-ja-man.sh

set -e

MAN_FILE="man/ja/tagger.1"
HTML_FILE="/tmp/tagger_ja_$(date +%s).html"

if [ ! -f "$MAN_FILE" ]; then
    echo "Error: $MAN_FILE not found"
    exit 1
fi

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
