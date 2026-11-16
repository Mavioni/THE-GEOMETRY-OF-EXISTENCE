# The Geometry of Existence — repository tasks
PY ?= python3

.PHONY: all book indexes site serve check coverage clean

all: book site check

book:            ## re-cut book/ and art/ from the edition PDF, then rebuild the indexes
	$(PY) tools/extract_book.py
	$(PY) tools/build_indexes.py

indexes:         ## rebuild book/README.md, level strips, art/README.md, workbook/
	$(PY) tools/build_indexes.py

site:            ## build the reading edition into _site/
	$(PY) tools/build_site.py

serve: site      ## read it at http://localhost:8000
	$(PY) -m http.server -d _site 8000

check:           ## re-run every computation the book relies on
	$(PY) checks/verify_all.py

coverage:        ## confirm every printed word reaches the Markdown
	$(PY) tools/check_coverage.py

clean:
	rm -rf _site
