# The Tools

Everything a reader sees in this repository is made from one file, [`edition/The-Geometry-of-Everything.pdf`](../edition/README.md), by the scripts in this folder. Nothing is retyped by hand.

```
edition/The-Geometry-of-Everything.pdf
        │
        ├─ extract.py ──────► book/**.md, book/manifest.json, art/paintings, art/plates, art/figures
        │                         │
        │                         ├─ build_pages.py ──► book/README.md, art/README.md, workbook/
        │                         │
        │                         └─ build_site.py ───► _site/  (the website)
        │
        └─ check_coverage.py ─► "every printed word reaches book/"
```

| Script | What it does | Needs |
|---|---|---|
| [`book.py`](book.py) | **The map of the book**: which pages become which file. Edit this when a new edition changes the page numbers. | nothing |
| [`extract.py`](extract.py) | Reads the typesetting itself (fonts, sizes, colours and positions) to decide what each line is: a title, a teaching, a table, a verse, a caption. Writes the Markdown book and renders every painting, plate and figure. | PyMuPDF, Pillow |
| [`build_pages.py`](build_pages.py) | Writes the contents page, the gallery and the workbook from `book/manifest.json`. | nothing |
| [`build_site.py`](build_site.py) | Turns the Markdown into the website, styled like the printed book, using [`site/style.css`](site/style.css) and [`site/script.js`](site/script.js). Runs the checks and puts their output on the site. | markdown |
| [`check_coverage.py`](check_coverage.py) | Compares every word printed in the PDF with the Markdown and lists anything missing. | PyMuPDF |

## Rebuilding

```sh
pip install -r requirements.txt
make all        # book, check, coverage and site, in that order
```

or one step at a time: `make book`, `make check`, `make coverage`, `make site`, `make serve`. Run `make help` to list them.

## A new edition

1. Replace `edition/The-Geometry-of-Everything.pdf` with the new PDF.
2. Update the page numbers in [`book.py`](book.py) (the PDF's own outline lists where each chapter starts).
3. Run `make all`. If `make coverage` reports missing words, the new layout has something the extractor does not yet recognise; the report names the file.
4. Update the size, page count and SHA-256 in [`edition/README.md`](../edition/README.md) and the root README.

## The website

[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) builds and publishes the website on every push to `main`. For it to run, **Settings → Pages → Source** must be set to **GitHub Actions** (a one-time setting).
