# The Geometry of Everything: repository tasks.  Run `make help` to list them.
PY ?= python3

.PHONY: help all book site serve check coverage clean

help:            ## list the tasks
	@grep -E '^[a-z]+:.*##' Makefile | sed 's/:.*##/\t/'

all: book check coverage site   ## rebuild everything and test it

book:            ## cut book/ and art/ from the PDF, then write the contents, gallery and workbook
	$(PY) tools/extract.py
	$(PY) tools/build_pages.py

check:           ## recompute every number the book relies on
	$(PY) checks/verify_all.py

coverage:        ## confirm every printed word of the PDF reaches book/
	$(PY) tools/check_coverage.py

site:            ## build the website into _site/
	$(PY) tools/build_site.py

serve: site      ## read the website at http://localhost:8000
	$(PY) -m http.server -d _site 8000

clean:           ## remove the built website
	rm -rf _site
