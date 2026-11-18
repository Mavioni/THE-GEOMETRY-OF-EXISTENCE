# Contributing

*"A book that cannot be corrected is not a lamp but a tombstone."* (How to Carry This Book)

This repository holds one book. The most useful contributions are the ones the book itself asks for: corrections, tests and results.

## Without writing any code

You need a free GitHub account. Go to **[Issues → New issue](https://github.com/Mavioni/THE-GEOMETRY-OF-EXISTENCE/issues/new/choose)** and pick the form that fits:

| You found… | Use the form |
|---|---|
| an error of fact, a wrong date or source, a misquotation, a typing error | **A correction to the text** |
| a claim carrying the wrong mark (◆ commitment, ● evidence, ◇ analogy) | **A mark is wrong** |
| a check in `checks/verify_all.py` that fails | **A check failed** |
| evidence for or against one of the twelve predictions | **A prediction tested** |
| the result of running the Ninety-Day Trial on your own life | **A Ninety-Day Trial result** |

The book's promise: *each edition will publish what changed and why. A claim that fails is removed, and the removal is recorded, never silently erased.* Corrections you report may be listed, with your name if you agree, in the next edition.

## Changing the repository

**The PDF is the source of everything.** The folders `book/`, `art/` and `workbook/` are generated from `edition/The-Geometry-of-Everything.pdf`, so they are never edited by hand: change the tools, or change the PDF, and regenerate. A correction to the book's text is made in the next edition of the PDF, not in the Markdown.

```sh
pip install -r requirements.txt
make book       # cut book/ and art/ from the PDF; write the contents, gallery and workbook
make check      # recompute the mathematics (standard library only)
make coverage   # confirm every printed word reaches book/
make serve      # read the website at http://localhost:8000
```

[`tools/README.md`](tools/README.md) explains each script. Two rules keep the repository honest:

- `checks/verify_all.py` uses only the Python standard library, so anyone can run it.
- After `make book`, `make coverage` must report **0 missing**. The automatic checks on GitHub also re-cut the PDF and fail if the committed Markdown differs.

When you open a pull request, list what changed, one line per change.

## License

The book and this repository are licensed under [CC BY-SA 4.0](LICENSE). By contributing you agree that your contribution is licensed the same way.
