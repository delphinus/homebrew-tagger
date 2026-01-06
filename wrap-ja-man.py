#!/usr/bin/env python3
"""
Wrap Japanese man page text with proper line breaking.
Usage: mandoc -T utf8 man/ja/tagger.1 | ./wrap-ja-man.py [width]
"""

import sys
import os
import unicodedata
import re


def get_display_width(text):
    """Get the display width of text considering fullwidth characters."""
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2  # Fullwidth characters
        else:
            width += 1  # Halfwidth characters
    return width


def wrap_line(line, max_width, indent=''):
    """Wrap a line to max_width, handling Japanese text properly."""
    if not line.strip():
        return [line]

    # Characters that should not appear at line start (kinsoku shori)
    line_start_forbidden = '、。，．・：；？！゛゜´｀¨＾￣＿ヽヾゝゞ〃仝々〆〇ー—‐〜～）〕］｝」』】'
    # Characters that should not appear at line end
    line_end_forbidden = '（〔［｛「『【'

    # Preserve leading whitespace
    leading_space = len(line) - len(line.lstrip())
    prefix = line[:leading_space]
    text = line[leading_space:]

    if get_display_width(prefix + text) <= max_width:
        return [line]

    wrapped_lines = []
    current_line = prefix
    current_width = get_display_width(prefix)

    i = 0
    while i < len(text):
        char = text[i]
        char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1

        # Check if adding this character would exceed the width
        if current_width + char_width > max_width and current_line.strip():
            # Check if next character is forbidden at line start
            # If so, try to include it in current line (overflow is acceptable for kinsoku)
            if i < len(text) and text[i] in line_start_forbidden:
                current_line += char
                current_width += char_width
                i += 1
                continue

            # Check if current last character is forbidden at line end
            if current_line and current_line[-1] in line_end_forbidden:
                # Move it to next line
                last_char = current_line[-1]
                current_line = current_line[:-1]
                wrapped_lines.append(current_line)
                current_line = indent + last_char
                current_width = get_display_width(indent) + (2 if unicodedata.east_asian_width(last_char) in ('F', 'W') else 1)
            else:
                wrapped_lines.append(current_line)
                current_line = indent
                current_width = get_display_width(indent)

        current_line += char
        current_width += char_width
        i += 1

    if current_line.strip():
        wrapped_lines.append(current_line)

    return wrapped_lines


def process_man_page(input_stream, max_width):
    """Process man page with proper Japanese line wrapping."""
    for line in input_stream:
        line = line.rstrip('\n')

        # Detect indentation level for continuation lines
        leading_space = len(line) - len(line.lstrip())
        indent = ' ' * leading_space

        wrapped = wrap_line(line, max_width, indent)
        for wrapped_line in wrapped:
            print(wrapped_line)


def main():
    # Get width from argument or environment variable
    if len(sys.argv) > 1:
        try:
            width = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid width '{sys.argv[1]}'", file=sys.stderr)
            sys.exit(1)
    else:
        width = int(os.environ.get('MANWIDTH', os.environ.get('COLUMNS', 80)))

    process_man_page(sys.stdin, width)


if __name__ == '__main__':
    main()
