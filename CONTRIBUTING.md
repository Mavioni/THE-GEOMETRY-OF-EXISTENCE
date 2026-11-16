# Contributing

*"A book built that way is not ruined by an error. It is improved by one."*

This repository holds one book. Contributions are corrections, checks and results, made the way the book asks to be corrected: openly, with the kind of claim stated, and never silently.

## The rule of the edition

**Nothing is changed silently.** Every change to the book's text belongs in the next edition's list of corrections, dated and attributed. A pull request that changes what the book says must say what changed in its description, one line per change, in the form the book uses:

> Field Manual, Chapter Seven: "someone's else's" now reads "someone else's."

## What goes where

| You found… | Do this |
|---|---|
| A failing check | Open *A check failed* with the output of `python3 checks/verify_all.py -v`. |
| A claim with the wrong mark | Open *A mark is wrong*. Quote the sentence exactly. |
| An error in the book itself | Open *A correction to the text*. The PDF in `edition/` is the edition of record; it is not edited in place. |
| A difference between the Markdown and the PDF | That is a conversion error. Fix `tools/extract_book.py`, run `make book`, and check that the diff in `book/` is only the fix. |
| A result from running a protocol | Open *A test result*, whichever way it came out. |
| A result from doing a practice | Open *A practice result*, or keep it in your own fork of the [workbook](workbook/README.md). |

## Working on the repository

```sh
pip install -r requirements.txt
make book      # re-cut book/ and art/ from edition/ — never edit book/ by hand
make check     # the computations
make coverage  # every printed word reaches the Markdown
make serve     # the reading edition at http://localhost:8000
```

`book/`, `art/`, `workbook/` and the level contents are generated. Change the tools, not their output. `checks/verify_all.py` must keep to the Python standard library, as the book says it does.

## Marks

When you write about a claim — in an issue, a review, a commit — say which kind it is:

- **Lived** — a stance or a practice, tested only by doing it.
- **Argued** — reasons are given; no one is compelled.
- **Demonstrated** — follows from stated definitions, or established science within a stated domain.
- **Measured** — an observation, with its source.
- **On record** — a matter of published history.

No claim larger than its evidence.

## License of contributions

The book and this repository are licensed under [CC BY-SA 4.0](LICENSE). By contributing you agree that your contribution is licensed the same way, and that a correction you report may be listed, dated and attributed, in the next edition.
