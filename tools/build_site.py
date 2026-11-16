#!/usr/bin/env python3
"""Build the reading edition: a static website made from the Markdown book.

    pip install markdown
    python3 tools/build_site.py            # writes _site/
    python3 -m http.server -d _site 8000   # read it at http://localhost:8000

The site is laid out like the book: navy plates with gold line-work open
every level, part and chapter; text pages are cream; the five marks are set in
small capitals; each Practice and Audit is a ruled box. It follows the reader's
light or dark setting. GitHub Pages publishes it through
.github/workflows/pages.yml.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book")
OUT = os.path.join(ROOT, "_site")
SITE_URL = "https://mavioni.github.io/THE-GEOMETRY-OF-EXISTENCE/"
PDF_REL = "edition/The_Geometry_of_Existence_A_Manual_for_Life.pdf"
PDF_SAVE_AS = "The-Geometry-of-Existence.pdf"


def pdf_label():
    size = os.path.getsize(os.path.join(ROOT, PDF_REL)) / 1e6
    return f"PDF, 214 pages, {size:.1f} MB"

MARK_HELP = {
    "lived": "Lived — a stance or a practice. Tested only by doing it.",
    "argued": "Argued — reasons are given. No one is compelled.",
    "demonstrated": "Demonstrated — follows from stated definitions, or is established science within a stated domain.",
    "measured": "Measured — an observation, with its source.",
    "on-record": "On record — a matter of published history.",
}
NUM_WORDS = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
             "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
             "Eighteen", "Nineteen", "Twenty", "Twenty-One", "Twenty-Two", "Twenty-Three",
             "Twenty-Four", "Twenty-Five"]


def load_manifest():
    with open(os.path.join(BOOK, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)


def out_path_for(md_rel: str) -> str:
    """book/2-the-manual/README.md -> book/2-the-manual/index.html"""
    base, _ = os.path.splitext(md_rel)
    if os.path.basename(base) == "README":
        base = os.path.join(os.path.dirname(base), "index")
    return base + ".html"


def rel(from_out: str, to_out: str) -> str:
    return os.path.relpath(os.path.join(OUT, to_out), os.path.dirname(os.path.join(OUT, from_out))).replace(os.sep, "/")


# ---------------------------------------------------------------------------
# Markdown -> HTML, in the book's dress
# ---------------------------------------------------------------------------

FIG_RE = re.compile(
    r'<p align="center">\n  <img src="([^"]+/figures/[^"]+)" alt="([^"]*)" width="(\d+)">\n</p>'
    r'(?:\n\n<p align="center"><sub><i>(.*?)</i></sub></p>(?:\n\n<p align="center"><sub><i>(.*?)</i></sub></p>)?)?')


def prepare_markdown(md: str, strip_plate: bool) -> str:
    lines = md.split("\n", 1)
    if lines[0].startswith('<p align="center"><sub>THE GEOMETRY OF EXISTENCE'):
        md = lines[1]
    cut = md.rfind("\n---\n")
    if cut != -1 and "[Contents]" in md[cut:]:
        md = md[:cut]
    md = re.sub(r"<!-- level-strip -->.*?<!-- /level-strip -->", "", md, flags=re.S)
    if strip_plate:
        md = re.sub(r'^\s*<p align="center">\n  <img src="[^"]*plates/[^"]*"[^>]*>\n</p>\n\n'
                    r'(?:<p align="center"><sub>[^<]*</sub></p>\n\n)?# [^\n]*\n\n(?:> \*[^\n]*\*\n\n)?',
                    "", md, count=1)

    def fig(m):
        cap = " ".join(x for x in (m.group(4), m.group(5)) if x)
        alt = html.escape(m.group(2), quote=True)
        w = int(m.group(3))
        cap_html = f"<figcaption>{cap}</figcaption>" if cap else ""
        return (f'<figure class="figure"><img src="{m.group(1)}" alt="{alt}" width="{w}" loading="lazy">'
                f"{cap_html}</figure>")
    md = re.sub(r"\n\n(> \*\*[▲◆])", "\n\n<!-- callout -->\n\n\\1", md)
    md = FIG_RE.sub(fig, md)
    md = re.sub(r'<p align="center"><img src="([^"]*ornaments/[^"]*)" alt="" width="\d+"></p>',
                r'<div class="ornament"><img src="\1" alt=""></div>', md)
    md = re.sub(r'<p align="center"><sub><i>(.*?)</i></sub></p>', r'<p class="small-center"><i>\1</i></p>', md)
    md = re.sub(r'<p align="center"><sub>(.*?)</sub></p>', r'<p class="kicker">\1</p>', md)
    md = re.sub(r'<p align="center"><i>(.*?)</i></p>', r'<p class="subtitle">\1</p>', md)
    return md


def dress_html(h: str) -> str:
    def mark(m):
        label = m.group(1)
        key = label.split("—")[0].split(",")[0].strip().lower().replace(" ", "-")
        tip = MARK_HELP.get(key, label.title())
        return f'<span class="mark mark-{key}" title="{html.escape(tip)}">{label}</span>'
    h = re.sub(r"<code>([A-Z][A-Z ,—\-₀-₉S]+)</code>", mark, h)

    def callout(m):
        kind = "practice" if "Practice" in m.group(1) else "audit"
        return (f'<aside class="callout {kind}"><p class="callout-label">{m.group(1)}</p>'
                f"{m.group(2)}</aside>")
    h = re.sub(r"<blockquote>\s*<p><strong>(▲ Practice|◆ Audit)</strong></p>(.*?)</blockquote>",
               callout, h, flags=re.S)
    h = re.sub(r"<blockquote>\s*<p><em>([^<]*(?:<(?!/em>)[^<]*)*)</em></p>\s*</blockquote>",
               r'<blockquote class="epigraph"><p>\1</p></blockquote>', h)
    h = re.sub(r"<ul>\s*<li>\[x\]", '<ul class="checks">\n<li>', h)
    h = h.replace("<li>[x] ", "<li>")
    h = h.replace("<li>[ ] ", '<li><input type="checkbox" disabled> ')
    h = re.sub(r'href="([^"#:]*?)README\.md(#[^"]*)?"', lambda m: f'href="{m.group(1)}index.html{m.group(2) or ""}"', h)
    h = re.sub(r'href="([^"#:]+?)\.md(#[^"]*)?"', lambda m: f'href="{m.group(1)}.html{m.group(2) or ""}"', h)
    h = h.replace(' align="center"', ' class="center"')
    return h


def render_md(md: str) -> str:
    return dress_html(markdown.markdown(md, extensions=["tables", "sane_lists"],
                                        output_format="html5"))


# ---------------------------------------------------------------------------
# page shell
# ---------------------------------------------------------------------------


def shell(out_rel, title, body, *, description="", accent="#c9a14a", prev=None, nxt=None,
          current=""):
    r = lambda p: rel(out_rel, p)  # noqa: E731
    nav_items = [("Contents", "book/index.html"), ("Lines", "book/1-the-lines/index.html"),
                 ("Manual", "book/2-the-manual/index.html"), ("Degree", "book/3-the-degree/index.html"),
                 ("Principle", "book/4-the-principle/index.html"), ("Proof", "book/5-the-proof/index.html"),
                 ("Workbook", "workbook/index.html"), ("Gallery", "art/index.html"),
                 ("Checks", "checks/index.html")]
    nav = "".join(
        f'<a href="{r(p)}"{" aria-current=page" if current == label else ""}>{label}</a>'
        for label, p in nav_items)
    links = ""
    if prev:
        links += f'<link rel="prev" href="{r(prev[0])}">'
    if nxt:
        links += f'<link rel="next" href="{r(nxt[0])}">'
    pager = ""
    if prev or nxt:
        pager = '<nav class="pager" aria-label="Turn the page">'
        if prev:
            thumb = f'<img src="{r(prev[2])}" alt="">' if prev[2] else ""
            pager += f'<a class="prev" href="{r(prev[0])}">{thumb}<div><small>← previous</small><span>{prev[1]}</span></div></a>'
        if nxt:
            thumb = f'<img src="{r(nxt[2])}" alt="">' if nxt[2] else ""
            pager += f'<a class="next" href="{r(nxt[0])}"><div><small>next →</small><span>{nxt[1]}</span></div>{thumb}</a>'
        pager += "</nav>"
    t = html.escape(title)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t} · The Geometry of Existence</title>
<meta name="description" content="{html.escape(description or 'The Geometry of Existence: A Manual for Life, in five levels, the highest at the end.')}">
<meta property="og:title" content="{t}">
<meta property="og:url" content="{SITE_URL}{out_rel}">
<meta property="og:image" content="{r('art/plates/p001-cover.png')}">
<meta name="theme-color" content="#14112e">
<link rel="icon" href="{r('assets/favicon.svg')}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r('assets/style.css')}">
{links}
<style>:root{{--accent:{accent}}}</style>
<script src="{r('assets/script.js')}" defer></script>
</head>
<body>
<div class="progress" aria-hidden="true"></div>
<header class="masthead">
  <a class="brand" href="{r('index.html')}">The Geometry <span class="dot">·</span> of Existence</a>
  <nav aria-label="Book">{nav}</nav>
  <a class="dl-link" href="{r(PDF_REL)}" download="{PDF_SAVE_AS}" aria-label="Download the book ({pdf_label()})">PDF ↓</a>
  <button class="theme-toggle" type="button" aria-label="Switch light or dark">◐</button>
</header>
<main>
{body}
{pager}
</main>
<footer class="colophon">
  <p>The Geometry of Existence: A Manual for Life · Massimo Vincent Panella · complete edition, 15 November 2026</p>
  <p><a href="{r(PDF_REL)}" download="{PDF_SAVE_AS}">Download the book ({pdf_label()})</a> ·
     <a href="{r('download.html')}">About the edition</a> ·
     <a href="{r('book/6-back-matter/04-corrections-and-open-accounts.html')}">Corrections and open accounts</a> ·
     <a href="{r('checks/index.html')}">The checks</a></p>
  <p>Nothing here is medical, psychological, or legal advice. The practices are yours to try and yours to stop.</p>
  <p>© Massimo Vincent Panella · licensed under <a rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a></p>
</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------


def plate_hero(out_rel, u, kicker_override=None):
    if not u["plates"]:
        return ""
    img = rel(out_rel, "art/" + u["plates"][0])
    kicker = kicker_override or u["kicker"]
    title = u["title"].split(" · ")[-1] if u["kind"] in ("level", "part") else u["title"]
    epi = f'<blockquote class="epigraph"><p>{html.escape(u["epigraph"])}</p></blockquote>' if u["epigraph"] else ""
    return (f'<section class="plate-hero"><img src="{img}" alt="{html.escape(kicker)} — {html.escape(title)}">'
            f'<p class="kicker">{html.escape(kicker)}</p><h1>{html.escape(title)}</h1>{epi}</section>')


def build_units(m):
    units = m["units"]
    levels = {lv["n"]: lv for lv in m["levels"]}
    for i, u in enumerate(units):
        md_rel = os.path.join("book", u["path"])
        out_rel = out_path_for(md_rel)
        md = open(os.path.join(ROOT, md_rel), encoding="utf-8").read()
        has_plate = bool(u["plates"])
        body_md = prepare_markdown(md, strip_plate=has_plate)
        # images in the Markdown point at ../../art; the site keeps the same tree
        body = render_md(body_md)
        lv = levels[u["level"]]
        crumb_bits = [lv["kicker"]] + ([lv["name"]] if u["level"] not in (0, 6) else [])
        pages = f"page {u['first']}" if u["first"] == u["last"] else f"pages {u['first']}–{u['last']}"
        crumb = f'<p class="crumb">{" · ".join(crumb_bits)} · {pages}</p>'
        hero = plate_hero(out_rel, u)
        extra = ""
        if u["kind"] == "level":
            members = [x for x in units if x["level"] == u["level"] and x is not u]
            cards = []
            for x in members:
                href = rel(out_rel, out_path_for(os.path.join("book", x["path"])))
                if x["plates"]:
                    im = f'<img src="{rel(out_rel, "art/" + x["plates"][0].replace("plates/", "plates/thumbs/"))}" alt="">'
                else:
                    im = ""
                lab = f"{x['number']} · {x['title']}" if x["number"] else x["title"]
                cards.append(f'<a href="{href}">{im}{html.escape(lab)}</a>')
            extra = '<h2>In this level</h2><div class="gallery">' + "".join(cards) + "</div>"
        content = (hero + '<article class="text">' + (crumb if not hero else "") + body + "</article>"
                   + (f'<div class="wide">{extra}</div>' if extra else ""))

        def link(x):
            if x is None:
                return None
            th = "art/" + x["plates"][0].replace("plates/", "plates/thumbs/") if x["plates"] else ""
            return (out_path_for(os.path.join("book", x["path"])), html.escape(x["title"]), th)
        prev = link(units[i - 1]) if i else None
        nxt = link(units[i + 1]) if i + 1 < len(units) else None
        current = {1: "Lines", 2: "Manual", 3: "Degree", 4: "Principle", 5: "Proof"}.get(u["level"], "")
        page = shell(out_rel, u["title"], content, description=u["epigraph"], accent=lv["accent"],
                     prev=prev, nxt=nxt, current=current)
        write(out_rel, page)


def build_contents(m):
    out_rel = "book/index.html"
    parts = ['<article class="text contents"><p class="crumb">Contents</p><h1>Contents</h1>'
             '<p class="subtitle">One book in five levels, the highest at the end.</p>']
    levels = {lv["n"]: lv for lv in m["levels"]}
    for n in sorted(levels):
        lv = levels[n]
        units = [u for u in m["units"] if u["level"] == n]
        if not units:
            continue
        opener = units[0]
        img = ""
        if opener["kind"] == "level" and opener["plates"]:
            img = (f'<a href="{rel(out_rel, out_path_for(os.path.join("book", opener["path"])))}">'
                   f'<img src="{rel(out_rel, "art/" + opener["plates"][0].replace("plates/", "plates/thumbs/"))}" alt=""></a>')
        items = []
        for u in units:
            if u["kind"] == "level":
                continue
            href = rel(out_rel, out_path_for(os.path.join("book", u["path"])))
            if u["kind"] == "part":
                items.append(f'<li class="part"><a href="{href}">{html.escape(u["title"])}</a></li>')
                continue
            num = f'<span class="num">{u["number"]}</span>' if u["number"] else ""
            items.append(f'<li class="{u["kind"]}"><a href="{href}">{num}{html.escape(u["title"])}</a>'
                         f'<span class="pg">{u["first"]}</span></li>')
        parts.append(f'<section class="level"><div>{img}</div><div><p class="kicker" style="text-align:left">{lv["kicker"]}</p>'
                     f'<h3>{html.escape(lv["name"])}</h3><p class="subtitle" style="text-align:left">{html.escape(lv["sub"])}</p>'
                     f'<ul>{"".join(items)}</ul></div></section>')
    parts.append("</article>")
    write(out_rel, shell(out_rel, "Contents", "".join(parts), current="Contents"))


def build_home(m):
    out_rel = "index.html"
    levels = [u for u in m["units"] if u["kind"] == "level"]
    names = {lv["n"]: lv for lv in m["levels"]}
    cards = []
    for u in levels:
        lv = names[u["level"]]
        cards.append(
            f'<a class="level-card" href="{out_path_for(os.path.join("book", u["path"]))}">'
            f'<img src="art/{u["plates"][0].replace("plates/", "plates/thumbs/")}" alt="{lv["kicker"]} — {lv["name"]}">'
            f'<p class="kicker">{lv["kicker"]}</p><span class="name">{html.escape(lv["name"])}</span>'
            f'<span class="sub">{html.escape(lv["sub"])}</span></a>')
    marks = "".join(
        f'<dt><span class="mark mark-{k}">{k.replace("-", " ").upper()}</span></dt><dd>{html.escape(v.split("— ", 1)[1])}</dd>'
        for k, v in MARK_HELP.items())
    body = f"""
<section class="home-hero">
  <img class="cover" src="art/plates/p001-cover.png" alt="The Geometry of Existence — A Manual for Life — cover">
  <p class="first-principle">Nothing gives legitimacy to existence except existence itself.</p>
  <p class="attr">The First Principle</p>
  <div class="actions">
    <a class="btn primary" href="book/1-the-lines/index.html">Begin with the Lines</a>
    <a class="btn" href="book/index.html">Contents</a>
    <a class="btn" href="{PDF_REL}" download="{PDF_SAVE_AS}" aria-label="Download the book ({pdf_label()})">Download the PDF ↓</a>
  </div>
</section>
<div class="three">
  <div><span class="n">1</span>Existence itself is sufficient.</div>
  <div><span class="n">2</span>Consciousness gives us the opportunity to understand it.</div>
  <div><span class="n">3</span>Connection gives us the opportunity to honor it.</div>
</div>
<h2>Five levels</h2>
<p class="subtitle">Each level says the same thing at a greater depth, and each is complete in itself.</p>
<div class="levels">{"".join(cards)}</div>
<section class="marks-legend">
  <h2>Five marks</h2>
  <p class="subtitle">Every claim in this book is one of five kinds, and the book tries never to let one kind pass for another.</p>
  <dl>{marks}</dl>
</section>
<section class="text" style="margin-top:3rem">
  <h2>One promise</h2>
  <p class="center">Every claim says what kind of claim it is. No claim is larger than its evidence. And every computation was run again — <a href="checks/index.html">run them yourself</a>.</p>
  <p class="center"><i>A book built that way is not ruined by an error. It is improved by one.</i></p>
</section>
"""
    write(out_rel, shell(out_rel, "A Manual for Life", body))


def build_gallery(m):
    out_rel = "art/index.html"
    page_unit = {}
    for u in m["units"]:
        for p in range(u["first"], u["last"] + 1):
            page_unit[p] = u
    plates = []
    for p in m["plates"]:
        u = page_unit.get(p["page"])
        href = rel(out_rel, out_path_for(os.path.join("book", u["path"]))) if u else "../index.html"
        cap = " · ".join(x for x in (p["kicker"], p["title"]) if x)
        plates.append(f'<a href="{href}"><img src="{p["file"].replace("plates/", "plates/thumbs/")}" alt="{html.escape(cap)}" loading="lazy">'
                      f'{html.escape(cap)}<br><small>page {p["page"]}</small></a>')
    figs = []
    for f in m["figures"]:
        u = page_unit.get(f["page"])
        href = rel(out_rel, out_path_for(os.path.join("book", u["path"]))) if u else "#"
        cap = f["caption"] or (u["title"] if u else "")
        figs.append(f'<a href="{href}"><img src="{f["file"]}" alt="{html.escape(cap)}" loading="lazy">'
                    f'<i>{html.escape(cap[:160])}</i><br><small>page {f["page"]}</small></a>')
    body = (f'<article class="text"><p class="crumb">The gallery</p><h1>The Gallery</h1>'
            f'<p class="subtitle">Every plate and figure in the complete edition. Every figure is computed from the book’s own mathematics.</p></article>'
            f'<h2>Plates</h2><div class="gallery">{"".join(plates)}</div>'
            f'<h2>Figures</h2><div class="gallery figs">{"".join(figs)}</div>')
    write(out_rel, shell(out_rel, "The Gallery", body, current="Gallery"))


def build_download(m):
    out_rel = "download.html"
    import hashlib
    data = open(os.path.join(ROOT, PDF_REL), "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    body = f"""
<section class="plate-hero">
  <a href="{PDF_REL}" download="{PDF_SAVE_AS}"><img src="art/plates/p001-cover.png" alt="The Geometry of Existence — cover. Select to download the PDF."></a>
  <p class="kicker">The complete edition · 15 November 2026</p>
  <h1>Download the Book</h1>
  <p><a class="btn primary" href="{PDF_REL}" download="{PDF_SAVE_AS}">Download the PDF ↓</a></p>
  <p class="small-center" style="color:#d6cdb6">{pdf_label()} · 5.5 × 8.5 in · fonts embedded</p>
</section>
<article class="text">
  <h2>Other ways to read it</h2>
  <p>The PDF is the edition of record, laid out for print. It is not a tagged PDF, so screen readers and
  reflowing readers handle it poorly. The same text, with every plate and figure described, is here:</p>
  <ul>
    <li><a href="book/index.html"><b>Read online</b></a> — this website: it reflows to any screen, follows light or dark mode,
    works with screen readers and browser zoom, and prints page by page.</li>
    <li><a href="https://github.com/Mavioni/THE-GEOMETRY-OF-EXISTENCE/tree/main/book"><b>The book in Markdown</b></a> — one file per chapter, on GitHub.</li>
  </ul>
  <h2>Check your copy</h2>
  <p>SHA-256 of the file:</p>
  <p><code style="word-break:break-all">{sha}</code></p>
  <p class="small-center">Run <code>sha256sum {os.path.basename(PDF_REL)}</code> (on macOS <code>shasum -a 256</code>) and compare.</p>
</article>
"""
    write(out_rel, shell(out_rel, "Download the Book", body,
                         description="Download The Geometry of Existence: A Manual for Life as a PDF."))


def build_markdown_folder(folder, title, current):
    src = os.path.join(ROOT, folder)
    files = sorted(f for f in os.listdir(src) if f.endswith(".md"))
    order = [f for f in files if f != "README.md"]
    for f in files:
        md_rel = os.path.join(folder, f)
        out_rel = out_path_for(md_rel)
        md = open(os.path.join(src, f), encoding="utf-8").read()
        body = render_md(prepare_markdown(md, strip_plate=False))
        prev = nxt = None
        if f in order:
            i = order.index(f)
            if i:
                prev = (out_path_for(os.path.join(folder, order[i - 1])), order[i - 1][3:-3].replace("-", " ").title(), "")
            if i + 1 < len(order):
                nxt = (out_path_for(os.path.join(folder, order[i + 1])), order[i + 1][3:-3].replace("-", " ").title(), "")
        page_title = title if f == "README.md" else re.search(r"^# (.+)$", md, flags=re.M).group(1)
        write(out_rel, shell(out_rel, page_title, f'<article class="text">{body}</article>',
                             prev=prev, nxt=nxt, current=current))


def write(out_rel, text):
    path = os.path.join(OUT, out_rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="10" fill="#14112e"/>
<g fill="none" stroke="#c9a14a" stroke-width="1.6"><circle cx="32" cy="32" r="24"/><circle cx="32" cy="32" r="16" stroke-opacity=".7"/><circle cx="32" cy="32" r="8" stroke-opacity=".5"/></g>
<circle cx="32" cy="32" r="3" fill="none" stroke="#efe6d0" stroke-width="1.6"/></svg>
"""


def main():
    m = load_manifest()
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "art"), os.path.join(OUT, "art"),
                    ignore=shutil.ignore_patterns("README.md"))
    shutil.copytree(os.path.join(ROOT, "edition"), os.path.join(OUT, "edition"),
                    ignore=shutil.ignore_patterns("README.md"))
    os.makedirs(os.path.join(OUT, "assets"))
    for f in ("style.css", "script.js"):
        shutil.copy(os.path.join(ROOT, "site", f), os.path.join(OUT, "assets", f))
    with open(os.path.join(OUT, "assets", "favicon.svg"), "w") as fh:
        fh.write(FAVICON)
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    build_home(m)
    build_contents(m)
    build_units(m)
    build_gallery(m)
    build_download(m)
    build_markdown_folder("workbook", "The Workbook", "Workbook")
    build_markdown_folder("checks", "The Checks", "Checks")
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"site written to {os.path.relpath(OUT, ROOT)}/ ({n} files)")


if __name__ == "__main__":
    main()
