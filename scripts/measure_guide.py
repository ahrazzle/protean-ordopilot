#!/usr/bin/env python3
"""Count words and sentences in docs/guide.md, reproducibly.

Method (fixed, deterministic, standard library only):

1. Read the file as UTF-8 text.
2. Remove fenced code blocks (lines between ``` markers).
3. Remove table separator rows (rows made only of |, -, :, and spaces).
4. Strip line-leading markers: heading hashes (#), blockquote arrows (>),
   list dashes (-, *, +), and ordered-list numbers ("1.").
5. Strip table pipes (|) and inline backticks (`) from the remaining text.
6. Words are regex tokens matching [A-Za-z0-9']+ .
7. Sentences are the non-empty spans left after splitting the stripped text
   on [.!?]+ ; a span counts only if it holds at least one word token.

Usage: python3 scripts/measure_guide.py [path]   (default: docs/guide.md)

Run this script instead of quoting a number from memory. Any published count
for the guide must name this method.
"""
import re
import sys

WORD = re.compile(r"[A-Za-z0-9']+")
SENTENCE_SPLIT = re.compile(r"[.!?]+")
LIST_MARKER = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
SEPARATOR_ROW = re.compile(r"^\s*\|?[\s:\-|]+\|?\s*$")


def strip_markers(text):
    lines = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if SEPARATOR_ROW.match(line):
            continue
        line = re.sub(r"^\s*#+\s*", "", line)      # heading hashes
        line = re.sub(r"^\s*>\s?", "", line)       # blockquote arrow
        line = LIST_MARKER.sub("", line)           # list markers
        line = line.replace("|", " ")              # table pipes
        line = line.replace("`", "")               # inline code ticks
        lines.append(line)
    return "\n".join(lines)


def count(text):
    stripped = strip_markers(text)
    words = WORD.findall(stripped)
    sentences = 0
    for span in SENTENCE_SPLIT.split(stripped):
        if WORD.search(span):
            sentences += 1
    return len(words), sentences


def main(argv):
    path = argv[1] if len(argv) > 1 else "docs/guide.md"
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    words, sentences = count(text)
    if sentences == 0:
        print("words=%d sentences=0 wps=n/a" % words)
        return 0
    print("method=scripts/measure_guide.py file=%s words=%d sentences=%d "
          "wps=%.2f" % (path, words, sentences, words / sentences))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
