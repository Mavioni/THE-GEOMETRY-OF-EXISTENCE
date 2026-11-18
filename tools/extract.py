#!/usr/bin/env python3
"""Cut the edition PDF into the illustrated Markdown book.

    python3 tools/extract.py

Reads   edition/The-Geometry-of-Everything.pdf
Writes  book/**.md           one file per unit listed in tools/book.py
        book/manifest.json   the reading order and each chapter's parts
        art/paintings/       the cover, the six Book plates, the back cover
        art/plates/          the twenty-six chapter plates
        art/figures/         every other figure

Nothing is retyped. The typesetting decides what each line is: its font,
size, colour and position say whether it is a title, a teaching, a label,
a verse, a table cell or a caption. Requires PyMuPDF (pip install pymupdf).
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import statistics
import sys
from dataclasses import dataclass, field

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import book as B  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_DIR = os.path.join(ROOT, "book")
ART_DIR = os.path.join(ROOT, "art")

ACCENTS = {0xA8792B, 0x2F4F95, 0xAD3F2A, 0x2C6B62, 0x674A87}
MUTED = 0x6D6252          # captions and attributions
RUNNING = 0x8A7D68        # running heads, leaders, small numbers
LABEL_INK = {0x2B2620, 0xFBF7EE}   # ink used only inside figures
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
NUMBER_WORDS = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
                "eighteen", "nineteen", "twenty", "twenty-one", "twenty-two", "twenty-three",
                "twenty-four", "twenty-five", "twenty-six"]


# ---------------------------------------------------------------------------
# Reading a page: characters -> pieces -> rows
# ---------------------------------------------------------------------------

def fmt_of(font: str) -> str:
    italic = "Italic" in font or "Itali" in font
    bold = "Bold" in font or "Semi" in font
    return ("b" if bold else "") + ("i" if italic else "")


def family(font: str) -> str:
    if font.startswith("Cormorant"):
        return "CG"
    if font.startswith("EB-Garamond"):
        return "EB"
    if font.startswith("Inter"):
        return "IN"
    if font.startswith("DejaVu"):
        return "DV"
    return font


@dataclass
class Char:
    c: str
    x0: float
    y0: float
    x1: float
    y1: float
    font: str
    size: float
    color: int


@dataclass
class Piece:
    """A run of text on one line, with its formatting."""
    runs: list            # [(text, fmt)]
    x0: float
    y0: float
    x1: float
    y1: float
    font: str             # of the first visible character
    size: float
    color: int
    spaced: bool = False  # letter-spaced capitals
    line: int = 0         # which PDF line it came from
    big: float = 0.0      # the largest character size in the piece

    @property
    def text(self) -> str:
        return "".join(t for t, _ in self.runs)

    @property
    def fam(self) -> str:
        return family(self.font)

    @property
    def accent(self) -> bool:
        return self.color in ACCENTS

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def italic(self) -> bool:
        vis = [(t, f) for t, f in self.runs if t.strip()]
        return bool(vis) and all("i" in f for _, f in vis)


def despace(chars: list[Char]) -> str:
    """Undo letter-spacing: 'C H A P T E R  O N E' -> 'CHAPTER ONE'."""
    glyphs = [c for c in chars if c.c != " "]
    if len(glyphs) < 2:
        return "".join(c.c for c in glyphs)
    gaps = [glyphs[i + 1].x0 - glyphs[i].x1 for i in range(len(glyphs) - 1)]
    letter = statistics.median(gaps)
    word = letter + 0.2 * glyphs[0].size
    out = glyphs[0].c
    for g, nxt in zip(gaps, glyphs[1:]):
        out += (" " if g > word else "") + nxt.c
    return out


def is_spaced(chars: list[Char]) -> bool:
    if family(chars[0].font) not in ("CG", "IN") and chars[0].size > 6:
        return False
    glyphs = [c for c in chars if c.c != " "]
    spaces = len(chars) - len(glyphs)
    if glyphs and glyphs[0].size >= 9 and any(c.c.isdigit() for c in glyphs):
        return False
    return len(glyphs) >= 2 and spaces >= 0.5 * (len(glyphs) - 1) and \
        all(len(w) <= 2 for w in "".join(c.c for c in chars).split())


def style_runs(chars: list[Char]):
    """Split a line's characters into runs of one font, size and colour."""
    runs, cur = [], []
    for ch in chars:
        if cur and ch.c != " " and (ch.font, round(ch.size, 1), ch.color) != \
                (cur[-1].font, round(cur[-1].size, 1), cur[-1].color) and cur[-1].c != " ":
            runs.append(cur)
            cur = []
        elif cur and ch.c != " " and cur[-1].c == " ":
            prev = next((c for c in reversed(cur) if c.c != " "), None)
            if prev and (ch.font, round(ch.size, 1), ch.color) != (prev.font, round(prev.size, 1), prev.color):
                # move trailing spaces into the new run boundary
                runs.append(cur)
                cur = []
        cur.append(ch)
    if cur:
        runs.append(cur)
    return runs


def make_pieces(line_chars: list[Char]) -> list[Piece]:
    """One PDF line -> pieces, split at wide gaps and at label/text boundaries."""
    groups, cur = [], []
    for ch in line_chars:
        if cur and ch.c != " ":
            last = next((c for c in reversed(cur) if c.c != " "), None)
            if last is not None and ch.x0 - last.x1 > 9.0:
                groups.append(cur)
                cur = []
        cur.append(ch)
    if cur:
        groups.append(cur)

    pieces = []
    for g in groups:
        runs = style_runs(g)
        # a letter-spaced label followed by ordinary text becomes two pieces
        segs, seg = [], []
        seg_spaced = seg_digits = False
        for r in runs:
            vis = [c for c in r if c.c != " "]
            if not vis:
                seg.append(r)
                continue
            digits = vis[0].color in ACCENTS and re.fullmatch(r"\d+\.?", "".join(c.c for c in vis))
            sp = vis[0].color in ACCENTS and bool(digits or (family(vis[0].font) == "CG" and is_spaced(r)))
            if seg and sp != seg_spaced:
                prev_vis = [c for rr in seg for c in rr if c.c != " "]
                gap = vis[0].x0 - prev_vis[-1].x1 if prev_vis else 99
                if not digits and not (seg_spaced and seg_digits) and gap <= 5:
                    seg.append(r)        # a run-in label: keep it in the sentence
                    seg_spaced = False
                    continue
                segs.append((seg, seg_spaced))
                seg = []
            seg_spaced = sp
            seg_digits = bool(digits)
            seg.append(r)
        if seg:
            segs.append((seg, seg_spaced if any(c.c != " " for r in seg for c in r) else False))
        for runs_, _ in segs:
            out_runs, all_chars = [], []
            spaced_any = False
            for r in runs_:
                vis = [c for c in r if c.c != " "]
                all_chars += r
                if not vis:
                    out_runs.append((" ", ""))
                    continue
                if is_spaced(r):
                    spaced_any = True
                    lead = " " if r[0].c == " " else ""
                    trail = " " if r[-1].c == " " else ""
                    f = "b" if vis[0].color in ACCENTS else fmt_of(vis[0].font)
                    out_runs.append((lead + despace(r) + trail, f))
                else:
                    out_runs.append(("".join(c.c for c in r), fmt_of(vis[0].font)))
            vis = [c for c in all_chars if c.c != " "]
            if not vis:
                continue
            first = vis[0]
            pieces.append(Piece(out_runs, min(c.x0 for c in vis), min(c.y0 for c in vis),
                                max(c.x1 for c in vis), max(c.y1 for c in vis),
                                first.font, round(first.size, 1), first.color, spaced_any,
                                big=round(max(c.size for c in vis), 1)))
    return pieces


def page_chars_lines(page):
    for b in page.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            chars = []
            for s in ln["spans"]:
                for c in s["chars"]:
                    x0, y0, x1, y1 = c["bbox"]
                    chars.append(Char(c["c"], x0, y0, x1, y1, s["font"], s["size"], s["color"]))
            if any(c.c.strip() for c in chars):
                yield chars


# ---------------------------------------------------------------------------
# Figures: clusters of vector drawing
# ---------------------------------------------------------------------------

def figure_regions(page) -> list[pymupdf.Rect]:
    pw, ph = page.rect.width, page.rect.height
    rects = []
    for d in page.get_drawings():
        r = d["rect"]
        if r.width > pw - 10 and r.height > ph - 20:
            continue                    # the page background
        rects.append(pymupdf.Rect(r))
    big = [r for r in rects if r.width > 40 or r.height > 40]
    if big:                             # the small ornament set above a plate
        top = min(r.y0 for r in big)
        rects = [r for r in rects if not (r.width < 24 and r.height < 8 and r.y1 < top - 2)]
    rects.sort(key=lambda r: r.y0)
    clusters = []
    for r in rects:
        if clusters and r.y0 <= clusters[-1].y1 + 14:
            clusters[-1] |= r
        else:
            clusters.append(pymupdf.Rect(r))
    return [c for c in clusters if c.width > 40 and c.height > 30]


def is_label_style(p: Piece) -> bool:
    return p.size < 7.0 or p.color in LABEL_INK


def is_caption_style(p: Piece) -> bool:
    return p.fam == "EB" and p.italic and p.size <= 8.6 and p.color == MUTED


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def esc(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = re.sub(r"([*_`\[\]])", r"\\\1", text)
    return text.replace("<", "&lt;")


def join_runs(a: list, b: list) -> list:
    """Join two lines of runs, as the reader would read them."""
    if not a:
        return list(b)
    if not b:
        return a
    tail = a[-1][0]
    if re.search(r"\w-$", tail.rstrip()) or tail.endswith((" ", "—")) or b[0][0].startswith(" "):
        a = a[:-1] + [(tail.rstrip() if re.search(r"\w-$", tail.rstrip()) else tail, a[-1][1])]
        return a + list(b)
    return a + [(" ", a[-1][1] if a[-1][1] == b[0][1] else "")] + list(b)


def md(runs: list, invert_italic: bool = False) -> str:
    """Runs -> Markdown with *italic* and **bold**."""
    merged = []
    for t, f in runs:
        if invert_italic:
            f = f.replace("i", "") if "i" in f else f + "i"
        if not t:
            continue
        if not t.strip():
            if merged:
                merged[-1][0] += t
            else:
                merged.append([t, ""])
            continue
        if merged and merged[-1][1] == f:
            merged[-1][0] += t
        else:
            merged.append([t, f])
    out = []
    for t, f in merged:
        lead = t[:len(t) - len(t.lstrip())]
        trail = t[len(t.rstrip()):]
        core = re.sub(r"\s+", " ", t.strip())
        if not core:
            out.append(" ")
            continue
        wrap = {"": "", "i": "*", "b": "**", "bi": "***"}[f]
        out.append(lead + wrap + esc(core) + wrap + trail)
    s = re.sub(r"\s+", " ", "".join(out)).strip()
    s = re.sub(r"\s*\x01\s*", "<br>", s)
    s = re.sub(r"“\s+", "“", s)
    s = re.sub(r"\*\*\*\*", "", s)
    return s


def plain(runs: list) -> str:
    s = re.sub(r"\s+", " ", "".join(t for t, _ in runs).replace("\x01", " ")).strip()
    return re.sub(r"“\s+", "“", s)


def smart_title(text: str) -> str:
    if text.upper() != text:
        return text
    small = {"of", "and", "the", "a", "for", "in", "to", "with", "on"}
    words = text.lower().split()
    return " ".join(w if (i and w in small) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def rel(src: str, dst: str) -> str:
    return os.path.relpath(dst, os.path.dirname(src)).replace(os.sep, "/")


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------

@dataclass
class Block:
    kind: str
    data: dict = field(default_factory=dict)


class Builder:
    """Turns rows into blocks: paragraphs, lists, tables, verse, figures."""

    def __init__(self, unit, out_path, manifest_unit):
        self.unit = unit
        self.path = out_path
        self.mu = manifest_unit
        self.blocks: list[Block] = []
        self.section = None         # current chapter movement
        self.titles = 0
        self.last_row_bottom = None
        self.last_row_top = None
        self.prev_line_full = False
        self.last_row_right = None
        self.page_margin = 43.2
        self.para_open = False
        self.figure_count = 0

    # -- helpers --------------------------------------------------------
    @property
    def last(self) -> Block | None:
        return self.blocks[-1] if self.blocks else None

    def add(self, kind, **data):
        self.close_para()
        self.blocks.append(Block(kind, data))
        return self.blocks[-1]

    def close_para(self):
        self.para_open = False

    def rx(self, x):
        return x - self.page_margin

    # -- rows -----------------------------------------------------------
    def row(self, pieces: list[Piece], page_no: int, first_on_page: bool):
        pieces = sorted(pieces, key=lambda p: p.x0)
        # merge pieces that sit close together into one
        merged = [pieces[0]]
        for p in pieces[1:]:
            q = merged[-1]
            same_label = (p.spaced or q.spaced) and p.fam == q.fam == "CG" and \
                (p.font, p.size, p.color) == (q.font, q.size, q.color) and p.x0 - q.x1 < 30 and \
                not (header_style(p) and p.x0 - q.x1 > 5)
            if same_label or (p.x0 - q.x1 <= 9.0 and p.line == q.line and not (p.spaced and p.accent) and
                              not (q.accent and q.fam == "CG" and not p.accent)):
                q.runs = q.runs + ([(" ", "")] if p.x0 - q.x1 > 1.2 else []) + p.runs
                q.x1 = max(q.x1, p.x1)
                q.y0 = min(q.y0, p.y0)
                q.y1 = max(q.y1, p.y1)
            else:
                merged.append(p)
        pieces = merged
        first = pieces[0]
        text = " ".join(plain(p.runs) for p in pieces)
        top = min(p.y0 for p in pieces)
        # gap: distance from the top of the previous row to the top of this one
        gap = None if first_on_page or self.last_row_top is None else top - self.last_row_top
        self._row(pieces, first, text, gap, page_no, first_on_page)
        self.last_row_top = top
        self.last_row_bottom = max(p.y1 for p in pieces)
        self.last_row_right = max(p.x1 for p in pieces)
        self.last_row_size = first.size

    def _row(self, pieces, first, text, gap, page_no, first_on_page):
        kind = self.unit["kind"]
        texty = [p for p in pieces if not (p.fam == "DV" and len(p.text.strip()) == 1)]
        lead = texty[0] if texty else first

        # titles ------------------------------------------------------
        if first.fam == "CG" and first.size >= 18 and not first.accent:
            if self.last and self.last.kind == "title" and gap is not None and gap < 40:
                self.last.data["raw"] += " " + text
                self.last.data["text"] = smart_title(self.last.data["raw"])
                return
            t = smart_title(text)
            self.titles += 1
            self.add("title", text=t, raw=text, level=1 if self.titles == 1 else 2)
            return
        # kicker (CHAPTER ONE, BOOK ONE, THE SUMMIT) ------------------
        if len(pieces) == 1 and first.spaced and first.fam == "CG" and first.size >= 7.7 and \
                first.color in ACCENTS | {0xCFB98B} and not self.blocks_have_title():
            self.add("kicker", text=text)
            return
        # subtitle under a chapter title ------------------------------
        if self.last and self.last.kind == "title" and first.fam == "EB" and first.italic and \
                first.color == MUTED and first.size >= 9.0 and kind in ("chapter", "front") and \
                self.titles == 1 and kind == "chapter":
            self.add("subtitle", text=text)
            return
        # chapter movement heading: "IV ● The Tale" ---------------------
        m = re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX)\s+(.*)$", text)
        if kind == "chapter" and m and first.accent and first.fam == "CG" and \
                first.text.strip().replace(" ", "") in ROMAN and len(pieces) >= 2:
            mark = "".join(re.findall(r"[◆●◇]", text))
            name = re.sub(r"[◆●◇]", "", m.group(2)).strip()
            self.section = name
            self.add("movement", roman=m.group(1), mark=mark, name=name)
            return
        # sub-headings --------------------------------------------------
        if first.fam == "CG" and first.size >= 13.4 and not first.italic and not first.accent:
            self.section = text
            self.add("h2", runs=self.all_runs(pieces))
            return
        if first.fam == "CG" and first.size >= 12.9 and first.italic:
            self.add("h3", runs=self.all_runs(pieces))
            return
        if first.fam == "CG" and 10.9 <= first.size <= 11.6 and not first.accent:
            self.add("h3", runs=self.all_runs(pieces))
            return
        if self.last and self.last.kind == "h3" and first.italic and first.color == MUTED and \
                abs(self.rx(first.x0)) < 2 and gap is not None and gap < 18:
            self.last.data["runs"] = join_runs(self.last.data["runs"], first.runs)
            return
        # mark labels: "◇ ANALOGY", "LIMITS" ------------------------------
        if len(pieces) == 1 and first.accent and first.size < 8 and \
                all("b" in f or t.strip() in "◆●◇" for t, f in first.runs if t.strip()) and \
                (first.spaced or re.fullmatch(r"[◆●◇] [A-Z ,]+", text)):
            self.add("label", text=text)
            return
        # the creed question on a chapter opener ------------------------
        if any(p.color == 0x4A4237 for p in pieces):
            q = [p for p in pieces if p.color == 0x4A4237]
            if self.last and self.last.kind == "creed" and not first.spaced:
                self.last.data["runs"] = join_runs(self.last.data["runs"], sum((p.runs for p in q), []))
            else:
                word = plain(first.runs) if first.spaced else ""
                self.add("creed", word=word, runs=sum((p.runs for p in q), []))
            return
        # captions ----------------------------------------------------
        if is_caption_style(lead) and lead.size <= 8.6 and not (self.last and self.last.kind == "witness"):
            if self.last and self.last.kind in ("figure", "caption") and \
                    (gap is None or gap < 16 or
                     (self.last.kind == "figure" and not self.last.data.get("caption"))):
                if self.last.kind == "figure":
                    self.last.data["caption"] = join_runs(self.last.data.get("caption") or [], self.all_runs(pieces))
                else:
                    self.last.data["runs"] = join_runs(self.last.data["runs"], self.all_runs(pieces))
                return
            self.add("caption", runs=self.all_runs(pieces))
            return
        # attribution under a quotation -------------------------------
        if first.fam == "CG" and first.color == MUTED and 8.0 <= first.size <= 8.6 and \
                self.last and self.last.kind == "quote":
            q = self.last.data
            q["attrib"] = join_runs(q.get("attrib") or [], self.all_runs(pieces))
            return
        # verse --------------------------------------------------------
        verse_here = (self.section == "The Song") or self.unit["file"].endswith("law-of-the-sophont.md")
        if verse_here and lead.fam == "EB" and lead.italic:
            if self.last and self.last.kind == "verse" and gap is not None and gap < lead.size * 1.75:
                self.last.data["stanzas"][-1].append((self.rx(lead.x0) > 6, lead.runs))
            elif self.last and self.last.kind == "verse":
                self.last.data["stanzas"].append([(self.rx(lead.x0) > 6, lead.runs)])
            else:
                self.add("verse", stanzas=[[(False, lead.runs)]])
            return
        # quotations: centred italic lines -----------------------------
        centred = self.is_centred(pieces)
        if lead.fam == "EB" and lead.italic and lead.size >= 10.5 and centred and lead.color != MUTED:
            if self.last and self.last.kind == "quote" and not self.last.data.get("attrib") and \
                    gap is not None and gap < lead.size * 1.75:
                prev = plain(self.last.data["runs"])
                nxt = plain(self.all_runs(pieces))
                if prev[-1:].isalpha() and nxt[:1].isupper():
                    self.last.data["runs"] = self.last.data["runs"] + [("\x01", "")] + self.all_runs(pieces)
                else:
                    self.last.data["runs"] = join_runs(self.last.data["runs"], self.all_runs(pieces))
            else:
                self.add("quote", runs=self.all_runs(pieces), attrib=None,
                         lead=(self.unit["kind"] == "opener"))
            return
        # witnesses ----------------------------------------------------
        if self.section == "The Witnesses" and (first.text.startswith("★") or
                                                ("b" in lead.runs[0][1] and lead.size >= 9.9)):
            star = first.text.startswith("★") or any(p.text.strip() == "★" for p in pieces)
            runs = self.all_runs([p for p in pieces if p.text.strip() != "★"])
            runs = [(t.replace("★", ""), f) for t, f in runs]
            name = [r for r in runs if "b" in r[1]]
            source = runs[len(name):] if runs[:len(name)] == name else [r for r in runs if "b" not in r[1]]
            self.add("witness", star=star, name=plain(name), source=source, desc=[])
            return
        if self.last and self.last.kind == "witness" and lead.fam == "EB" and lead.size < 10 and not lead.accent:
            self.last.data["desc"] = join_runs(self.last.data["desc"], self.all_runs(pieces))
            return
        # bullets -------------------------------------------------------
        if first.text.lstrip().startswith("•") and first.text.strip() != "•":
            runs = list(first.runs)
            runs[0] = (runs[0][0].lstrip()[1:].lstrip(), runs[0][1])
            if not runs[0][0]:
                runs = runs[1:]
            first = Piece(runs, first.x0 + 6, first.y0, first.x1, first.y1, first.font,
                          first.size, first.color)
            pieces = [Piece([("•", "")], first.x0 - 6, first.y0, first.x0 - 3, first.y1,
                            first.font, first.size, first.color), first] + pieces[1:]
            first = pieces[0]
        if first.text.strip() == "•":
            rest = pieces[1:]
            if rest:
                item = self.all_runs(rest)
                xtext = self.rx(rest[0].x0)
            else:
                item, xtext = [], self.rx(first.x1) + 4
            if self.last and self.last.kind == "list" and self.last.data["ordered"] is False:
                self.last.data["items"].append(item)
            else:
                self.add("list", ordered=False, items=[item], start=1, xtext=xtext)
            self.last.data["xtext"] = xtext
            return
        # numbered items: teachings, predictions, the monthly cycle -----
        num = re.fullmatch(r"(\d{1,3})\.?", first.text.strip())
        if num and first.accent and len(pieces) >= 2 and self.rx(first.x0) < 40:
            n = int(num.group(1))
            item = self.all_runs(pieces[1:])
            xtext = self.rx(pieces[1].x0)
            if self.last and self.last.kind == "list" and self.last.data["ordered"]:
                self.last.data["items"].append(item)
                self.last.data["numbers"].append(n)
            else:
                self.add("list", ordered=True, items=[item], numbers=[n], xtext=xtext)
            self.last.data["xtext"] = xtext
            return
        # continuation of a list item -----------------------------------
        if self.last and self.last.kind == "list" and len(pieces) == 1 and \
                abs(self.rx(first.x0) - self.last.data["xtext"]) < 3 and \
                (gap is None or gap < first.size * 1.62):
            items = self.last.data["items"]
            items[-1] = join_runs(items[-1], first.runs)
            return
        # tables --------------------------------------------------------
        if self.table_row(pieces, gap, first_on_page):
            return
        # the Reversal, set as a ruled callout ---------------------------
        if self.section == "The Reversal" and kind == "chapter":
            self.paragraph(pieces, gap, "callout", first_on_page)
            return
        # everything else: running text ---------------------------------
        cls = "centred" if (centred and lead.italic) else ("italic" if lead.italic and lead.size >= 10.9 else "body")
        if lead.color == MUTED and lead.italic:
            cls = "note"
        self.paragraph(pieces, gap, cls, first_on_page)

    def blocks_have_title(self):
        # a kicker comes before the title on its page
        return bool(self.last) and self.last.kind == "title"

    def is_centred(self, pieces):
        x0 = min(p.x0 for p in pieces)
        x1 = max(p.x1 for p in pieces)
        mid = self.page_margin + 147
        return x0 - self.page_margin > 8 and abs((x0 + x1) / 2 - mid) < 14

    def all_runs(self, pieces):
        runs = []
        for p in pieces:
            runs = runs + ([(" ", "")] if runs else []) + p.runs
        return runs

    def paragraph(self, pieces, gap, cls, first_on_page):
        runs = self.all_runs(pieces)
        lead = max(pieces, key=lambda p: p.big or p.size)
        label_start = pieces[0].accent and pieces[0].spaced
        if self.para_open and not label_start and self.last and self.last.kind == "para" and self.last.data["cls"] == cls:
            cont = False
            if first_on_page:
                cont = self.prev_line_full
            elif gap is not None and gap < (lead.big or lead.size) * 1.62:
                cont = True
            if cont:
                self.last.data["runs"] = join_runs(self.last.data["runs"], runs)
                self.track_fullness(pieces)
                return
        self.add("para", cls=cls, runs=runs)
        self.para_open = True
        self.track_fullness(pieces)

    def track_fullness(self, pieces):
        x1 = max(p.x1 for p in pieces)
        self.prev_line_full = (x1 - self.page_margin) > 294 * 0.86

    # -- tables -----------------------------------------------------------
    def table_row(self, pieces, gap, first_on_page) -> bool:
        tab = self.last if (self.last and self.last.kind == "table") else None
        if all(header_style(p) for p in pieces):
            if tab is None or tab.data["mode"] is not None:
                tab = self.add("table", rows=[], header=None, mode=None)
            if tab.data["mode"] is None:
                tab.data["header"] = (tab.data["header"] or []) + [pieces]
                return True
        wide = len(pieces) >= 2
        if not wide:
            if tab and (gap is None or gap < first_size(pieces) * 1.5) and tab.data["rows"]:
                tab.data["rows"][-1].append(pieces)       # a continuation line
                return True
            return False
        has_accent = any(p.accent for p in pieces)
        header_like = all(p.fam == "CG" and p.size < 8 and not p.accent and p.text.upper() == p.text
                          for p in pieces)
        if tab is None or (gap is not None and gap > 44 and not first_on_page):
            tab = self.add("table", rows=[], header=None, mode=None)
        d = tab.data
        if d["mode"] is None and header_like:
            if d["header"] is None:
                d["header"] = [pieces]
            else:
                d["header"].append(pieces)
            return True
        if d["mode"] is None:
            d["mode"] = "accent" if has_accent else "plain"
        if d["mode"] == "accent" and not has_accent and d["rows"]:
            d["rows"][-1].append(pieces)
        else:
            d["rows"].append([pieces])
        return True


def header_style(p) -> bool:
    return p.fam == "CG" and p.size < 8 and not p.accent and p.text.upper() == p.text and \
        any(ch.isalpha() for ch in p.text)


def first_size(pieces):
    return pieces[0].size


def finish_table(block: Block, margin_of) -> dict:
    """Group a table's pieces into columns and cells."""
    rows = block.data["rows"]
    header = block.data["header"]
    every = [p for r in rows for line in r for p in line] + \
            ([p for line in header for p in line] if header else [])
    xs = sorted(margin_of(p) for p in every)
    cols = []
    for x in xs:
        if cols and x - cols[-1][-1] < 9:
            cols[-1].append(x)
        else:
            cols.append([x])
    starts = [min(c) for c in cols]

    def col_of(p):
        x = margin_of(p)
        best = 0
        for i, s in enumerate(starts):
            if x >= s - 4:
                best = i
        return best

    def cells(lines):
        out = [[] for _ in starts]
        for line in lines:
            for p in line:
                i = col_of(p)
                out[i] = join_runs(out[i], p.runs)
        return out

    body = [cells(r) for r in rows]
    head = cells(header) if header else None
    # merge neighbouring columns that never both hold text (right-aligned numbers)
    i = 0
    while i + 1 < len(starts) and body:
        both = any(r[i] and r[i + 1] for r in body) or (head and head[i] and head[i + 1])
        if not both:
            for r in body + ([head] if head else []):
                r[i] = r[i] or r[i + 1]
                del r[i + 1]
            del starts[i + 1]
        else:
            i += 1
    # drop columns that are empty everywhere
    keep = [i for i in range(len(starts)) if any(r[i] for r in body) or (head and head[i])]
    body = [[r[i] for i in keep] for r in body]
    head = [head[i] for i in keep] if head else None
    return dict(head=head, body=body)


# ---------------------------------------------------------------------------
# Rendering blocks to Markdown
# ---------------------------------------------------------------------------

def render(blocks: list[Block], unit, out_path, margin_of, nav) -> str:
    lines = []
    w = lines.append
    for b in blocks:
        d = b.data
        k = b.kind
        if k == "kicker":
            w(f"<sub>{d['text']}</sub>\n")
        elif k == "title":
            w(("# " if d["level"] == 1 else "## ") + esc(d["text"]) + "\n")
        elif k == "subtitle":
            w(f"*{esc(d['text'])}*\n")
        elif k == "movement":
            mark = f" {d['mark']}" if d["mark"] else ""
            w(f"## {d['roman']} ·{mark} {esc(d['name'])}\n")
        elif k == "h2":
            w("## " + md(d["runs"]) + "\n")
        elif k == "h3":
            w("### " + md(d["runs"]).replace("*", "") + "\n" if False else "### " + md(d["runs"]) + "\n")
        elif k == "label":
            w(f"**{esc(d['text'])}**\n")
        elif k == "creed":
            word = d["word"].upper()
            w(f"> **{word}** · *{md(d['runs']).strip('*')}*\n")
        elif k == "quote":
            body = md(d["runs"])
            if body.startswith("*") and body.endswith("*") and not body.startswith("**"):
                body = body[1:-1]
            if d.get("lead"):
                w(f"*{body}*\n")
                continue
            w(f"> *{body}*")
            if d.get("attrib"):
                w(">\n> — " + md(d["attrib"]))
            w("")
        elif k == "verse":
            out = []
            for st in d["stanzas"]:
                ls = []
                for indent, runs in st:
                    t = md(runs)
                    t = t if t.startswith("*") else f"*{t}*"
                    ls.append(("&emsp;" if indent and unit["file"].endswith("sophont.md") else "") + t)
                out.append("<br>\n".join(ls))
            w("\n\n".join(out) + "\n")
        elif k == "witness":
            star = "★ " if d["star"] else ""
            src = md(d["source"], invert_italic=True)
            w(f"- {star}**{esc(d['name'])}** · {src}  \n  {md(d['desc'])}")
            if not (blocks.index(b) + 1 < len(blocks) and blocks[blocks.index(b) + 1].kind == "witness"):
                w("")
        elif k == "list":
            for i, item in enumerate(d["items"]):
                body = item[0][0][1:] if item and item[0][0].startswith("\x00") else md(item)
                if d["ordered"]:
                    w(f"{d['numbers'][i]}. {body}")
                else:
                    w(f"- {body}")
            w("")
        elif k == "table":
            t = finish_table(b, margin_of)
            if not t["body"] and t["head"] and len(t["head"]) == 1:
                w(f"**{md(t['head'][0])}**\n")
                continue
            if not t["body"] and t["head"]:
                t["body"] = [[[] for _ in t["head"]] for _ in range(6)]   # blank rows to write in
            if not t["head"] and len(t["body"]) > 1 and not t["body"][0][0] and t["body"][1][0]:
                t["head"], t["body"] = t["body"][0], t["body"][1:]
            n = max(len(r) for r in t["body"]) if t["body"] else len(t["head"])
            head = t["head"] or [[] for _ in range(n)]

            def cell(runs):
                return md(runs).replace("|", "\\|")
            linkify = nav.get("linkify")
            w("| " + " | ".join(cell(c) for c in head) + " |")
            w("|" + "---|" * n)
            for r in t["body"]:
                cs = [cell(c) for c in r]
                if linkify:
                    cs = [linkify(c) for c in cs]
                w("| " + " | ".join(cs) + " |")
            w("")
        elif k == "figure":
            src = rel(out_path, d["path"])
            alt = plain(d.get("caption") or []) or d.get("alt") or f"A figure from {unit['title']}"

            width = d.get("width", 420)
            w(f'<p align="center"><img src="{src}" alt="{alt.replace(chr(34), "&quot;")}" width="{width}"></p>\n')
            if d.get("caption"):
                w(f'<p align="center"><sub><i>{md(d["caption"]).replace("*", "")}</i></sub></p>\n')
        elif k == "caption":
            w(f'<p align="center"><sub><i>{md(d["runs"]).replace("*", "")}</i></sub></p>\n')
        elif k == "para":
            text = md(d["runs"])
            text = re.sub(r"^(\d+)\. ", r"\1\\. ", text)
            if d["cls"] == "callout":
                w("> " + text + "\n")
            elif d["cls"] in ("centred", "italic", "note"):
                t = text if text.startswith("*") else f"*{text}*"
                w((f'<p align="center"><i>{text.replace("*", "")}</i></p>\n') if d["cls"] == "centred" else t + "\n")
            else:
                w(text + "\n")
        elif k == "ornament":
            w('<p align="center">❧</p>\n')
    if not any(b.kind == "title" for b in blocks):
        lines.insert(0, f"# {esc(unit['title'])}\n")
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


# ---------------------------------------------------------------------------
# The whole book
# ---------------------------------------------------------------------------

def read_page(page):
    """One page -> (rows, hidden). Rows are ("row", [pieces]) or ("fig", (rect, labels));
    hidden are the labels inside figures, which the images carry."""
    regions = figure_regions(page)
    pieces = []
    for line_no, chars in enumerate(page_chars_lines(page)):
        for p in make_pieces(chars):
            p.line = line_no
            if p.y1 < 46 and p.color == RUNNING:
                continue                    # running head
            if p.y0 > 565 and p.fam == "CG" and p.color == MUTED:
                continue                    # page number
            if p.color == RUNNING and p.text.strip() in (".", ""):
                continue                    # leader dots
            if p.text.strip() == "❧":
                continue                    # ornament
            pieces.append(p)
    # drop the text that lives inside a figure; a region whose text is
    # body-sized (a magic square, a table) is not a figure but text
    figs = []
    for r in regions:
        inside = [p for p in pieces if r.contains(pymupdf.Point((p.x0 + p.x1) / 2, p.cy))
                  and not is_caption_style(p)]
        if any(not is_label_style(p) for p in inside):
            continue
        for p in pieces:
            if is_label_style(p) and not is_caption_style(p):
                grown = pymupdf.Rect(r.x0 - 30, r.y0 - 14, r.x1 + 30, r.y1 + 14)
                if grown.contains(pymupdf.Point((p.x0 + p.x1) / 2, p.cy)):
                    r |= pymupdf.Rect(p.x0, p.y0, p.x1, p.y1)
        inside = [p for p in pieces if r.contains(pymupdf.Point((p.x0 + p.x1) / 2, p.cy))
                  and not is_caption_style(p)]
        figs.append((r, inside))
    hidden = {id(p) for _, inside in figs for p in inside}
    pieces = [p for p in pieces if id(p) not in hidden]

    # a mark glyph set just before a letter-spaced label belongs to it
    for g in [p for p in pieces if p.text.strip() in ("◆", "●", "◇") and p.size < 8]:
        labels = [L for L in pieces if L is not g and L.spaced and L.accent and
                  -1 <= L.x0 - g.x1 <= 15 and abs(L.cy - g.cy) < 8]
        if labels:
            L = labels[0]
            L.runs = [(g.text.strip() + " ", "")] + L.runs
            L.x0 = g.x0
            pieces.remove(g)

    # drop caps: prepend the letter to the line beside it
    for dc in [p for p in pieces if p.fam == "CG" and p.size >= 30 and p.color == 0x231F1A
               and len(p.text.strip()) == 1]:
        pieces.remove(dc)
        cands = [p for p in pieces if p.x0 > dc.x1 - 2 and p.y0 >= dc.y0 - 8 and p.fam == "EB"]
        if cands:
            tgt = min(cands, key=lambda p: (p.y0, p.x0))
            tgt.runs = [(dc.text.strip(), "")] + tgt.runs
            tgt.x0 = dc.x0

    # figures enter the flow at their top edge
    items = [("text", p.cy, p) for p in pieces]
    for r, inside in figs:
        items.append(("fig", r.y0 + 1, (r, inside)))
    items.sort(key=lambda it: it[1])

    rows, cur, cur_y = [], [], None
    for kind, y, obj in items:
        if kind == "fig":
            if cur:
                rows.append(("row", cur))
                cur, cur_y = [], None
            rows.append(("fig", obj))
            continue
        if cur and abs(y - cur_y) > 3.6:
            rows.append(("row", cur))
            cur = []
        if not cur:
            cur_y = y
        cur.append(obj)
    if cur:
        rows.append(("row", cur))

    hidden_pieces = [p for _, inside in figs for p in inside]
    return rows, hidden_pieces


def unit_dict(u):
    first, last, part, file, title, kind = u
    return dict(first=first, last=last, part=part, file=file, title=title, kind=kind,
                path=f"book/{B.PARTS[part]['dir']}/{file}")


def render_clip(page, rect, path, zoom=3.0):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=rect, alpha=False)
    from PIL import Image
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    img.save(path, optimize=True)


def render_painting(page, path, dpi=144):
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    from PIL import Image
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img.save(path, quality=86, optimize=True, progressive=True)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    doc = pymupdf.open(os.path.join(ROOT, B.PDF))
    for d in ("book", "art/paintings", "art/plates", "art/figures"):
        full = os.path.join(ROOT, d)
        if os.path.isdir(full) and d != "book":
            shutil.rmtree(full)
    for part in B.PARTS:
        full = os.path.join(BOOK_DIR, part["dir"])
        if os.path.isdir(full):
            shutil.rmtree(full)
        os.makedirs(full, exist_ok=True)
    for d in ("paintings", "plates", "figures"):
        os.makedirs(os.path.join(ART_DIR, d), exist_ok=True)

    # the paintings: cover, Book plates, back cover
    paintings = {}
    for n in B.PAINTED_PAGES:
        if n == 1:
            name = "cover"
        elif n == doc.page_count:
            name = "back-cover"
        else:
            part = next(p for p in B.PARTS if p["plate"] == n)
            name = part["dir"]
        path = f"art/paintings/{name}.jpg"
        render_painting(doc[n - 1], os.path.join(ROOT, path))
        words = " ".join(plain(p.runs) for chars in page_chars_lines(doc[n - 1]) for p in make_pieces(chars))
        paintings[n] = dict(path=path, words=re.sub(r"\s+", " ", words).strip())

    units = [unit_dict(u) for u in B.UNITS]
    chapter_no = 0
    manifest_units = []
    for u in units:
        if u["kind"] == "chapter":
            chapter_no += 1
            u["number"] = chapter_no
    titles_by_number = {u["number"]: u for u in units if u.get("number")}

    for u in units:
        out_path = os.path.join(ROOT, u["path"])
        mu = dict(path=u["path"], title=u["title"], kind=u["kind"], part=u["part"],
                  pages=[u["first"], u["last"]])
        if u.get("number"):
            mu["number"] = u["number"]
        bld = Builder(u, out_path, mu)
        margins = {}

        if u["kind"] == "opener":
            pt = paintings[B.PARTS[u["part"]]["plate"]]
            bld.add("figure", path=os.path.join(ROOT, pt["path"]), caption=None,
                    alt=pt["words"], width=300)
        for n in range(u["first"], u["last"] + 1):
            if n in B.SKIPPED_PAGES:
                continue
            page = doc[n - 1]
            margin = 59.0 if n % 2 else 43.2
            bld.page_margin = margin
            if n in B.PAINTED_PAGES:
                pt = paintings[n]
                bld.add("figure", path=os.path.join(ROOT, pt["path"]), caption=None,
                        alt=pt["words"], width=300)
                continue
            rows, _ = read_page(page)
            first_on_page = True
            for kind, obj in rows:
                if kind == "fig":
                    r, inside = obj
                    pad = 4
                    clip = pymupdf.Rect(r.x0 - pad, r.y0 - pad, r.x1 + pad, r.y1 + pad) & page.rect
                    if u["kind"] == "chapter" and n == u["first"] and "plate" not in mu:
                        name = f"art/plates/{u['file'][:-3]}.png"
                        mu["plate"] = name
                        width = 360
                    else:
                        bld.figure_count += 1
                        stem = u["file"][:-3].split("-", 1)[1] if u["file"][0].isdigit() else u["file"][:-3]
                        name = f"art/figures/{B.PARTS[u['part']]['dir'][0]}-{stem}" + \
                               (f"-{bld.figure_count}" if bld.figure_count > 1 or u["file"].startswith("01-the-geometry") else "") + ".png"
                        width = min(480, int(clip.width * 1.5))
                    render_clip(page, clip, os.path.join(ROOT, name))
                    bld.add("figure", path=os.path.join(ROOT, name), caption=None,
                            alt="", width=width)
                    bld.last_row_bottom = r.y1
                    continue
                for p in obj:
                    margins[id(p)] = margin
                bld.row(obj, n, first_on_page)
                first_on_page = False

        def margin_of(p, _m=margins):
            return p.x0 - _m.get(id(p), 43.2)

        nav = {}
        if u["file"].startswith("04-index-of-situations"):
            nav["linkify"] = lambda c, _u=u: link_chapters(c, _u, titles_by_number, units)
        if u["kind"] == "opener":
            link_opener_list(bld.blocks, u, units)
        if u["file"].startswith("02-the-monthly"):
            link_monthly(bld.blocks, u, units)
        collect_chapter(bld.blocks, mu, margin_of)
        mu["figures"] = [dict(path=os.path.relpath(b.data["path"], ROOT).replace(os.sep, "/"),
                              caption=plain(b.data.get("caption") or []))
                         for b in bld.blocks if b.kind == "figure" and "/paintings/" not in b.data["path"]]
        if u["kind"] == "opener":
            intro = next((b for b in bld.blocks if b.kind == "quote"), None)
            mu["intro"] = plain(intro.data["runs"]) if intro else ""
        if u["kind"] in ("section", "front"):
            mu["kicker"] = B.PARTS[u["part"]]["name"]
        text = render(bld.blocks, u, out_path, margin_of, nav)
        text += navigation(u, units)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        mu["words"] = len(re.findall(r"\w+", text))
        manifest_units.append(mu)
        print(f"  {u['path']:<60} pp. {u['first']}-{u['last']}")

    manifest = dict(title=B.TITLE, subtitle=B.SUBTITLE, author=B.AUTHOR, edition=B.EDITION,
                    pdf=B.PDF, pages=doc.page_count,
                    paintings={str(k): v for k, v in paintings.items()},
                    parts=B.PARTS, units=manifest_units)
    with open(os.path.join(BOOK_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print(f"wrote {len(manifest_units)} files to book/")


# ---------------------------------------------------------------------------
# Links and navigation
# ---------------------------------------------------------------------------

def link_chapters(cell: str, unit, by_number, units) -> str:
    def rep(m):
        n = int(m.group(0))
        tgt = by_number.get(n)
        if not tgt:
            return m.group(0)
        return f"[{n}]({rel(unit['path'], tgt['path'])})"
    if re.fullmatch(r"[\d, A-Za-z]+", cell) and re.search(r"\d", cell):
        out = re.sub(r"\b\d{1,2}\b", rep, cell)
        km = next(x for x in units if x["title"] == "The Kept Middle")
        return out.replace("The Kept Middle", f"[The Kept Middle]({rel(unit['path'], km['path'])})")
    return cell


def link_opener_list(blocks, unit, units):
    for b in blocks:
        if b.kind == "list" and b.data["ordered"]:
            new = []
            for item in b.data["items"]:
                title = plain(item)
                tgt = next((x for x in units if x["title"] == title and x["kind"] == "chapter"), None)
                new.append([(f"\x00[{title}]({rel(unit['path'], tgt['path'])})", "")] if tgt else item)
            b.data["items"] = new


def link_monthly(blocks, unit, units):
    for b in blocks:
        if b.kind == "list" and b.data["ordered"]:
            new = []
            for item in b.data["items"]:
                text = plain(item)
                parts = []
                for piece in text.split(" · "):
                    name = re.sub(r"^\d+ · ", "", piece)
                    name2 = {"The Rivers": "The Rivers That Became This Book",
                             "The Summit: The Geometry": "The Geometry of Everything"}.get(name, name)
                    tgt = next((x for x in units if x["title"] == name2), None)
                    parts.append(f"[{piece}]({rel(unit['path'], tgt['path'])})" if tgt else piece)
                new.append([("\x00" + " · ".join(parts), "")])
            b.data["items"] = new


def navigation(u, units) -> str:
    i = units.index(u)
    prev_u = units[i - 1] if i else None
    next_u = units[i + 1] if i + 1 < len(units) else None
    bits = []
    if prev_u:
        bits.append(f"[← {prev_u['title']}]({rel(u['path'], prev_u['path'])})")
    bits.append(f"[Contents]({rel(u['path'], 'book/README.md')})")
    if next_u:
        bits.append(f"[{next_u['title']} →]({rel(u['path'], next_u['path'])})")
    return "\n---\n\n<p align=\"center\">" + " &nbsp;·&nbsp; ".join(bits) + "</p>\n"


def collect_chapter(blocks, mu, margin_of):
    """Record each chapter's parts in the manifest, for the workbook and the site."""
    if mu["kind"] != "chapter":
        return
    section = None
    mu["movements"] = []
    for b in blocks:
        k, d = b.kind, b.data
        if k == "kicker":
            mu["kicker"] = d["text"]
        elif k == "subtitle":
            mu["subtitle"] = d["text"]
        elif k == "figure" and "plate" in d["path"]:
            mu["plate_caption"] = plain(d.get("caption") or [])
        elif k == "quote" and section is None:
            mu["epigraph"] = dict(text=plain(d["runs"]), source=plain(d.get("attrib") or []))
        elif k == "creed":
            mu["creed"] = dict(word=d["word"].title(), question=plain(d["runs"]))
        elif k == "movement":
            section = d["name"]
            mu["movements"].append(dict(roman=d["roman"], mark=d["mark"], name=d["name"]))
        elif k == "list" and section == "The Teaching":
            mu["teachings"] = [d["numbers"][0], d["numbers"][-1]]
            mu["teaching_count"] = len(d["numbers"])
        elif k == "table" and section in ("The Practice", "The Ledger", "The Five Scales"):
            t = finish_table(b, margin_of)
            mu[section.split()[-1].lower()] = [[plain(r[0]), plain(r[-1])] for r in t["body"]]
        elif k == "para" and section == "The Reversal":
            mu["reversal"] = plain(d["runs"])
        elif k == "verse" and section == "The Song":
            mu["song"] = [plain(runs) for st in d["stanzas"] for _, runs in st]
        elif k == "h3" and section == "The Tale":
            mu["tale"] = plain(d["runs"])


if __name__ == "__main__":
    main()
