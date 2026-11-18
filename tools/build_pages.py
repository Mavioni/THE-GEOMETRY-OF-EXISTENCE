#!/usr/bin/env python3
"""Write the pages that are built from the book rather than cut from it.

    python3 tools/build_pages.py

Reads   book/manifest.json   (written by extract.py)
Writes  book/README.md       the contents, with every part and chapter
        art/README.md        the gallery: paintings, plates and figures
        workbook/*.md        a practice sheet for every chapter, the
                             Ninety-Day Trial and the Respect Ledger
Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rel(src: str, dst: str) -> str:
    return os.path.relpath(os.path.join(ROOT, dst), os.path.dirname(os.path.join(ROOT, src))).replace(os.sep, "/")


def pages(u) -> str:
    a, b = u["pages"]
    return f"p. {a}" if a == b else f"pp. {a}–{b}"


def esc(s: str) -> str:
    return s.replace("|", "\\|").replace("*", "\\*")


def write(path: str, text: str):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def painting_title(m, part) -> str:
    """The line under a Book's name on its painting: 'Existence', 'Consciousness' …"""
    if not part["plate"]:
        return ""
    words = m["paintings"][str(part["plate"])]["words"]
    rest = words.replace(part["kicker"].upper(), "", 1).replace(part["name"], "", 1)
    return re.sub(r"\s+", " ", rest).strip()


# ---------------------------------------------------------------------------
# book/README.md — the contents
# ---------------------------------------------------------------------------

def contents(m):
    src = "book/README.md"
    units = m["units"]
    out = [
        f'<p align="center"><img src="{rel(src, m["paintings"]["1"]["path"])}" alt="The cover of The Geometry of Everything" width="240"></p>',
        '<h1 align="center">Contents</h1>',
        f'<p align="center"><i>{m["title"]} · {m["subtitle"]}</i><br>{m["author"]} · {m["edition"]}</p>',
        "",
        "> **New here?** Begin with [How to Carry This Book](0-opening/01-how-to-carry-this-book.md). "
        "Every page ends with a link to the next one, so you can read straight through. "
        "To look something up by what is happening in your life, use the "
        "[Index of Situations](7-at-the-back/04-index-of-situations.md).",
        "",
    ]
    for part in m["parts"]:
        mine = [u for u in units if u["part"] == part["n"]]
        sub = painting_title(m, part)
        heading = part["name"] if part["n"] in (0, 7) else f"{part['kicker']} · {part['name']}"
        out.append(f"## {heading}" + (f" &nbsp;<sub>*{sub}*</sub>" if sub else ""))
        out.append("")
        opener = next((u for u in mine if u["kind"] == "opener"), None)
        if part["plate"]:
            img = m["paintings"][str(part["plate"])]["path"]
            link = rel(src, opener["path"]) if opener else ""
            out.append(f'<a href="{link}"><img src="{rel(src, img)}" alt="{part["kicker"]}: {part["name"]}" width="110" align="left"></a>')
            out.append("")
        if opener and opener.get("intro"):
            out.append(f"*{opener['intro']}*")
            out.append("")
        for u in mine:
            if u["kind"] == "opener":
                continue
            link = rel(src, u["path"])
            if u["kind"] == "chapter":
                sub_ = f" · *{u['subtitle']}*" if u.get("subtitle") else ""
                out.append(f"{u['number']}. [{u['title']}]({link}){sub_} <sub>{pages(u)}</sub>")
            else:
                out.append(f"- [{u['title']}]({link}) <sub>{pages(u)}</sub>")
        out.append("")
        if part["plate"]:
            out.append('<br clear="left">')
            out.append("")
    out += [
        "---",
        "",
        '<p align="center"><a href="../README.md">Home</a> &nbsp;·&nbsp; '
        '<a href="../art/README.md">Gallery</a> &nbsp;·&nbsp; '
        '<a href="../workbook/README.md">Workbook</a> &nbsp;·&nbsp; '
        f'<a href="../{m["pdf"]}">The PDF</a></p>',
    ]
    write(src, "\n".join(out))


# ---------------------------------------------------------------------------
# art/README.md — the gallery
# ---------------------------------------------------------------------------

def gallery(m):
    src = "art/README.md"
    units = m["units"]
    p = m["paintings"]
    out = [
        "# The Gallery",
        "",
        "Every picture in the book, in reading order. The paintings open the book and each of its "
        "five Books and the Summit. The plates open the chapters, and the figures illustrate the "
        "opening pages and the mathematics of the Summit. Select any picture to see it full size.",
        "",
        "> *The chapter plates are computed from the laws they name.* "
        "(Sources and Translations, p. 215)",
        "",
        "## The paintings",
        "",
        "| | | |",
        "|:---:|:---:|:---:|",
    ]
    cells = []
    order = ["1"] + [str(part["plate"]) for part in m["parts"] if part["plate"]] + [str(m["pages"])]
    for key in order:
        pt = p[key]
        name = os.path.basename(pt["path"])
        label = {"cover.jpg": "The cover", "back-cover.jpg": "The back cover"}.get(name)
        if not label:
            part = next(x for x in m["parts"] if str(x["plate"]) == key)
            label = f"{part['kicker']} · {part['name']}"
        cells.append(f'<a href="{rel(src, pt["path"])}"><img src="{rel(src, pt["path"])}" '
                     f'alt="{label}" width="200"></a><br><sub>{label}</sub>')
    for i in range(0, len(cells), 3):
        row = cells[i:i + 3] + [""] * (3 - len(cells[i:i + 3]))
        out.append("| " + " | ".join(row) + " |")
    out += ["", "## The chapter plates", "", "| | | |", "|:---:|:---:|:---:|"]
    cells = []
    for u in units:
        if u["kind"] != "chapter":
            continue
        img = u["plate"]
        cap = u.get("plate_caption", "")
        cells.append(f'<a href="{rel(src, u["path"])}"><img src="{rel(src, img)}" alt="{cap}" width="200"></a>'
                     f'<br><sub><b>{u["number"]} · {u["title"]}</b><br><i>{cap}</i></sub>')
    for i in range(0, len(cells), 3):
        row = cells[i:i + 3] + [""] * (3 - len(cells[i:i + 3]))
        out.append("| " + " | ".join(row) + " |")
    out += ["", "## The figures", ""]
    for u in units:
        figs = [f for f in u.get("figures", []) if "/figures/" in f["path"]]
        for f in figs:
            cap = f["caption"] or "(no caption in the book)"
            out.append(f'<a href="{rel(src, u["path"])}"><img src="{rel(src, f["path"])}" alt="{f["caption"]}" width="260" align="left"></a>')
            out.append("")
            out.append(f"**[{u['title']}]({rel(src, u['path'])})** <sub>{pages(u)}</sub>  ")
            out.append(f"*{esc(cap)}*")
            out.append("")
            out.append('<br clear="left">')
            out.append("")
    out += ["---", "", '<p align="center"><a href="../README.md">Home</a> &nbsp;·&nbsp; '
            '<a href="../book/README.md">Contents</a></p>']
    write(src, "\n".join(out))


# ---------------------------------------------------------------------------
# workbook/ — practice sheets
# ---------------------------------------------------------------------------

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def sheet(m, u, prev_u, next_u):
    src = f"workbook/{os.path.basename(u['path'])}"
    part = m["parts"][u["part"]]
    out = [
        f"<sub>WORKBOOK · {part['kicker'].upper()} · {part['name'].upper()}</sub>",
        "",
        f"# {u['number']} · {u['title']}",
        "",
        f"*{u.get('subtitle', '')}* &nbsp;·&nbsp; [Read the chapter]({rel(src, u['path'])}) <sub>({pages(u)})</sub>",
        "",
    ]
    if u.get("creed"):
        out += [f"> **{u['creed']['word'].upper()}** · *{u['creed']['question']}*", ""]
    out += ["## The Practice", ""]
    for label, text in u.get("practice", []):
        out += [f"**{label.title()}.** {text}", ""]
        if label == "DAILY":
            out += ["| " + " | ".join(DAYS) + " |", "|" + ":---:|" * 7, "| " + " | ".join(["☐"] * 7) + " |", ""]
        else:
            out += ["> This week: ", ">", "> &nbsp;", ""]
    out += ["## The Ledger", "", "Four questions, one for each word of the creed.", "",
            "| | Question | My answer |", "|---|---|---|"]
    for label, text in u.get("ledger", []):
        out.append(f"| **{label.title()}** | {esc(text)} | |")
    out += ["", "## Where it stops working", "",
            "*The Reversal, the place where the teaching stops working:*", "",
            f"> {u.get('reversal', '')}", ""]
    if u.get("song"):
        out += ["## To carry", "", "*The Song:*", "", "<br>\n".join(f"*{line}*" for line in u["song"]), ""]
    nav = []
    if prev_u:
        nav.append(f"[← {prev_u['number']} · {prev_u['title']}]({os.path.basename(prev_u['path'])})")
    nav.append("[Workbook](README.md)")
    if next_u:
        nav.append(f"[{next_u['number']} · {next_u['title']} →]({os.path.basename(next_u['path'])})")
    out += ["---", "", '<p align="center">' + " &nbsp;·&nbsp; ".join(nav) + "</p>"]
    write(src, "\n".join(out))


def trial_sheet(m):
    src = "workbook/the-ninety-day-trial.md"
    trial = next(u for u in m["units"] if u["title"] == "The Ninety-Day Trial")
    out = [
        "<sub>WORKBOOK</sub>",
        "",
        "# The Ninety-Day Trial",
        "",
        f"The book's own test of itself, to run on your own life. The full instructions are in "
        f"[The Ninety-Day Trial]({rel(src, trial['path'])}) <sub>({pages(trial)})</sub>. This sheet is for keeping score.",
        "",
        "## My sealed prediction · Day 0",
        "",
        "*What I expect to change, and by how much:*",
        "",
        "> &nbsp;",
        "",
        "## Three behaviours I am counting",
        "",
        "| | Behaviour | Baseline (days −14 to 0) | Day 30 | Day 37 | Day 90 |",
        "|---|---|---|---|---|---|",
        "| 1 | | | | | |",
        "| 2 | | | | | |",
        "| 3 | | | | | |",
        "",
        "## Ninety days, marked",
        "",
        "Mark each day kept. Days 31 to 37 are the pause: stop the practices, keep measuring.",
        "",
    ]
    def cell(d):
        return f"*{d} · pause*" if 31 <= d <= 37 else f"☐ {d}"
    for start in range(1, 91, 10):
        out.append("| " + " | ".join(cell(d) for d in range(start, start + 10)) + " |")
        if start == 1:
            out.append("|" + "---|" * 10)
    out += [
        "",
        "## Weekly rating from someone who sees you often",
        "",
        "*From 0 to 10: how calm, kind and reliable was I this week?*",
        "",
        "| Week | " + " | ".join(str(i) for i in range(1, 14)) + " |",
        "|---|" + "---|" * 13,
        "| Rating | " + " | ".join("" for _ in range(13)) + " |",
        "",
        "## The verdict · Day 90",
        "",
        "*Compared with my own starting trend, not just my starting point:*",
        "",
        "- What worked:",
        "- What did not:",
        "- What I will keep:",
        "",
        "---",
        "",
        '<p align="center"><a href="README.md">Workbook</a> &nbsp;·&nbsp; '
        '<a href="the-respect-ledger.md">The Respect Ledger →</a></p>',
    ]
    write(src, "\n".join(out))


def ledger_sheet(m):
    src = "workbook/the-respect-ledger.md"
    led = next(u for u in m["units"] if u["title"] == "The Respect Ledger")
    fl = next(u for u in m["units"] if u["title"] == "The Floor and the Ceiling")
    out = [
        "<sub>WORKBOOK</sub>",
        "",
        "# The Respect Ledger",
        "",
        "Three columns, kept weekly and honestly. **Given:** the dignity you extended freely. "
        "**Earned:** the trust you built by keeping your word. **Spent:** the standing you lost "
        "through your own lapses. Count care as conduct. Remember the starting balance.",
        "",
        f"<sub>From [The Respect Ledger]({rel(src, led['path'])}) and "
        f"[The Floor and the Ceiling]({rel(src, fl['path'])}).</sub>",
        "",
        "| Week of | Given | Earned | Spent |",
        "|---|---|---|---|",
    ]
    out += ["| | | | |"] * 13
    out += ["", "---", "", '<p align="center"><a href="the-ninety-day-trial.md">← The Ninety-Day Trial</a> '
            '&nbsp;·&nbsp; <a href="README.md">Workbook</a></p>']
    write(src, "\n".join(out))


def workbook(m):
    wb = os.path.join(ROOT, "workbook")
    if os.path.isdir(wb):
        shutil.rmtree(wb)
    chs = [u for u in m["units"] if u["kind"] == "chapter"]
    for i, u in enumerate(chs):
        sheet(m, u, chs[i - 1] if i else None, chs[i + 1] if i + 1 < len(chs) else None)
    trial_sheet(m)
    ledger_sheet(m)
    out = [
        "# The Workbook",
        "",
        "The book asks to be practised, not only read: *“Run the Ninety-Day Trial and judge the book by "
        "your own life.”* These sheets hold the practical parts of every chapter in one place, with room to write.",
        "",
        "**How to use them.** Open a sheet and print it (in your browser: *File → Print*), or copy it into "
        "your own notes. If you have a GitHub account you can also make your own copy of this whole "
        "repository (the **Fork** button at the top of the page) and fill the sheets in there.",
        "",
        "## For the whole book",
        "",
        "- [The Ninety-Day Trial](the-ninety-day-trial.md): your prediction, the ninety days, the verdict",
        "- [The Respect Ledger](the-respect-ledger.md): given, earned and spent, week by week",
        "",
    ]
    for part in m["parts"]:
        mine = [u for u in chs if u["part"] == part["n"]]
        if not mine:
            continue
        out += [f"## {part['kicker']} · {part['name']}", ""]
        for u in mine:
            word = u.get("creed", {}).get("word", "")
            out.append(f"{u['number']}. [{u['title']}]({os.path.basename(u['path'])}) <sub>{word}</sub>")
        out.append("")
    out += ["---", "", '<p align="center"><a href="../README.md">Home</a> &nbsp;·&nbsp; '
            '<a href="../book/README.md">Contents</a></p>']
    write("workbook/README.md", "\n".join(out))


def main():
    with open(os.path.join(ROOT, "book", "manifest.json"), encoding="utf-8") as f:
        m = json.load(f)
    contents(m)
    gallery(m)
    workbook(m)
    print("wrote book/README.md, art/README.md and workbook/")


if __name__ == "__main__":
    main()
