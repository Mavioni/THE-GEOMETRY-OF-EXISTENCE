#!/usr/bin/env python3
"""Confirm that every printed word of the edition reaches the Markdown book.

    python3 tools/check_coverage.py

For each file in book/, every word on its pages in the PDF must appear in
the file, as often as it is printed. Not counted: running heads, page
numbers, the labels inside figures (the images carry them), and the pages
tools/book.py lists as skipped. Exits non-zero if anything is missing.
Requires PyMuPDF.
"""
from __future__ import annotations

import html
import os
import re
import sys
from collections import Counter

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import book as B          # noqa: E402
import extract as X       # noqa: E402

ROOT = X.ROOT


def words(text: str) -> Counter:
    text = text.replace("’", "'").replace("‘", "'").lower()
    return Counter(re.findall(r"[^\W_]+(?:'[^\W_]+)*", text))


def markdown_words(path: str) -> Counter:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    alts = " ".join(re.findall(r'alt="([^"]*)"', text))
    text = re.sub(r"<[^>]+>", " ", text)            # HTML tags
    text = re.sub(r"\]\([^)]*\)", "] ", text)       # link targets
    text = text.replace("*", "").replace("\\", "")    # emphasis and escapes
    return words(html.unescape(text + " " + alts))


def main() -> int:
    doc = pymupdf.open(os.path.join(ROOT, B.PDF))
    missing_total = 0
    printed_total = 0
    for u in B.UNITS:
        first, last, part, file, title, kind = u
        path = os.path.join(ROOT, "book", B.PARTS[part]["dir"], file)
        printed = Counter()
        for n in range(first, last + 1):
            if n in B.SKIPPED_PAGES:
                continue
            page = doc[n - 1]
            if n in B.PAINTED_PAGES:
                printed += words(" ".join(X.plain(p.runs) for chars in X.page_chars_lines(page)
                                          for p in X.make_pieces(chars)))
                continue
            rows, _hidden = X.read_page(page)
            for kind_, obj in rows:
                if kind_ == "row":
                    printed += words(" ".join(X.plain(p.runs) for p in obj))
        have = markdown_words(path)
        missing = printed - have
        printed_total += sum(printed.values())
        if missing:
            missing_total += sum(missing.values())
            print(f"MISSING in {os.path.relpath(path, ROOT)}: {dict(missing)}")
    print(f"{printed_total} printed words checked; {missing_total} missing.")
    return 1 if missing_total else 0


if __name__ == "__main__":
    sys.exit(main())
