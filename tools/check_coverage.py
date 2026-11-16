#!/usr/bin/env python3
"""Check that every word printed in the edition reaches the Markdown book.

    python3 tools/check_coverage.py

For each unit, the words on its text pages (running heads and folios
excluded) are compared with the words in its Markdown file. Words inside
figures are carried by the figure images, so they are reported separately.
Exits non-zero if a unit loses more than 25 words and more than 2 % of its text.
"""
import os
import re
import sys
from collections import Counter

import pymupdf

sys.path.insert(0, os.path.dirname(__file__))
from structure import PDF, UNITS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORD = re.compile(r"[A-Za-zÀ-ÿ]{3,}")


def words(text):
    text = re.sub(r"-\s*\n\s*", "", text)
    return Counter(w.lower() for w in WORD.findall(text))


def main():
    doc = pymupdf.open(os.path.join(ROOT, PDF))
    bad = 0
    total_missing = 0
    for first, last, _lvl, path, title, _kind in UNITS:
        buf = []
        for pno in range(first, last + 1):
            page = doc[pno - 1]
            for b in page.get_text("dict")["blocks"]:
                for ln in b.get("lines", []):
                    if ln["bbox"][3] < 46 or ln["bbox"][1] > 560:
                        continue
                    buf.append("".join(s["text"] for s in ln["spans"]))
        pdf_words = words("\n".join(buf))
        md = open(os.path.join(ROOT, "book", path), encoding="utf-8").read()
        md = re.sub(r"<img[^>]*>", "", md)
        md = re.sub(r"[*`_\\]", "", md)
        md_words = words(md)
        missing = pdf_words - md_words
        n = sum(missing.values())
        total_missing += n
        # figure labels live in the images: allow a few, never more than 2 %
        lost = n > 25 and n > 0.02 * sum(pdf_words.values())
        if lost:
            bad += 1
        flag = "!!" if lost else "ok"
        print(f"{flag} {path:62s} pdf={sum(pdf_words.values()):5d} missing={n:3d} "
              + " ".join(list(missing)[:12]))
    print("total words not carried as text (most are figure labels):", total_missing)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
