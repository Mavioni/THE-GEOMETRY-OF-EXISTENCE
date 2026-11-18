#!/usr/bin/env python3
"""Build the reading edition: a website made from the Markdown book.

    pip install markdown
    python3 tools/build_site.py            writes _site/
    python3 -m http.server -d _site 8000   read it at http://localhost:8000

Every page of book/, workbook/ and the gallery becomes a web page dressed like
the printed edition: cream pages, night plates, the Garamonds, and each Book
in its own colour. The site follows the reader's light or dark setting, and
the ← and → keys turn the page. GitHub publishes it from
.github/workflows/pages.yml.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
SITE_URL = "https://mavioni.github.io/THE-GEOMETRY-OF-EXISTENCE/"
MARK_NAMES = {"◆": "Commitment: a stance you choose and defend by argument",
              "●": "Evidence: a claim about how the world works, open to being proved wrong",
              "◇": "Analogy: a picture to think with; it shows a pattern, never proves one"}


def load():
    with open(os.path.join(ROOT, "book", "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def html_path(md_rel: str) -> str:
    base = md_rel[:-3]
    if os.path.basename(base) == "README":
        base = os.path.join(os.path.dirname(base), "index")
    return base + ".html"


def rel(src_out: str, dst_out: str) -> str:
    return os.path.relpath(os.path.join(OUT, dst_out), os.path.dirname(os.path.join(OUT, src_out))).replace(os.sep, "/")


def pdf_label(m) -> str:
    size = os.path.getsize(os.path.join(ROOT, m["pdf"])) / 1e6
    return f"PDF · {m['pages']} pages · {size:.1f} MB"


# ---------------------------------------------------------------------------
# Markdown -> HTML
# ---------------------------------------------------------------------------

def strip_footer(md: str) -> str:
    cut = md.rfind("\n---\n")
    return md[:cut] if cut != -1 and "<p align=\"center\">" in md[cut:] else md


def marks_in_text(h: str) -> str:
    """Wrap the three mark glyphs in text (not inside tags) with an explanation."""
    parts = re.split(r"(<[^>]+>)", h)
    for i, p in enumerate(parts):
        if p.startswith("<"):
            continue
        parts[i] = re.sub("[◆●◇]", lambda g: f'<span class="mark" title="{MARK_NAMES[g.group(0)]}">{g.group(0)}</span>', p)
    return "".join(parts)


def dress(h: str) -> str:
    h = h.replace(' align="center"', ' class="center"')
    # kicker, subtitle
    h = re.sub(r"<p><sub>([^<]*)</sub></p>", r'<p class="kicker">\1</p>', h)
    h = re.sub(r"(</h1>\s*)<p><em>([^<]*)</em></p>", r'\1<p class="subtitle">\2</p>', h, count=1)
    # chapter movements
    def movement(mm):
        roman, mark, name = mm.group(1), mm.group(2) or "", mm.group(3)
        mk = f'<span class="mark" title="{MARK_NAMES[mark]}">&#{ord(mark)};</span>' if mark else ""
        return f'<h2 class="movement" id="{slug(name)}"><span class="roman">{roman}</span>{mk}<span>{name}</span></h2>'
    h = re.sub(r"<h2>(I|II|III|IV|V|VI|VII|VIII|IX) · (?:([◆●◇]) )?([^<]+)</h2>", movement, h)
    # the creed question on a chapter's first page
    h = re.sub(r"<blockquote>\s*<p><strong>(PEACE|LOVE|UNITY|RESPECT|ALL FOUR)</strong>",
               r'<blockquote class="creed"><p><strong>\1</strong>', h)
    # epigraphs: a quotation followed by its source
    h = re.sub(r"<blockquote>(\s*<p><em>.*?</em></p>\s*<p>— .*?</p>\s*)</blockquote>",
               r'<blockquote class="epigraph">\1</blockquote>', h, flags=re.S)
    # the Reversal
    h = re.sub(r'(id="the-reversal".*?</h2>\s*)<blockquote>', r'\1<blockquote class="reversal">', h, flags=re.S)
    # the Witnesses
    h = re.sub(r'(id="the-witnesses".*?</h2>\s*)<ul>', r'\1<ul class="witnesses">', h, flags=re.S)
    # numbered lists keep the book's own numbers
    def ol(mm):
        start = int(mm.group(1) or 1)
        body = mm.group(2)
        n = [start - 1]

        def li(x):
            n[0] += 1
            return f'<li data-n="{n[0]}">'
        return f'<ol class="teachings" start="{start}">' + re.sub(r"<li>", li, body) + "</ol>"
    h = re.sub(r'<ol(?: start="(\d+)")?>(.*?)</ol>', ol, h, flags=re.S)
    # verse: paragraphs of italic lines broken with <br>
    h = re.sub(r"<p>(<em>[^\n]*?<br>\s*.*?)</p>", r'<p class="verse">\1</p>', h, flags=re.S)
    # tables scroll on small screens; grids of numbers are centred
    def table(mm):
        t = mm.group(0)
        cells = re.findall(r"<td[^>]*>(.*?)</td>", t, flags=re.S)
        numeric = cells and all(re.fullmatch(r"[\s☐\dT−=*<>/a-z·]*", c) for c in cells) and \
            sum(bool(re.search(r"\d", c)) for c in cells) > len(cells) / 2
        if numeric:
            t = t.replace("<table>", '<table class="grid">', 1)
        return f'<div class="table-wrap">{t}</div>'
    h = re.sub(r"<table>.*?</table>", table, h, flags=re.S)
    # links between Markdown files become links between pages
    h = re.sub(r'href="([^"#:]*?)README\.md(#[^"]*)?"', lambda mm: f'href="{mm.group(1)}index.html{mm.group(2) or ""}"', h)
    h = re.sub(r'href="([^"#:]+?)\.md(#[^"]*)?"', lambda mm: f'href="{mm.group(1)}.html{mm.group(2) or ""}"', h)
    h = re.sub(r'(<img [^>]*?)(/?>)', lambda mm: mm.group(1) + (' loading="lazy"' if "loading=" not in mm.group(1) else "") + mm.group(2), h)
    return marks_in_text(h)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def render(md: str) -> str:
    # python-markdown does not read Markdown inside an HTML block, so the
    # centred paragraphs the book uses are converted here
    # keep neighbouring quotations apart (python-markdown would join them)
    md = re.sub(r"(^>[^\n]*\n)\n(?=>)", r"\1\n<!-- -->\n\n", md, flags=re.M)
    md = re.sub(r'<p align="center">(\[.*?)</p>', lambda mm: "<p class=\"center\">" +
                markdown.markdown(mm.group(1))[3:-4] + "</p>", md)
    return dress(markdown.markdown(md, extensions=["tables", "sane_lists"], output_format="html"))


# ---------------------------------------------------------------------------
# The page shell
# ---------------------------------------------------------------------------

ICON = ('<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><circle cx="12" cy="12" r="8.5" '
        'fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" '
        'fill="currentColor"/></svg>')


def shell(m, out_rel, title, body, *, part=0, description="", prev=None, nxt=None, current="",
          wide=False, before_main=""):
    r = lambda p: rel(out_rel, p)  # noqa: E731
    nav = [("Contents", "book/index.html"),
           ("Situations", "book/7-at-the-back/04-index-of-situations.html"),
           ("Workbook", "workbook/index.html"), ("Gallery", "art/index.html"),
           ("Checks", "checks/index.html"), ("PDF", m["pdf"])]
    nav_html = "".join(f'<a href="{r(p)}"{" aria-current=\"page\"" if current == label else ""}>{label}</a>'
                       for label, p in nav)
    head_links = ""
    pager = ""
    if prev or nxt:
        pager = '<nav class="pager" aria-label="Turn the page">'
        if prev:
            head_links += f'<link rel="prev" href="{r(prev[0])}">'
            pager += f'<a class="prev" href="{r(prev[0])}"><small>← previous</small>{html.escape(prev[1])}</a>'
        if nxt:
            head_links += f'<link rel="next" href="{r(nxt[0])}">'
            pager += f'<a class="next" href="{r(nxt[0])}"><small>next →</small>{html.escape(nxt[1])}</a>'
        pager += "</nav>"
    t = html.escape(title)
    full_title = m["title"] if title == m["title"] else f"{t} · {m['title']}"
    desc = html.escape(description or f"{m['title']}: {m['subtitle']}, by {m['author']}.")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="book">
<meta property="og:url" content="{SITE_URL}{'' if out_rel == 'index.html' else out_rel}">
<meta property="og:image" content="{SITE_URL}art/paintings/cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE_URL}{'' if out_rel == 'index.html' else out_rel}">
<meta name="theme-color" content="#100e19">
<link rel="icon" href="{r('assets/favicon.svg')}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<link rel="stylesheet" href="{r('assets/style.css')}">
{head_links}
<script src="{r('assets/script.js')}"></script>
</head>
<body class="part-{part}">
<a class="skip" href="#text">Skip to the text</a>
<div class="progress" aria-hidden="true"></div>
<header class="top">
<a class="brand" href="{r('index.html')}">The Geometry of Everything</a>
<nav aria-label="The book">{nav_html}</nav>
<button class="theme-toggle" type="button" aria-label="Switch between light and dark">{ICON}</button>
</header>
{before_main}
<main id="text"{' class="wide"' if wide else ''}>
{body}
</main>
{pager}
<footer>
<p><i>{m['title']}</i> · {m['subtitle']} · {m['author']} · {m['edition']}</p>
<p><a href="{r(m['pdf'])}">Download the PDF</a> · <a href="https://github.com/Mavioni/THE-GEOMETRY-OF-EXISTENCE">The book on GitHub</a> ·
Licensed <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a></p>
</footer>
</body>
</html>
"""


def write(out_rel: str, text: str):
    path = os.path.join(OUT, out_rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def book_pages(m):
    units = m["units"]
    outs = [html_path(u["path"]) for u in units]
    for i, u in enumerate(units):
        out_rel = outs[i]
        md = strip_footer(read(u["path"]))
        prev = (outs[i - 1], units[i - 1]["title"]) if i else ("book/index.html", "Contents")
        nxt = (outs[i + 1], units[i + 1]["title"]) if i + 1 < len(units) else None
        before = ""
        if u["kind"] == "opener":
            part = m["parts"][u["part"]]
            painting = m["paintings"][str(part["plate"])]
            words = painting["words"]
            sub = words.replace(part["kicker"].upper(), "", 1).replace(part["name"], "", 1).strip()
            before = (f'<section class="night"><img class="painting" src="{rel(out_rel, painting["path"])}" '
                      f'alt="{html.escape(words)}" width="420">'
                      f'<h1 class="visually-hidden">{part["kicker"]}: {part["name"]}, {html.escape(sub)}</h1>'
                      f'<p class="lede">{html.escape(u.get("intro", ""))}</p></section>')
            # the Markdown repeats the painting, the kicker, the title and the intro
            md = re.sub(r"\A.*?^# [^\n]*\n\n(?:\*[^\n]*\*\n\n)?", "", md, flags=re.S | re.M)
            if not re.search(r"^\d+\. ", md, re.M):
                mine = [x for x in units if x["part"] == u["part"] and x is not u]
                md += "\n\n" + "\n".join(f"- [{x['title']}]({os.path.basename(x['path'])})" for x in mine)
        body = render(md)
        write(out_rel, shell(m, out_rel, u["title"], body, part=u["part"], prev=prev, nxt=nxt,
                             description=u.get("subtitle", ""), before_main=before,
                             current="Situations" if "index-of-situations" in out_rel else ""))
    return outs


def contents_page(m):
    out_rel = "book/index.html"
    md = strip_footer(read("book/README.md"))
    md = re.sub(r"\A<p align=\"center\"><img[^\n]*\n", "", md)
    body = render(md)
    write(out_rel, shell(m, out_rel, "Contents", body, current="Contents",
                         nxt=(html_path(m["units"][0]["path"]), m["units"][0]["title"])))


def home(m):
    out_rel = "index.html"
    r = lambda p: rel(out_rel, p)  # noqa: E731
    first = next(u for u in m["units"] if u["title"] == "How to Carry This Book")
    books = []
    for part in m["parts"]:
        if not part["plate"]:
            continue
        opener = next(u for u in m["units"] if u["part"] == part["n"] and u["kind"] == "opener")
        p = m["paintings"][str(part["plate"])]
        sub = p["words"].replace(part["kicker"].upper(), "", 1).replace(part["name"], "", 1).strip()
        books.append(f'<a href="{r(html_path(opener["path"]))}" class="part-{part["n"]}"><img src="{r(p["path"])}" '
                     f'alt="" loading="lazy"><small>{part["kicker"]}</small><span>{part["name"]}</span>'
                     f'<em>{html.escape(sub)}</em></a>')
    hero = f"""<section class="night">
<div class="hero">
<img class="painting" src="{r('art/paintings/cover.jpg')}" alt="The cover of The Geometry of Everything">
<div>
<p class="kicker" style="text-align:inherit">Existence · Consciousness · Relation</p>
<h1>The Geometry of Everything</h1>
<p class="sub">Earn Your Reality · A Manual for Life</p>
<p style="letter-spacing:.2em;font-family:'Cormorant Garamond',serif">MASSIMO VINCENT PANELLA</p>
<p class="lines">Existence needs no permission.<br>Understanding is an opportunity.<br>Connection is a responsibility you may choose.</p>
<p class="creed">Peace, love and unity are what you bring. Respect is what you prove.</p>
<div class="buttons">
<a class="button" href="{r(html_path(first['path']))}">Start reading</a>
<a class="button ghost" href="{r('book/index.html')}">Contents</a>
<a class="button ghost" href="{r(m['pdf'])}" download="The-Geometry-of-Everything.pdf">Download the PDF</a>
</div>
<p style="font-size:.85rem;color:#b9ad93;margin-top:.8rem">{pdf_label(m)} · free to share under CC BY-SA 4.0</p>
</div>
</div>
</section>"""
    body = f"""
<h2>Five Books and a Summit</h2>
<p>Two hundred and forty teachings in twenty-six chapters, rising like the shoulders of a mountain:
first the Ground of existence; then the Light of consciousness; then the Bond of relation; then the
Work by which you earn; then the Becoming by which you change. Above them stands the Summit: the
geometry beneath it all, and the test that tries it.</p>
<div class="books">{''.join(books)}</div>

<h2>Three marks</h2>
<p>Every claim in this book is one of three kinds, and the book tells you which.</p>
<div class="marks">
<div><b><span class="g">◆</span>Commitment.</b> A stance you choose and defend by argument, such as the floor of dignity. No experiment can prove a commitment, and this book never pretends one can.</div>
<div><b><span class="g">●</span>Evidence.</b> A claim about how the world works, backed by history or research, and open to being proved wrong.</div>
<div><b><span class="g">◇</span>Analogy.</b> A picture to think with, such as the cell that changes its kind, or the five scales of nature. An analogy shows a pattern. It never proves one.</div>
</div>

<h2>Ways to read it</h2>
<ul>
<li><a href="{r(html_path(first['path']))}">From the beginning</a>, one chapter a week: the book becomes a half-year's schooling.</li>
<li>On <a href="{r('book/7-at-the-back/02-the-monthly-reading-cycle.html')}">the monthly cycle</a>, one day's reading for each day of the month.</li>
<li>By <a href="{r('book/7-at-the-back/04-index-of-situations.html')}">what is happening in your life</a>: the Index of Situations.</li>
<li>As a test: run <a href="{r('book/7-at-the-back/01-the-ninety-day-trial.html')}">the Ninety-Day Trial</a> and judge the book by your own life. The <a href="{r('workbook/index.html')}">workbook</a> has a sheet for every chapter.</li>
<li>As an argument: <a href="{r('book/6-the-summit/02-how-this-book-could-be-wrong.html')}">How This Book Could Be Wrong</a> shows exactly where each claim could fail, and <a href="{r('checks/index.html')}">the checks</a> recompute its mathematics.</li>
</ul>
"""
    write(out_rel, shell(m, out_rel, m["title"], body, before_main=hero, wide=True))


def simple_page(m, md_rel, out_rel, title, current="", wide=False, keep_footer=False):
    md = read(md_rel)
    if not keep_footer:
        md = strip_footer(md)
    write(out_rel, shell(m, out_rel, title, render(md), current=current, wide=wide))


def checks_page(m):
    out_rel = "checks/index.html"
    run = subprocess.run([sys.executable, os.path.join(ROOT, "checks", "verify_all.py"), "-v"],
                         capture_output=True, text=True, cwd=ROOT)
    intro = render(strip_footer(read("checks/README.md")))
    body = (intro + "<h2>The checks, run when this site was built</h2>"
            f'<pre class="checks">{html.escape(run.stdout)}</pre>')
    write(out_rel, shell(m, out_rel, "The Checks", body, current="Checks"))
    if run.returncode != 0:
        raise SystemExit("verify_all.py failed; the site was not built")


def main():
    m = load()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "art"), os.path.join(OUT, "art"),
                    ignore=shutil.ignore_patterns("*.md"))
    os.makedirs(os.path.join(OUT, "edition"))
    shutil.copy(os.path.join(ROOT, m["pdf"]), os.path.join(OUT, m["pdf"]))
    assets = os.path.join(OUT, "assets")
    shutil.copytree(os.path.join(ROOT, "tools", "site"), assets)
    shutil.copy(os.path.join(ROOT, "art", "favicon.svg"), os.path.join(assets, "favicon.svg"))

    home(m)
    contents_page(m)
    book_pages(m)
    simple_page(m, "art/README.md", "art/index.html", "The Gallery", current="Gallery", wide=True)
    for f in sorted(os.listdir(os.path.join(ROOT, "workbook"))):
        if f.endswith(".md"):
            title = "The Workbook" if f == "README.md" else \
                re.sub(r"^# ", "", next(line for line in read(f"workbook/{f}").splitlines() if line.startswith("# ")))
            simple_page(m, f"workbook/{f}", html_path(f"workbook/{f}"), title, current="Workbook", keep_footer=True)
    checks_page(m)
    with open(os.path.join(OUT, ".nojekyll"), "w") as f:
        f.write("")
    n = sum(len(files) for _, _, files in os.walk(OUT))
    print(f"built _site/ ({n} files)")


if __name__ == "__main__":
    main()
