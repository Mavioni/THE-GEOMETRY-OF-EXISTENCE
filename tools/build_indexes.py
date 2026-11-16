#!/usr/bin/env python3
"""Write the illustrated indexes that sit around the book.

    python3 tools/build_indexes.py        (after extract_book.py)

Writes book/README.md            the illustrated table of contents
       book/*/README.md          a contents strip appended to each level's opening
       art/README.md             the gallery: every plate and figure, with its page
       art/marks/*.svg           the five marks, Practice and Audit, as badges
       art/banner.svg            the repository banner
       workbook/*.md             one practice sheet per chapter, plus the graded audits

Everything here is derived from book/manifest.json and the Markdown it
indexes; nothing is typed in by hand except the layout.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/Mavioni/THE-GEOMETRY-OF-EXISTENCE"
SITE = "https://mavioni.github.io/THE-GEOMETRY-OF-EXISTENCE/"
PDF_NAME = "The_Geometry_of_Existence_A_Manual_for_Life.pdf"
PDF_DOWNLOAD = f"{REPO}/raw/main/edition/{PDF_NAME}"
BOOK = os.path.join(ROOT, "book")
ART = os.path.join(ROOT, "art")
WORKBOOK = os.path.join(ROOT, "workbook")

NUM_WORDS = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
             "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
             "Eighteen", "Nineteen", "Twenty", "Twenty-One", "Twenty-Two", "Twenty-Three",
             "Twenty-Four", "Twenty-Five"]

# The book's palette (sampled from the edition's typesetting)
NAVY = "#14112e"
INK = "#1f1b3a"
CREAM = "#f4eedf"
GOLD = "#c9a14a"
GOLD_DEEP = "#8c6a1e"
TEAL = "#3e8e89"
MUTED = "#8c879a"

MARKS = [
    ("lived", "LIVED", GOLD_DEEP, "A stance or a practice. Tested only by doing it."),
    ("argued", "ARGUED", INK, "Reasons are given. No one is compelled."),
    ("demonstrated", "DEMONSTRATED", TEAL, "Follows from stated definitions, or established science in a stated domain. Recomputed."),
    ("measured", "MEASURED", "#b4562f", "An observation, with its source. The book reports none of its own."),
    ("on-record", "ON RECORD", "#5b4f8a", "A matter of published history: a date, a name, a paper."),
    ("practice", "▲ PRACTICE", GOLD, "Something done today."),
    ("audit", "◆ AUDIT", TEAL, "A question that can find the chapter wrong."),
]


def rel(from_file, to_path):
    return os.path.relpath(to_path, os.path.dirname(from_file)).replace(os.sep, "/")


def badge_svg(label, color):
    # letter-spaced small caps on a hairline frame, like the marks in the book
    w = int(len(label) * 7.6 + 26)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="22" viewBox="0 0 {w} 22" role="img" aria-label="{label}">
  <rect x="0.5" y="0.5" width="{w - 1}" height="21" rx="2" fill="{CREAM}" stroke="{color}" stroke-width="1"/>
  <text x="{w / 2}" y="15" text-anchor="middle" font-family="EB Garamond, Garamond, Georgia, serif" font-size="11" font-weight="600" letter-spacing="1.6" fill="{color}">{label}</text>
</svg>
'''


def banner_svg():
    rings = "\n".join(
        f'    <circle cx="600" cy="150" r="{r}" fill="none" stroke="{GOLD}" stroke-opacity="{0.55 - i * 0.045:.3f}" stroke-width="0.8"/>'
        for i, r in enumerate(range(18, 18 + 11 * 22, 22)))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-label="The Geometry of Existence — A Manual for Life">
  <defs>
    <radialGradient id="g" cx="50%" cy="50%" r="70%">
      <stop offset="0" stop-color="#241e52"/>
      <stop offset="1" stop-color="{NAVY}"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="300" fill="url(#g)"/>
  <rect x="14" y="14" width="1172" height="272" fill="none" stroke="{GOLD}" stroke-opacity="0.6" stroke-width="0.8"/>
{rings}
    <circle cx="600" cy="150" r="6" fill="none" stroke="#efe6d0" stroke-width="1.2"/>
    <circle cx="600" cy="150" r="1.6" fill="#efe6d0"/>
  <text x="600" y="72" text-anchor="middle" font-family="Cormorant Garamond, Garamond, Georgia, serif" font-size="34" font-weight="300" letter-spacing="9" fill="#efe6d0">THE GEOMETRY OF EXISTENCE</text>
  <text x="600" y="252" text-anchor="middle" font-family="EB Garamond, Garamond, Georgia, serif" font-size="13" letter-spacing="6" fill="{GOLD}">A MANUAL FOR LIFE · IN FIVE LEVELS, THE HIGHEST AT THE END</text>
</svg>
'''


def load():
    with open(os.path.join(BOOK, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)


def thumb(plate):
    return plate.replace("plates/", "plates/thumbs/")


def unit_label(u):
    if u["number"]:
        return f"{u['number']} · {u['title']}"
    return u["title"]


# ---------------------------------------------------------------------------


def write_marks():
    os.makedirs(os.path.join(ART, "marks"), exist_ok=True)
    for key, label, color, _ in MARKS:
        with open(os.path.join(ART, "marks", f"{key}.svg"), "w", encoding="utf-8") as fh:
            fh.write(badge_svg(label, color))
    with open(os.path.join(ART, "banner.svg"), "w", encoding="utf-8") as fh:
        fh.write(banner_svg())


def level_units(m, n):
    return [u for u in m["units"] if u["level"] == n]


def write_book_index(m):
    path = os.path.join(BOOK, "README.md")
    out = []
    out.append('<p align="center">\n  <img src="../art/plates/p001-cover.png" alt="The Geometry of Existence — cover" width="300">\n</p>')
    out.append('<h1 align="center">Contents</h1>')
    out.append('<p align="center"><i>One book in five levels. Each level says the same thing at a greater depth,<br>'
               'and each is complete in itself. You may stop at any level and have the whole of that level.</i></p>')
    out.append('<p align="center"><img src="../art/ornaments/divider.png" alt="" width="200"></p>')
    for lv in m["levels"]:
        units = level_units(m, lv["n"])
        if not units:
            continue
        opener = units[0]
        head = []
        if opener["kind"] == "level" and opener["plates"]:
            img = rel(path, os.path.join(ART, thumb(opener["plates"][0])))
            head.append(f'<a href="{rel(path, os.path.join(BOOK, opener["path"]))}">'
                        f'<img src="{img}" alt="{lv["kicker"]} — {lv["name"]}" width="120" align="left"></a>')
        out.append("\n".join(head) + f'\n\n### {lv["kicker"]} · {lv["name"]}\n\n*{lv["sub"]}*\n')
        lines = []
        for u in units:
            link = rel(path, os.path.join(BOOK, u["path"]))
            if u["kind"] == "level":
                continue
            if u["kind"] == "part":
                lines.append(f"- **[{u['title']}]({link})** — *{u['epigraph']}*")
                continue
            indent = "  " if lv["n"] == 2 and u["kind"] == "chapter" else ""
            pages = f"p. {u['first']}" if u["first"] == u["last"] else f"pp. {u['first']}–{u['last']}"
            epi = f" — *{u['epigraph']}*" if u["kind"] == "chapter" and u["epigraph"] else ""
            lines.append(f"{indent}- [{unit_label(u)}]({link}) <sub>{pages}</sub>{epi}")
        out.append("\n".join(lines))
        out.append('<br clear="left">')
    out.append("---\n\n<p align=\"center\">"
               "[Download the PDF](../edition/README.md) · "
               f"[Read online]({SITE}) · "
               "[The gallery](../art/README.md) · [The workbook](../workbook/README.md) · "
               "[Run the checks](../checks/README.md)</p>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(out) + "\n")


def append_level_strips(m):
    """Give each level's opening page a strip of its chapters' plates."""
    for lv in m["levels"]:
        units = level_units(m, lv["n"])
        if not units or units[0]["kind"] != "level":
            continue
        opener = units[0]
        path = os.path.join(BOOK, opener["path"])
        text = open(path, encoding="utf-8").read()
        text = re.sub(r"\n<!-- level-strip -->.*?<!-- /level-strip -->\n", "\n", text, flags=re.S)
        cells, rows = [], []
        for u in units[1:]:
            link = rel(path, os.path.join(BOOK, u["path"]))
            if u["plates"]:
                img = rel(path, os.path.join(ART, thumb(u["plates"][0])))
                cells.append(f'<td align="center" valign="top" width="25%"><a href="{link}"><img src="{img}" width="110" alt="{u["title"]}"></a><br>'
                             f'<sub>{unit_label(u) if u["kind"] != "part" else u["title"]}</sub></td>')
            else:
                cells.append(f'<td align="center" valign="top" width="25%"><a href="{link}"><b>{u["title"]}</b></a><br><sub>'
                             + (f"p. {u['first']}" if u["first"] == u["last"] else f"pp. {u['first']}–{u['last']}")
                             + "</sub></td>")
        for i in range(0, len(cells), 4):
            rows.append("<tr>" + "".join(cells[i:i + 4]) + "</tr>")
        strip = ("\n<!-- level-strip -->\n## In this level\n\n<table>\n" + "\n".join(rows) +
                 "\n</table>\n<!-- /level-strip -->\n")
        # place the strip before the navigation footer
        idx = text.rfind("\n---\n")
        text = text[:idx] + "\n" + strip + text[idx:]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)


def write_gallery(m):
    path = os.path.join(ART, "README.md")
    unit_by_path = {u["path"]: u for u in m["units"]}
    out = ['<p align="center"><img src="banner.svg" alt="The Geometry of Existence" width="100%"></p>',
           "# The Gallery",
           "*Every plate and figure in the complete edition, cut from the typeset PDF at print resolution.*",
           "The colophon says it plainly: *every figure is computed from the book's own mathematics.* "
           "The plates open the levels, the parts and the chapters; the figures sit inside the text, "
           "where they answer to a sentence. Each image links to the page of the book it belongs to.",
           "| Folder | What it holds |\n|---|---|\n"
           "| [`plates/`](plates) | the full-page plates at 144 dpi — cover, five levels, four parts, twenty-five chapters, colophon |\n"
           "| [`plates/thumbs/`](plates/thumbs) | the same plates at gallery size |\n"
           "| [`figures/`](figures) | medallions, diagrams and charts, cropped from the text pages at 288 dpi |\n"
           "| [`marks/`](marks) | the five marks, Practice and Audit, as badges for use in issues and notes |\n"
           "| [`ornaments/`](ornaments) | the section divider |\n"
           "| [`banner.svg`](banner.svg) | the repository banner |",
           "## Plates"]
    rows, cells = [], []
    for p in m["plates"]:
        u = unit_by_path.get(p["unit"])
        link = rel(path, os.path.join(BOOK, p["unit"])) if u else rel(path, os.path.join(ROOT, "README.md"))
        cap = " · ".join(x for x in (p["kicker"], p["title"]) if x)
        cells.append(f'<td align="center" valign="top" width="25%"><a href="{link}"><img src="{p["file"]}" width="150" alt="{cap}"></a>'
                     f'<br><sub><b>{cap}</b><br>page {p["page"]}</sub></td>')
    for i in range(0, len(cells), 4):
        rows.append("<tr>" + "".join(cells[i:i + 4]) + "</tr>")
    out.append("<table>\n" + "\n".join(rows) + "\n</table>")
    out.append("## Figures")
    page_unit = {}
    for u in m["units"]:
        for pno in range(u["first"], u["last"] + 1):
            page_unit[pno] = u
    rows, cells = [], []
    for f in m["figures"]:
        u = page_unit.get(f["page"])
        link = rel(path, os.path.join(BOOK, u["path"])) if u else "#"
        cap = f["caption"] or (u["title"] if u else "")
        cap = re.sub(r"\s+", " ", cap)
        short = cap if len(cap) < 140 else cap[:137].rsplit(" ", 1)[0] + "…"
        cells.append(f'<td align="center" valign="top" width="33%"><a href="{link}"><img src="{f["file"]}" width="220" alt="{short}"></a>'
                     f'<br><sub><i>{short}</i><br>page {f["page"]} · {u["title"] if u else ""}</sub></td>')
    for i in range(0, len(cells), 3):
        rows.append("<tr>" + "".join(cells[i:i + 3]) + "</tr>")
    out.append("<table>\n" + "\n".join(rows) + "\n</table>")
    out.append("## Marks\n\n" + "\n".join(
        f'- <img src="marks/{k}.svg" alt="{lbl}" height="18"> &nbsp;{desc}' for k, lbl, _, desc in MARKS))
    out.append("---\n\n<p align=\"center\">[The book](../book/README.md) · [Home](../README.md)</p>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(out) + "\n")


# ---------------------------------------------------------------------------
# the workbook
# ---------------------------------------------------------------------------


def callouts(md):
    """Pull the ▲ Practice and ◆ Audit blocks out of a chapter."""
    found = {}
    for kind in ("Practice", "Audit"):
        mm = re.search(r"> \*\*[▲◆] " + kind + r"\*\*\n>\n((?:> .*\n?)+)", md)
        if mm:
            found[kind] = "\n".join(l[2:] for l in mm.group(1).strip().split("\n"))
    return found


def graded_lines(m):
    md = open(os.path.join(BOOK, "3-the-degree/19-the-graded-audits.md"), encoding="utf-8").read()
    out = {}
    for mm in re.finditer(r"^\*\*(\d+) · ([^*]+?)\.\*\* (.+)$", md, flags=re.M):
        out[int(mm.group(1))] = mm.group(3)
    return out


def write_workbook(m):
    os.makedirs(WORKBOOK, exist_ok=True)
    graded = graded_lines(m)
    index = []
    for u in m["units"]:
        if u["kind"] != "chapter":
            continue
        md = open(os.path.join(BOOK, u["path"]), encoding="utf-8").read()
        c = callouts(md)
        if not c:
            continue
        n = u["number"]
        fname = f"{n:02d}-{os.path.splitext(os.path.basename(u['path']))[0].split('-', 1)[1]}.md"
        path = os.path.join(WORKBOOK, fname)
        chap = rel(path, os.path.join(BOOK, u["path"]))
        img = rel(path, os.path.join(ART, thumb(u["plates"][0]))) if u["plates"] else ""
        body = [f'<img src="{img}" alt="Chapter {NUM_WORDS[n]}" width="110" align="right">' if img else "",
                f"# {n} · {u['title']}",
                f"> *{u['epigraph']}*" if u["epigraph"] else "",
                f"<sub>Chapter {NUM_WORDS[n]} · [read the chapter]({chap}) · pages {u['first']}–{u['last']}</sub>",
                '<br clear="right">',
                "## Before you begin — the falsifier",
                "*“Do a Practice exactly as written, with your falsifier written first. If nothing you can "
                "observe changes, the practice failed for you. That is a result, and it counts.”* "
                "— Corrections and Open Accounts",
                "If this practice works for me, I will be able to observe:\n\n> &nbsp;\n\n"
                "If it does not, I will see instead:\n\n> &nbsp;",
                "## ▲ Practice",
                "> " + c.get("Practice", "").replace("\n", "\n> "),
                "| Date | What I did, exactly as written | What I observed |\n|---|---|---|\n|  |  |  |\n|  |  |  |\n|  |  |  |",
                "## ◆ Audit",
                "> " + c.get("Audit", "").replace("\n", "\n> "),
                "My honest answer:\n\n> &nbsp;"]
        if n in graded:
            body += ["## The graded line",
                     "<sub>From *The Graded Audits*, Level Three. Mark it, date it, and mark it again in a month.</sub>",
                     f"> {graded[n]}",
                     "| Date | Mark (0–10) | What would raise it one | What would lower it one |\n"
                     "|---|---|---|---|\n|  |  |  |  |\n|  |  |  |  |"]
        body += ["## Result",
                 "- [ ] The falsifier was written before the practice began.\n"
                 "- [ ] Something I could observe changed.\n"
                 "- [ ] Nothing changed — the practice failed for me, and that result is recorded here.",
                 "---",
                 "<p align=\"center\"><sub>Nothing here is medical, psychological, or legal advice. "
                 "The practices are yours to try and yours to stop.</sub></p>",
                 f"<p align=\"center\"><a href=\"README.md\">Workbook</a> · <a href=\"{chap}\">Chapter</a></p>"]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(b for b in body if b) + "\n")
        index.append((n, u, fname, img))

    path = os.path.join(WORKBOOK, "README.md")
    out = ['<p align="center"><img src="../art/plates/thumbs/p012-the-manual.png" width="140" alt="Level Two — The Manual"></p>',
           '<h1 align="center">The Workbook</h1>',
           '<p align="center"><i>Read one chapter. Do its practice. Then read the next.</i></p>',
           "Every chapter of Levels Two to Four ends in a **Practice** — something done today — and an "
           "**Audit** — a question that can find the chapter wrong. This folder turns each of them into a sheet "
           "you can copy, fill and keep: the falsifier first, the practice as written, the audit, and for the "
           "fifteen chapters of the Manual the graded line from Level Three, to mark now and again in a month.",
           "**How to use it.** Copy a sheet into your own notes (or fork this repository and fill it in your "
           "fork — your answers are yours, so keep them in a private fork). Write the falsifier before you "
           "begin. Record what happened, including nothing.",
           ]
    rows, cells = [], []
    for n, u, fname, img in index:
        im = f'<img src="{img}" width="90" alt="">' if img else ""
        cells.append(f'<td align="center" valign="top" width="20%"><a href="{fname}">{im}</a><br><sub><b>{n}</b> · {u["title"]}</sub></td>')
    for i in range(0, len(cells), 5):
        rows.append("<tr>" + "".join(cells[i:i + 5]) + "</tr>")
    out.append("<table>\n" + "\n".join(rows) + "\n</table>")
    out.append("See also: [The Graded Audits](../book/3-the-degree/19-the-graded-audits.md) · "
               "[The Fifteen Lines](../book/2-the-manual/16-the-fifteen-lines.md) · "
               "[The Discipline in One Page](../book/6-back-matter/01-the-discipline-in-one-page.md)")
    out.append("<p align=\"center\"><sub>Nothing here is medical, psychological, or legal advice. "
               "The practices are yours to try and yours to stop.</sub></p>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(out) + "\n")
    return len(index)


def pdf_facts(m):
    path = os.path.join(ROOT, "edition", PDF_NAME)
    data = open(path, "rb").read()
    pages = max(u["last"] for u in m["units"])
    return dict(pages=pages, mb=f"{len(data) / 1e6:.1f} MB", sha=hashlib.sha256(data).hexdigest())


def download_svg(label, sub):
    w = 340
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="58" viewBox="0 0 {w} 58" role="img" aria-label="{label} — {sub}">
  <rect x="0.5" y="0.5" width="{w - 1}" height="57" rx="3" fill="{NAVY}" stroke="{GOLD}" stroke-width="1"/>
  <g transform="translate(30 29)" fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
    <circle r="15" stroke-opacity="0.5"/><path d="M0 -8 V7 M-6 1 L0 7 L6 1"/><path d="M-8 11 H8"/>
  </g>
  <text x="58" y="26" font-family="Cormorant Garamond, Garamond, Georgia, serif" font-size="17" letter-spacing="3" fill="#efe6d0">{label}</text>
  <text x="58" y="44" font-family="EB Garamond, Garamond, Georgia, serif" font-size="11.5" letter-spacing="1.2" fill="{GOLD}">{sub}</text>
</svg>
'''


def write_edition_page(m):
    f = pdf_facts(m)
    sub = f"PDF · {f['pages']} PAGES · {f['mb']}"
    with open(os.path.join(ART, "download.svg"), "w", encoding="utf-8") as fh:
        fh.write(download_svg("DOWNLOAD THE BOOK", sub))
    text = f'''<p align="center"><a href="{PDF_DOWNLOAD}"><img src="../art/plates/p001-cover.png" alt="The Geometry of Existence — cover. Select to download the PDF." width="260"></a></p>

<h1 align="center">The Edition</h1>

<p align="center"><i>The Geometry of Existence: A Manual for Life</i> · complete edition, 15 November 2026</p>

<p align="center"><a href="{PDF_DOWNLOAD}"><img src="../art/download.svg" alt="Download the book: PDF, {f['pages']} pages, {f['mb']}" width="340"></a></p>

## Download

| | |
|---|---|
| **Download** | **[{PDF_NAME}]({PDF_DOWNLOAD})** — PDF, {f['pages']} pages, {f['mb']} |
| **View in the browser** | [Open on GitHub]({PDF_NAME}) |
| **Page size** | 5.5 × 8.5 in (digest), the plates printed full-bleed in navy and gold |
| **Typefaces** | EB Garamond and Cormorant Garamond, embedded |
| **SHA-256** | `{f['sha']}` |

To check your copy: `sha256sum {PDF_NAME}` (macOS: `shasum -a 256 {PDF_NAME}`) should print the line above.

## Other ways to read it

The PDF is the edition of record. It is laid out for print and is **not a tagged PDF**, so screen readers and reflowing readers handle it poorly. The same text, with every plate and figure and with image descriptions, is available in two accessible forms:

- **[The reading edition]({SITE})** — the website: reflows to any screen, follows light or dark mode, works with screen readers and browser zoom, and can be printed page by page.
- **[The book in Markdown](../book/README.md)** — one file per chapter, readable on GitHub or in any text editor.

Both are cut from this PDF by the tools in this repository, and a check confirms every printed word reaches them.

---

<p align="center"><a href="../README.md">Home</a> · <a href="../book/README.md">Contents</a> · <a href="{SITE}">Website</a></p>
'''
    with open(os.path.join(ROOT, "edition", "README.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    return f


def main():
    m = load()
    write_edition_page(m)
    write_marks()
    write_book_index(m)
    append_level_strips(m)
    write_gallery(m)
    n = write_workbook(m)
    print(f"indexes written; workbook has {n} sheets")


if __name__ == "__main__":
    main()
