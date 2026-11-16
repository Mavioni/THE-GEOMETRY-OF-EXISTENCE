#!/usr/bin/env python3
"""Cut the edition PDF into the illustrated Markdown book.

    python3 tools/extract_book.py

Reads  edition/The_Geometry_of_Existence_A_Manual_for_Life.pdf
Writes book/**.md          one file per unit in tools/structure.py
       book/manifest.json  the reading order, used by build_site.py
       art/plates/*.png    every full-page plate (cover, levels, parts, chapters)
       art/plates/thumbs/  the same plates at gallery size
       art/figures/*.png   every in-text figure, medallion and diagram

The conversion reads the typesetting itself: fonts, sizes, colours and
positions decide what is a heading, a mark, a practice, an audit, a table
or a figure. Nothing in the text is retyped by hand. Requires PyMuPDF.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field

import pymupdf

sys.path.insert(0, os.path.dirname(__file__))
from structure import CHAPTER_NUMBERS, LEVELS, PDF, UNITS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book")
ART = os.path.join(ROOT, "art")

GOLD_TAG = 0x8C6A1E
MUTED = 0x8C879A
CAPTION = 0x4A4560
BODY_LEFT = 46.0
BODY_RIGHT = 350.0

MARK_WORDS = ("LIVED", "ARGUED", "DEMONSTRATED", "MEASURED", "ON RECORD",
              "SOURCE-REPORTED", "CORRECTION", "KNOWLEDGEABLE")

# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------


def despace(text: str) -> str:
    """'T H E    S T A N C E' -> 'THE STANCE' (undo letter-spacing)."""
    t = text.strip()
    if re.fullmatch(r"(?:\S(?: |$))+(?:\s{2,}(?:\S(?: |$))+)*\s*", t + " ") or \
            re.fullmatch(r"(\S ){2,}\S", t):
        words = re.split(r"\s{2,}", t)
        return " ".join(w.replace(" ", "") for w in words)
    return t


def is_spaced(text: str) -> bool:
    t = text.strip()
    return bool(re.fullmatch(r"\S( {1,4}\S)+", t)) and len(t) > 4 and \
        all(len(w) == 1 for w in t.split())


def respace_words(text: str) -> str:
    """Letter-spaced text whose word gaps were lost: best effort."""
    t = text.strip()
    if re.search(r"\s{2,}", t):
        return " ".join(w.replace(" ", "") for w in re.split(r"\s{2,}", t))
    return t


SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or",
         "the", "to", "with"}


def title_case(text: str) -> str:
    out = []
    for i, w in enumerate(text.lower().split()):
        if i and w in SMALL:
            out.append(w)
        elif w in ("i", "ii", "iii", "iv", "v"):
            out.append(w.upper())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48] or "x"


def md_escape(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = re.sub(r"([*_`])", r"\\\1", text)
    text = text.replace("<", "&lt;")
    return text


def rel(from_file: str, to_path: str) -> str:
    return os.path.relpath(to_path, os.path.dirname(from_file)).replace(os.sep, "/")


# --------------------------------------------------------------------------
# page model
# --------------------------------------------------------------------------


@dataclass
class Span:
    text: str
    font: str
    size: float
    color: int
    bbox: tuple
    origin: tuple

    @property
    def italic(self):
        return "Italic" in self.font or self.font.endswith("LightI")

    @property
    def bold(self):
        return "SemiBold" in self.font or "SemiBo" in self.font

    @property
    def is_tag(self):
        return self.bold and self.size < 7.6 and self.color == GOLD_TAG


@dataclass
class Line:
    spans: list
    bbox: tuple
    kind: str = "body"
    marker: str | None = None
    chars: list = field(default_factory=list)

    @property
    def text(self):
        return "".join(s.text for s in self.spans)

    @property
    def x0(self):
        return self.bbox[0]

    @property
    def y0(self):
        return self.bbox[1]

    @property
    def x1(self):
        return self.bbox[2]

    @property
    def y1(self):
        return self.bbox[3]

    @property
    def first(self) -> Span:
        for s in self.spans:
            if s.text.strip() and "DejaVu" not in s.font and s.font != "Helvetica":
                return s
        return self.spans[0]

    @property
    def size(self):
        return round(self.first.size, 1)


@dataclass
class Item:
    y: float
    kind: str               # line | figure | table | ornament | checkitem
    line: Line | None = None
    data: dict = field(default_factory=dict)


def page_is_plate(page) -> bool:
    for dr in page.get_drawings()[:3]:
        f = dr.get("fill")
        if f and dr["rect"].width > 390 and dr["rect"].height > 600 and sum(f) < 1.0:
            return True
    return False


def page_lines(page) -> list[Line]:
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            spans, chars = [], []
            for s in ln["spans"]:
                text = "".join(c["c"] for c in s["chars"])
                if not text:
                    continue
                spans.append(Span(text, s["font"], s["size"], s["color"], tuple(s["bbox"]),
                                  tuple(s["origin"])))
                chars.extend((c["c"], c["bbox"][0], c["bbox"][2]) for c in s["chars"])
            if not spans or not "".join(x.text for x in spans).strip():
                continue
            out.append(Line(spans, tuple(ln["bbox"]), chars=chars))
    return merge_split_lines(out)


def baseline(ln: "Line") -> float:
    big = max(s.size for s in ln.spans)
    ys = Counter()
    for s in ln.spans:
        if s.size >= big * 0.9:
            ys[round(s.origin[1], 1)] += len(s.text)
    return ys.most_common(1)[0][0]


def merge_split_lines(lines: list) -> list:
    """Rejoin one printed line that the PDF stored as pieces (inline maths)."""
    lines = sorted(lines, key=lambda l: (baseline(l), l.x0))
    out = []
    for ln in lines:
        if out:
            prev = out[-1]
            if abs(baseline(prev) - baseline(ln)) < 1.0 and -2 <= ln.x0 - prev.x1 < 3 and \
                    abs(max(s.size for s in prev.spans) - max(s.size for s in ln.spans)) < 1.0:
                prev.spans.extend(ln.spans)
                prev.chars.extend(ln.chars)
                prev.bbox = _union(prev.bbox, ln.bbox)
                continue
        out.append(ln)
    return out


def spaced_text(ln: "Line") -> str:
    """Read letter-spaced type by its geometry: big gaps are word breaks."""
    nz = [c for c in ln.chars if c[0] != " "]
    if len(nz) < 3:
        return ln.text.strip()
    gaps = [nz[i + 1][1] - nz[i][2] for i in range(len(nz) - 1)]
    med = sorted(gaps)[len(gaps) // 2]
    out = nz[0][0]
    for g, c in zip(gaps, nz[1:]):
        if g > med * 1.7 and g > med + 1.2:
            out += " "
        out += c[0]
    return out


def line_is_spaced(ln: "Line") -> bool:
    nz = [c for c in ln.chars if c[0] != " "]
    if len(nz) < 4:
        return False
    gaps = sorted(nz[i + 1][1] - nz[i][2] for i in range(len(nz) - 1))
    return gaps[len(gaps) // 4] > 1.2 * 1 and is_spaced(ln.text.replace("   ", " ").replace("  ", " "))


def is_running_head(ln: Line) -> bool:
    return ln.y1 < 46 and ln.size < 7


def is_folio(ln: Line) -> bool:
    return ln.y0 > 560 and re.fullmatch(r"[\d ]+", ln.text.strip() or "x") is not None


# --------------------------------------------------------------------------
# drawings: figures, tables, ornaments
# --------------------------------------------------------------------------


def _union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _touch(a, b, pad):
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1])


def analyse_drawings(page):
    """Return (figure boxes, table rules, ornaments, callout bars)."""
    rects, thin = [], []
    gold_rules, light_rules = [], []
    for dr in page.get_drawings():
        r = dr["rect"]
        box = (r.x0, r.y0, r.x1, r.y1)
        if r.width > 390 and r.height > 600:
            continue                                   # page background
        col = dr.get("color")
        if r.height < 1.2 and r.x0 <= 47 and r.x1 >= 349 and col:
            if abs(col[0] - 0.788) < 0.02 and (dr.get("width") or 0) > 0.6:
                gold_rules.append(r.y0)
                continue
            if abs(col[0] - 0.812) < 0.02 and (dr.get("width") or 0) < 0.4:
                light_rules.append(r.y0)
                continue
        if r.width < 2.5 or r.height < 2.5:
            thin.append(box)
        else:
            rects.append(box)
    # cluster the solid drawings
    clusters = []
    for b in rects:
        merged = [c for c in clusters if _touch(c, b, 8)]
        for c in merged:
            clusters.remove(c)
            b = _union(b, c)
        clusters.append(b)
    changed = True
    while changed:
        changed = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                if _touch(clusters[i], clusters[j], 8):
                    clusters[i] = _union(clusters[i], clusters[j])
                    del clusters[j]
                    changed = True
                    break
            if changed:
                break
    figures, ornaments = [], []
    for c in clusters:
        w, h = c[2] - c[0], c[3] - c[1]
        if w < 16 and h < 16:
            ornaments.append(c)
            continue
        # let thin strokes (axes, ticks, rules) that touch the figure join it
        for t in thin:
            if _touch(c, t, 3) and (t[2] - t[0]) < 320:
                c = _union(c, t)
        figures.append(c)
    # thin-only figures (axes drawn only with lines) — rare; ignored as rules
    return figures, sorted(gold_rules), sorted(light_rules), ornaments


# --------------------------------------------------------------------------
# inline runs
# --------------------------------------------------------------------------


def line_runs(ln: Line, base_size: float):
    """Turn a line's spans into (text, style) runs."""
    runs = []
    # baseline: the most common origin y among body-size spans
    ys = Counter(round(s.origin[1], 1) for s in ln.spans if s.size >= base_size * 0.9)
    base_y = ys.most_common(1)[0][0] if ys else ln.spans[0].origin[1]
    for s in ln.spans:
        t = s.text
        if s.font == "Helvetica" and t.strip() in ("·", "•"):
            continue
        if "DejaVu" in s.font and t.strip() in ("▲", "◆", "\x00", "■", "□"):
            continue
        t = t.replace("\x00", "")
        if s.is_tag:
            style = "tag"
        elif s.size < base_size * 0.86 and "DejaVu" not in s.font and t.strip():
            dy = s.origin[1] - base_y
            style = "sub" if dy > 0.6 else ("sup" if dy < -0.6 else "")
            if not style:
                style = "i" if s.italic else ""
        elif s.bold and s.italic:
            style = "bi"
        elif s.bold:
            style = "b"
        elif s.italic:
            style = "i"
        else:
            style = ""
        runs.append([t, style])
    return runs


VOCAB: Counter = Counter()


def join_runs(acc: list, nxt: list):
    """Append the runs of the next line, undoing end-of-line hyphenation."""
    if not acc:
        acc.extend([r[:] for r in nxt])
        return
    if not nxt:
        return
    last = acc[-1]
    first = nxt[0]
    m = re.search(r"([A-Za-zÀ-ÿ]+)-$", last[0])
    n = re.match(r"([a-zà-ÿ][A-Za-zà-ÿ]*)", first[0])
    if m and n:
        joined = (m.group(1) + n.group(1)).lower()
        hyph = (m.group(1) + "-" + n.group(1)).lower()
        if VOCAB[hyph] > VOCAB[joined]:
            pass                     # a real compound: keep the hyphen
        else:
            last[0] = last[0][:-1]
        acc.extend([r[:] for r in nxt])
        return
    if last[1] == "tag" and first[1] == "tag" and last[0].endswith("-"):
        last[0] = last[0][:-1]
        acc.extend([r[:] for r in nxt])
        return
    if (last[0].endswith(("-", "/")) or (last[0].endswith("—") and not last[0].endswith(" —"))) \
            and not last[0].endswith(" -"):
        acc.extend([r[:] for r in nxt])
        return
    if last[0] and not last[0].endswith(" "):
        if first[1] == last[1]:
            last[0] += " "
        else:
            acc.append([" ", ""])
    acc.extend([r[:] for r in nxt])


def render_runs(runs) -> str:
    merged = []
    for t, st in runs:
        if merged and merged[-1][1] == st:
            merged[-1][0] += t
        else:
            merged.append([t, st])
    out = []
    for t, st in merged:
        if st in ("", None):
            out.append(md_escape(t))
            continue
        lead = t[: len(t) - len(t.lstrip())]
        trail = t[len(t.rstrip()):]
        core = t.strip()
        if not core:
            out.append(t)
            continue
        if st == "tag":
            out.append(f"{lead}`{core}`{trail}")
        elif st == "sub":
            out.append(f"{lead}<sub>{md_escape(core)}</sub>{trail}")
        elif st == "sup":
            out.append(f"{lead}<sup>{md_escape(core)}</sup>{trail}")
        elif st == "i":
            out.append(f"{lead}*{md_escape(core)}*{trail}")
        elif st == "b":
            out.append(f"{lead}**{md_escape(core)}**{trail}")
        elif st == "bi":
            out.append(f"{lead}***{md_escape(core)}***{trail}")
    s = "".join(out)
    s = re.sub(r"\*\*\*\*", "", s)            # adjoining bold runs
    s = re.sub(r"(?<!\*)\*\*(?!\*)", "**", s)
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s


# --------------------------------------------------------------------------
# line classification
# --------------------------------------------------------------------------


def classify(ln: Line) -> str:
    f = ln.first
    t = ln.text.strip()
    if "DejaVu" in ln.spans[0].font:
        s0 = ln.spans[0].text
        if "▲" in s0:
            return "practice"
        if "◆" in s0:
            return "audit"
        if "\x00" in s0 or "■" in s0:
            return "check"
    if f.font == "Helvetica" and t in ("·", "•"):
        return "bullet"
    if t in ("·", "•"):
        return "bullet"
    if re.fullmatch(r"\d{1,2}", t) and (f.color in (GOLD_TAG, 0xC9A14A) or "Cormorant" in f.font):
        return "numeral"
    if "Cormorant" in f.font:
        if f.bold and f.size >= 14:
            return "h3"
        if not f.italic and f.size >= 14.5:
            return "h2"
        if not f.italic and f.size >= 11.8 and is_spaced(t.replace("   ", " ")):
            return "h2"
        if f.italic and f.size >= 13.5:
            return "epigraph"
        if f.italic and f.size >= 12.5 and re.match(r"\d+\.\d+", t):
            return "h4"
        if f.italic:
            return "subtitle"
    if f.font.startswith("EBGaramond-Medium") and line_is_spaced(ln):
        return "kicker"
    if line_is_spaced(ln) and f.color == MUTED:
        return "muted"
    if f.color == CAPTION and f.italic:
        return "caption"
    if f.color == MUTED:
        return "muted"
    return "body"


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------


def extract_table(lines: list[Line], gold_y: float, rules: list[float]):
    """Lines of size ~7.3 around a gold header rule form a table."""
    tl = [ln for ln in lines if 7.0 <= ln.size <= 7.6 and gold_y - 30 < ln.y0]
    head = [ln for ln in tl if ln.y1 <= gold_y + 1]
    body = [ln for ln in tl if ln.y0 > gold_y]
    # rows end where the vertical rhythm breaks
    rows_bounds = [gold_y] + [r for r in rules if r > gold_y]
    last = rows_bounds[-1]
    tail = [ln for ln in body if ln.y0 > last]
    end = last
    for ln in sorted(tail, key=lambda l: l.y0):
        if ln.y0 - end < 16:
            end = ln.y1
    body = [ln for ln in body if ln.y0 <= end]
    used = head + body
    head_spans = sorted([s for ln in head for s in ln.spans if s.text.strip()],
                        key=lambda s: s.bbox[0])
    cols = []
    for s in head_spans:
        if not cols or s.bbox[0] - cols[-1] > 12:
            cols.append(s.bbox[0])

    def col_of(x):
        idx = 0
        for i, c in enumerate(cols):
            if x >= c - 3:
                idx = i
        return idx

    def cells_for(lines_):
        cells = [[] for _ in cols]
        for ln in sorted(lines_, key=lambda l: (round(l.y0), l.x0)):
            for s in ln.spans:
                if not s.text.strip():
                    continue
                cells[col_of(s.bbox[0])].append(s.text.strip())
        out = []
        for c in cells:
            txt = ""
            for piece in c:
                if txt.endswith("-") and piece[:1].islower():
                    txt = txt[:-1] + piece
                elif txt:
                    txt += " " + piece
                else:
                    txt = piece
            out.append(txt.replace("|", "\\|"))
        return out

    header = cells_for(head)
    bounds = rows_bounds + [end + 0.5]
    rows = []
    for a, b in zip(bounds, bounds[1:]):
        rl = [ln for ln in body if a < (ln.y0 + ln.y1) / 2 < b]
        if rl:
            rows.append(cells_for(rl))
    top = min(ln.y0 for ln in head) if head else gold_y - 12
    return dict(header=header, rows=rows, top=top, bottom=end), used


# --------------------------------------------------------------------------
# page -> items
# --------------------------------------------------------------------------


def render_clip(page, box, path, zoom=4.0):
    pad = 4
    clip = pymupdf.Rect(box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad) & page.rect
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
    pix.save(path)


def is_blocking(ln: Line) -> bool:
    """Lines that belong to the running text and therefore bound a figure."""
    k = classify(ln)
    if k in ("practice", "audit", "check", "caption", "h2", "h3", "h4", "kicker",
             "epigraph", "subtitle", "bullet"):
        return True
    if k == "numeral":
        return False
    t = ln.text.strip()
    if ln.size >= 9.5:
        if len(t) <= 3 and abs(ln.size - 10.6) > 0.3:
            return False
        if "DejaVu" in ln.first.font:
            return False
        return True
    return False


def page_figures(page, lines, used):
    """Group the page's drawings into figures, bounded by the running text."""
    blocking = [ln for ln in lines if id(ln) in used or is_blocking(ln)]
    draws = []
    for dr in page.get_drawings():
        r = dr["rect"]
        if r.width > 390 and r.height > 600:
            continue
        col = dr.get("color")
        if r.height < 1.2 and r.x0 <= 47 and r.x1 >= 349 and col and \
                (abs(col[0] - 0.788) < 0.02 or abs(col[0] - 0.812) < 0.02):
            continue                                   # table rules
        box = (r.x0, r.y0, r.x1, r.y1)
        # decoration that runs alongside text (callout bars, label rules)
        if any(b.y0 - 1 < box[3] and box[1] < b.y1 + 1 for b in blocking):
            # unless it is a clipped background that merely reaches the text
            if not (r.width > 40 and r.height > 40):
                continue
        draws.append(box)
    if not draws:
        return []
    draws.sort(key=lambda b: b[1])
    bands = []
    for b in draws:
        if bands:
            cur = bands[-1]
            lo, hi = min(cur[1], b[1]), max(cur[3], b[3])
            between = [l for l in blocking if cur[3] <= l.y0 and l.y1 <= b[1]]
            if not between and b[1] <= cur[3] + 60:
                bands[-1] = _union(cur, b)
                continue
        bands.append(b)
    out = []
    for band in bands:
        box = list(band)
        # cut clipped backgrounds at the running text
        for ln in blocking:
            if _touch(tuple(box), ln.bbox, 0):
                mid = (box[1] + box[3]) / 2
                if (ln.y0 + ln.y1) / 2 > mid:
                    box[3] = min(box[3], ln.y0 - 3)
                else:
                    box[1] = max(box[1], ln.y1 + 3)
        box = tuple(box)
        if box[3] - box[1] < 2:
            continue
        labels = []
        for ln in lines:
            if id(ln) in used or ln in blocking:
                continue
            cy = (ln.y0 + ln.y1) / 2
            if box[1] - 22 <= cy <= box[3] + 22:
                sep = [l for l in blocking if (box[3] <= l.y0 and l.y1 <= ln.y0) or
                       (ln.y1 <= l.y0 and l.y1 <= box[1])]
                if not sep:
                    labels.append(ln)
        for ln in labels:
            box = _union(box, ln.bbox)
        w, h = box[2] - box[0], box[3] - box[1]
        kind = "ornament" if (h < 20 and not labels) else "figure"
        out.append((kind, box, labels))
    return out


def page_items(page, pno: int, figs_out: list):
    lines = [ln for ln in page_lines(page) if not is_running_head(ln) and not is_folio(ln)]
    _, gold, light, _ = analyse_drawings(page)
    items: list[Item] = []
    used = set()

    for gy in gold:
        tab, tl = extract_table(lines, gy, [r for r in light if r > gy])
        for ln in tl:
            used.add(id(ln))
        items.append(Item(tab["top"], "table", data=tab))

    cap_lines = [ln for ln in lines if classify(ln) == "caption"]
    k = 0
    for kind, box, labels in page_figures(page, lines, used):
        if kind == "ornament":
            orn = os.path.join(ART, "ornaments", "divider.png")
            if not os.path.exists(orn):
                os.makedirs(os.path.dirname(orn), exist_ok=True)
                render_clip(page, box, orn)
            items.append(Item(box[1], "ornament"))
            continue
        for ln in labels:
            used.add(id(ln))
        caption = []
        for ln in sorted(cap_lines, key=lambda l: l.y0):
            if id(ln) in used:
                continue
            prev_bottom = caption[-1].y1 if caption else box[3]
            if -2 <= ln.y0 - prev_bottom < 16:
                caption.append(ln)
                used.add(id(ln))
        k += 1
        name = f"p{pno:03d}-{k}.png"
        render_clip(page, box, os.path.join(ART, "figures", name))
        figs_out.append(dict(page=pno, file=f"figures/{name}",
                             caption=" ".join(l.text.strip() for l in caption)))
        items.append(Item(box[1], "figure", data=dict(
            file=name, box=box, w=box[2] - box[0], h=box[3] - box[1],
            caption=caption)))

    for ln in lines:
        if id(ln) in used:
            continue
        ln.kind = classify(ln)
        items.append(Item(ln.y0, "line", line=ln))

    items.sort(key=lambda it: (round(it.y, 1), it.line.x0 if it.line else 0))
    # attach numerals and bullets to the line on their row
    markers = [it for it in items if it.kind == "line" and it.line.kind in ("numeral", "bullet")]
    rest = [it for it in items if it not in markers]
    for m in markers:
        ml = m.line
        cy = (ml.y0 + ml.y1) / 2
        cands = [it for it in rest if it.kind == "line" and it.line.x0 > ml.x1 and
                 it.line.y0 - 3 <= cy <= it.line.y1 + 3 and not it.line.marker]
        if not cands:
            cands = [it for it in rest if it.kind == "line" and it.line.y0 > ml.y0 and not it.line.marker][:1]
        if cands:
            tgt = min(cands, key=lambda it: abs((it.line.y0 + it.line.y1) / 2 - cy))
            num = ml.text.strip()
            tgt.line.marker = (str(int(num)) + ".") if ml.kind == "numeral" else "-"
    return rest


# --------------------------------------------------------------------------
# plates
# --------------------------------------------------------------------------


def plate_info(page):
    info = dict(kicker="", title=[], epigraph=[], other=[])
    for ln in page_lines(page):
        f = ln.first
        t = ln.text.strip()
        if f.font.startswith("EBGaramond-Medium") and is_spaced(t):
            info["kicker"] = info["kicker"] or title_case(spaced_text(ln))
        elif "Cormorant" in f.font and not f.italic and f.size >= 19:
            info["title"].append(spaced_text(ln) if line_is_spaced(ln) else t)
        elif "Cormorant" in f.font and f.italic and f.size >= 11:
            if len(t) > 2:
                info["epigraph"].append(t)
        else:
            info["other"].append(t)
    title = " ".join(info["title"])
    if title.isupper():
        title = title_case(title)
    info["title"] = title
    info["epigraph"] = " ".join(info["epigraph"])
    return info


def save_plate(page, pno: int, name: str):
    os.makedirs(os.path.join(ART, "plates", "thumbs"), exist_ok=True)
    fn = f"p{pno:03d}-{name}.png"
    page.get_pixmap(dpi=144).save(os.path.join(ART, "plates", fn))
    page.get_pixmap(dpi=40).save(os.path.join(ART, "plates", "thumbs", fn))
    return fn


# --------------------------------------------------------------------------
# unit -> markdown
# --------------------------------------------------------------------------


class Writer:
    def __init__(self, md_path):
        self.md_path = md_path
        self.blocks: list[str] = []
        self.para: list | None = None
        self.para_kind = None           # body | callout | item
        self.para_prefix = ""
        self.last_line: Line | None = None
        self.callout = None             # "practice" | "audit" | None
        self.pending_kicker = ""

    # -- paragraphs -------------------------------------------------------
    def flush(self):
        if self.para:
            text = render_runs(self.para)
            if text:
                if self.para_kind == "item":
                    text = self.para_prefix + " " + text.replace("\n", "\n   ")
                if self.callout:
                    text = "> " + text.replace("\n", "\n> ")
                self.blocks.append(text)
        self.para = None
        self.para_kind = None
        self.last_line = None

    def add_block(self, text: str):
        self.flush()
        if self.callout and not text.startswith(">"):
            self.close_callout()
        self.blocks.append(text)

    def close_callout(self):
        self.flush()
        self.callout = None

    def body_line(self, ln: Line, new_page: bool):
        base = ln.size
        runs = line_runs(ln, base)
        prev = self.last_line
        new_para = True
        if self.para is not None and prev is not None and not ln.marker:
            gap = baseline(ln) - baseline(prev)
            pitch = max(prev.size, ln.size) * 1.62
            if new_page:
                new_para = not (prev.x1 > BODY_RIGHT - 8 and abs(ln.x0 - prev.x0) < 20
                                and abs(prev.size - ln.size) < 0.5)
                if prev.text.rstrip().endswith((".", ":", "?", "!")) and ln.spans[0].bold:
                    new_para = True
            elif gap <= pitch * 1.12 and gap > 0:
                new_para = False
            # a size change inside a list item is a soft break, not a new item
            if self.para_kind == "item" and 0 < gap <= pitch * 1.25 and ln.x0 >= prev.x0 - 2 - 30:
                if abs(prev.size - ln.size) >= 0.4:
                    self.para.append(["\n", ""])
                    self.para.extend([r[:] for r in runs])
                    self.last_line = ln
                    return
                new_para = False if (gap <= pitch * 1.12 or new_page) and not new_para is True else new_para
        if self.callout and ln.x0 < 52 and not ln.marker:
            self.close_callout()
        if new_para:
            self.flush()
            self.para = []
            if ln.marker:
                self.para_kind = "item"
                self.para_prefix = ln.marker
            else:
                self.para_kind = "body"
        if self.para and self.para[-1][0] == "\n":
            self.para.extend([r[:] for r in runs])
        else:
            join_runs(self.para, runs)
        self.last_line = ln

    def text(self) -> str:
        self.flush()
        out = "\n\n".join(b for b in self.blocks if b.strip())
        out = re.sub(r"\n{3,}", "\n\n", out)
        return out.strip() + "\n"


def write_unit(doc, unit, prev_unit, next_unit, figures_index, plates_index):
    first, last, level, path, title, kind = unit
    md_path = os.path.join(BOOK, path)
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    w = Writer(md_path)
    art_rel = lambda p: rel(md_path, os.path.join(ART, p))  # noqa: E731
    base = os.path.splitext(os.path.basename(path))[0]
    if base == "README":
        base = os.path.basename(os.path.dirname(path))
    unit_meta = dict(path=path, title=title, kind=kind, level=level, first=first,
                     last=last, plates=[], epigraph="", kicker="")

    for pno in range(first, last + 1):
        page = doc[pno - 1]
        if page_is_plate(page):
            info = plate_info(page)
            name = slug(info["title"] or title)
            fn = save_plate(page, pno, name)
            plates_index.append(dict(page=pno, file=f"plates/{fn}", kicker=info["kicker"],
                                     title=info["title"], epigraph=info["epigraph"],
                                     unit=path))
            unit_meta["plates"].append(f"plates/{fn}")
            unit_meta["epigraph"] = unit_meta["epigraph"] or info["epigraph"]
            unit_meta["kicker"] = unit_meta["kicker"] or info["kicker"]
            alt = " — ".join(x for x in (info["kicker"], info["title"]) if x)
            w.add_block(f'<p align="center">\n  <img src="{art_rel("plates/" + fn)}" '
                        f'alt="{alt}" width="440">\n</p>')
            if info["kicker"]:
                w.add_block(f'<p align="center"><sub>{info["kicker"].upper()}</sub></p>')
            heading = info["title"] or title
            w.add_block(f"# {heading}")
            if info["epigraph"]:
                w.add_block(f"> *{md_escape(info['epigraph'])}*")
            for extra in info["other"]:
                if len(extra) > 3:
                    w.add_block(f'<p align="center"><sub><i>{md_escape(extra)}</i></sub></p>')
            continue

        items = page_items(page, pno, figures_index)
        new_page = True
        for it in items:
            if it.kind == "figure":
                d = it.data
                width = int(min(560, max(170, d["w"] * 1.6)))
                cap = " ".join(l.text.strip() for l in d["caption"])
                w.add_block(f'<p align="center">\n  <img src="{art_rel("figures/" + d["file"])}" '
                            f'alt="{md_escape(cap) or "Figure, page " + str(pno)}" width="{width}">\n</p>')
                if cap:
                    w.add_block(f'<p align="center"><sub><i>{md_escape(cap)}</i></sub></p>')
                new_page = False
                continue
            if it.kind == "table":
                t = it.data
                if not t["rows"]:
                    continue
                lines = ["| " + " | ".join(t["header"]) + " |",
                         "|" + "|".join(["---"] * len(t["header"])) + "|"]
                for r in t["rows"]:
                    lines.append("| " + " | ".join(r) + " |")
                w.add_block("\n".join(lines))
                new_page = False
                continue
            if it.kind == "ornament":
                if w.callout:
                    w.close_callout()
                w.add_block(f'<p align="center"><img src="{art_rel("ornaments/divider.png")}" alt="" width="200"></p>')
                new_page = False
                continue
            ln = it.line
            k = ln.kind
            t = ln.text.strip()
            if w.pending_kicker and k not in ("h2", "h3", "h4", "kicker"):
                w.add_block(f'<p align="center"><sub>{w.pending_kicker.upper()}</sub></p>')
                w.pending_kicker = ""
            if k == "kicker":
                w.flush()
                w.pending_kicker = title_case(spaced_text(ln))
                continue
            if k in ("h2", "h3", "h4"):
                txt = spaced_text(ln) if line_is_spaced(ln) else re.sub(r"\s{2,}", " ", t)
                if txt.isupper() and len(txt) > 3:
                    txt = title_case(txt)
                # headings wrap: continue the previous heading block
                if w.blocks and w.para is None and w.blocks[-1].startswith("#") and \
                        w.last_heading_y is not None and 0 < ln.y0 - w.last_heading_y < 20 and \
                        w.last_heading_kind == k:
                    w.blocks[-1] += " " + txt
                    w.last_heading_y = ln.y0
                    continue
                if w.pending_kicker:
                    txt = f"{w.pending_kicker} · {txt}"
                    w.pending_kicker = ""
                hashes = {"h2": "##", "h3": "###", "h4": "####"}[k]
                w.add_block(f"{hashes} {md_escape(txt)}")
                w.last_heading_y = ln.y0
                w.last_heading_kind = k
                new_page = False
                continue
            if k in ("subtitle", "epigraph"):
                w.flush()
                prev = w.blocks[-1] if w.blocks else ""
                if ln.marker:
                    w.add_block(f"{ln.marker} *{md_escape(t)}*")
                    w.last_sub_y = ln.y0
                    continue
                if re.match(r"^\d+\. \*", prev) and getattr(w, "last_sub_y", None) is not None \
                        and 0 < ln.y0 - w.last_sub_y < 22:
                    w.blocks[-1] = prev[:-1] + " " + md_escape(t) + "*"
                    w.last_sub_y = ln.y0
                    continue
                if prev.startswith(("<p align=\"center\"><i>", "> *")) and \
                        getattr(w, "last_sub_y", None) is not None and 0 < ln.y0 - w.last_sub_y < max(22, ln.size * 1.9):
                    if prev.startswith("> *"):
                        w.blocks[-1] = prev[:-1] + " " + md_escape(t) + "*"
                    else:
                        w.blocks[-1] = prev.replace("</i></p>", " " + md_escape(t) + "</i></p>")
                elif k == "epigraph":
                    w.add_block(f"> *{md_escape(t)}*")
                else:
                    w.add_block(f'<p align="center"><i>{md_escape(t)}</i></p>')
                w.last_sub_y = ln.y0
                new_page = False
                continue
            if k in ("practice", "audit"):
                w.close_callout()
                label = "▲ Practice" if k == "practice" else "◆ Audit"
                w.blocks.append(f"> **{label}**\n>")
                w.callout = k
                new_page = False
                continue
            if k == "check":
                w.add_block("- [x] " + render_runs(line_runs(ln, ln.size)))
                w.last_check = ln
                new_page = False
                continue
            if k == "muted":
                w.add_block(f'<p align="center"><sub>{md_escape(spaced_text(ln) if line_is_spaced(ln) else t)}</sub></p>')
                continue
            if k == "caption":
                w.add_block(f'<p align="center"><sub><i>{md_escape(t)}</i></sub></p>')
                continue
            # continuation of a checklist line
            if getattr(w, "last_check", None) is not None and w.blocks and \
                    w.blocks[-1].startswith("- [x]") and ln.size < 8 and w.para is None:
                w.blocks[-1] += " " + render_runs(line_runs(ln, ln.size))
                continue
            w.last_check = None
            # callouts: the indented body of a practice/audit
            if w.callout and ln.x0 >= 52:
                if w.para is None:
                    w.blocks[-1] = w.blocks[-1]   # label already placed
                w.body_line(ln, new_page)
            else:
                if w.callout:
                    w.close_callout()
                w.body_line(ln, new_page)
            new_page = False
        # end of page: keep the paragraph open so it can continue

    body = w.text()
    body = re.sub(r"(?m)^(- \[x\] .*)\n(?!- |\n|<|>|#)(.+)$", r"\1 \2", body)
    # callout blocks were written as separate paragraphs: join them
    body = re.sub(r"(> \*\*[▲◆] [A-Za-z]+\*\*\n>)\n\n> ", r"\1\n> ", body)
    body = re.sub(r"\n\n> (?!\*\*[▲◆]|\*)", "\n>\n> ", body)

    # navigation
    nav = []
    if prev_unit:
        nav.append(f"[← {prev_unit[4]}]({rel(md_path, os.path.join(BOOK, prev_unit[3]))})")
    nav.append(f"[Contents]({rel(md_path, os.path.join(BOOK, 'README.md'))})")
    if next_unit:
        nav.append(f"[{next_unit[4]} →]({rel(md_path, os.path.join(BOOK, next_unit[3]))})")
    lvl = LEVELS[level]
    crumb = (f'<p align="center"><sub>THE GEOMETRY OF EXISTENCE · '
             f'{lvl["kicker"].upper()}'
             + (f' · {lvl["name"].upper()}' if level not in (0, 6) else "")
             + f' · PAGES {first}–{last}</sub></p>' if first != last else
             f'<p align="center"><sub>THE GEOMETRY OF EXISTENCE · {lvl["kicker"].upper()}'
             + (f' · {lvl["name"].upper()}' if level not in (0, 6) else "")
             + f' · PAGE {first}</sub></p>')
    if not body.lstrip().startswith("<p align=\"center\">\n  <img") and not body.lstrip().startswith("#"):
        body = f"# {title}\n\n" + body
    footer = "\n\n---\n\n<p align=\"center\">" + " · ".join(nav) + "</p>\n"
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(crumb + "\n\n" + body + footer)
    return unit_meta


def build_vocab(doc):
    for page in doc:
        words = re.findall(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)*", page.get_text())
        # the last word of each line may be a hyphenation artefact; count anyway,
        # artefacts are rare compared with genuine occurrences
        for wd in words:
            VOCAB[wd.lower()] += 1


def main():
    doc = pymupdf.open(os.path.join(ROOT, PDF))
    for sub in ("plates", "figures", "ornaments"):
        d = os.path.join(ART, sub)
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            if f.endswith(".png"):
                os.remove(os.path.join(d, f))
    build_vocab(doc)
    Writer.last_heading_y = None
    Writer.last_heading_kind = None

    figures, plates, units = [], [], []
    # the cover is a plate of its own
    cover = save_plate(doc[0], 1, "cover")
    plates.append(dict(page=1, file=f"plates/{cover}", kicker="Cover",
                       title="The Geometry of Existence",
                       epigraph="A Manual for Life · In five levels, the highest at the end",
                       unit="README.md"))
    for i, u in enumerate(UNITS):
        prev_u = UNITS[i - 1] if i else None
        next_u = UNITS[i + 1] if i + 1 < len(UNITS) else None
        meta = write_unit(doc, u, prev_u, next_u, figures, plates)
        base = os.path.splitext(os.path.basename(u[3]))[0]
        meta["number"] = CHAPTER_NUMBERS.get(base)
        units.append(meta)

    levels = []
    for lv in LEVELS:
        lv = dict(lv)
        for p in plates:
            if p["unit"].startswith(lv["dir"] + "/README") and p["epigraph"]:
                lv["sub"] = p["epigraph"]
        levels.append(lv)
    manifest = dict(title="The Geometry of Existence", subtitle="A Manual for Life",
                    author="Massimo Vincent Panella",
                    edition="Complete edition · 15 November 2026",
                    pdf=PDF, cover=f"plates/{cover}",
                    levels=levels, units=units, plates=plates, figures=figures)
    with open(os.path.join(BOOK, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
    print(f"{len(units)} units, {len(plates)} plates, {len(figures)} figures")


if __name__ == "__main__":
    main()
