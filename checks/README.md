# The Checks

*“Every figure here is computed, not sketched.”* (The Summit, p. 184)

The book's Summit rests on a small amount of real mathematics: balanced ternary, the arithmetic of “both must pass”, the game theory of repeated meetings, the Kamea of the Sun, rose curves, and the 240 roots of E8. This folder holds one program, [`verify_all.py`](verify_all.py), that computes all of it again from the definitions the book prints, and compares the results with the printed numbers.

It also checks what the book says about itself: that there are 240 teachings numbered straight through 26 chapters, that every chapter moves through the same nine steps in the same order, that each step carries the mark the book says it does, and that the reading cycle, the Index of Situations and the Ninety-Day Trial add up.

## Run it yourself

You need [Python 3](https://www.python.org/downloads/) and nothing else: the program uses only Python's standard library.

```sh
python3 checks/verify_all.py        # run every check
python3 checks/verify_all.py -v     # also show the computed values
python3 checks/verify_all.py -k e8  # run only the checks whose name contains "e8"
```

The same checks run automatically on GitHub every time the repository changes; the badge on the front page shows the latest result. The [website](https://mavioni.github.io/THE-GEOMETRY-OF-EXISTENCE/checks/) shows the output of the last run.

## What is checked

| The book says | Where | Checked how |
|---|---|---|
| 37 = 1101, 111 = 11010, −5 = T11 in balanced ternary, and every whole number has exactly one such spelling | II. The Trit, p. 185 | converts each number both ways; enumerates all 59,049 ten-digit spellings |
| base 3 is the most economical whole-number base, a little over five percent cheaper than base 2 | II, p. 186 | computes b / ln b and its minimum |
| with honesty 0.9 and kindness 0.2, the three ANDs give 0.20, 0.18 and 0.10, the average 0.55, and no AND exceeds its weakest input | III, p. 186; The Kept Middle, p. 18 | exact fractions, and a full 0.01 grid |
| tit-for-tat holds off the steady defector when w ≥ 1/2 and the alternator when w ≥ 2/3 | V, p. 188 | simulates the repeated game and checks the thresholds exactly |
| the logarithm turns multiplication into addition and loses nothing | VI, p. 189 | |
| the Kamea of the Sun: rows, columns and diagonals of 111, a total of 666, and the symmetry of its 18 complementary pairs | VII, pp. 189–190 | reads the square from the Markdown book and checks every line and pair |
| of the 66 pairs of the twelve odd stems, 58 share no factor and 8 generate a new order | VIII, p. 191 | enumerates the pairs; rotates the compound curves |
| the 240 roots of E8 fall into eight rings of thirty in the Coxeter plane, one ring at 0.618 of the outermost | IX, pp. 191–192 | builds the roots and the Coxeter element, projects, and measures the rings |
| 240 teachings in 26 chapters, nine movements each, with their marks | How to Carry This Book, pp. 9–10 | reads every chapter of the Markdown book |

Two statements are reported as **not run**, never as passed: that no six-by-six magic square can set every pair across its centre (a known theorem, cited rather than searched), and the habit-formation figures (measurements reported by their authors, with nothing to recompute).

## If a check fails

That is an error in the book or in this repository, and the book asks to be told. Open an issue with the form **A check failed** and paste the output of `python3 checks/verify_all.py -v`.
