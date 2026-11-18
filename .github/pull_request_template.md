## What changed

<!-- One line per change. If the book's text changed, write it the way an errata list would:
     Chapter 7, Where Attention Goes, p. 64: "…" now reads "…". -->

## Checks

- [ ] `python3 checks/verify_all.py` passes
- [ ] If the PDF or the tools changed: `make book` was run, and `python3 tools/check_coverage.py` reports 0 missing
- [ ] Nothing in `book/`, `art/` or `workbook/` was edited by hand (those folders are generated)
