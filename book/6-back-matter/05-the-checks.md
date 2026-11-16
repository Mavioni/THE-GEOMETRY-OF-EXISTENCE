<p align="center"><sub>THE GEOMETRY OF EXISTENCE · AFTER THE LEVELS · PAGES 212–213</sub></p>

## The Checks

<p align="center"><i>every computation this book relies on, re-run for this edition</i></p>

Each line below is a computation that was run again while this edition was being made. All passed. The program that runs the first group accompanies the book as *verify\_all.py*; it uses nothing outside the standard Python library. The second group is the frozen workshop code, re-run unchanged.

- [x] Balanced ternary: each of the nine digit sums has exactly one (result, carry) with a + b = r + 3c

- [x] (+1) + (−1) = 0 with no carry, and zero is the only digit fixed by negation

- [x] Truncation: the discarded tail is always less than half the kept unit, for every word up to length 7 in radix 3

- [x] The same holds in balanced radix 5 and radix 7, so radix 3 is the smallest such radix, not the only one

- [x] Nearest rounding is not error-free on average: V = 1 truncated at k = 1 always errs by +1

- [x] Signed binary digits {−1, 0, +1} in radix 2: the value 1 is equally near 0 and 2, so unique nearest truncation fails there

- [x] Simplex identities: p₀ = 1 − q and p± = (q ± m)/2

- [x] Blume–Capel conditional zero probability at β = 1, Δ = 0: 0.3333, 0.2447, 0.1173 for local field 0, 1, 2

- [x] Three-spin model at βJ = βD = ln 2, βK = 2 ln 2: zero probability 32/49 aligned and 1/5 opposed

- [x] With K = 0 the same model gives 8/25 and 1/2, so the ordering reverses; the threshold is βK = ½ ln cosh 2βJ ≈ 0.3769

- [x] Consequence model at βχ = ln 2, other couplings off: 1/3 with no record, 1/2 with one zero on record; difference exactly 1/6

- [x] The log-odds shift equals βχ·ΔC for every tested J, D, K and boundary, and vanishes when χ = 0

- [x] The record stays bounded: 0 ≤ C<sub>t</sub> ≤ ρ<sup>t</sup> C₀ + (1 − ρ<sup>t</sup>)/(1 − ρ), on 200 random histories

- [x] Frozen record C = 1 with K = 0 and βχ = 2 ln 2: zero probability 32/49 aligned and 4/5 opposed

- [x] Both six-site graphs have nine edges and degree three at every site

- [x] Minimum energy −J with six ground states on the prism; −9J/2 with two on K₃,₃ (all 729 states of each)

- [x] Zero-site fraction 0.278246795804 on the prism and 0.001256340995 on K₃,₃; difference 0.276990454809

- [x] Probability of at least one zero site: 0.883127466845 and 0.007244882875

- [x] Two zeros frozen in advance on the prism: 3 of the 15 placements reach −J, and the mean best energy is +J/5

- [x] Dry-run arithmetic: (0.27485 − 0.001416667 − 0.276990454809) / 0.001500182 = −2.371

- [x] E₈: 112 + 128 = 240 roots, each of squared length 2, and every pair with inner product −1 sums to another root

- [x] Hausdorff dimension of the Cantor set: log 2 / log 3 = 0.630930

- [x] Learning-study table arithmetic: ternary leads binary by 1.04, 0.74, 0.78 and the frozen mask by 3.74, 1.93, 1.96; at width 16 the float gap is 1.40 and wider binary leads by 0.30

- [x] Graded “and” of 0.9 with 0.2: 0.2 (the smaller), 0.18 (the product), 0.1 (the strictest); the average is 0.55

- [x] Each of those three forms of “and” is at most the smaller input, across a full grid of values

- [x] Standard operators: “A and not-A” is never more than half true, and is exactly half true only at one half

- [x] Łukasiewicz operators: “A and not-A” is 0 and “A or not-A” is 1 at every degree

- [x] Axiom S₀ by model checking: a model where something exists and is not conscious; a model where two existing things differ in a further property; and all eight settings of E, C, R consistent with it, with L following E alone

- [x] Protected part: if P² = P and a change is confined to the complement of P, the protected part is exactly unchanged (100 random cases, exact arithmetic)

- [x] Workshop: sophonticism\_consequence\_test.py — all analytic identities and zero-coupling controls passed (1/3 → 1/2, difference 1/6).

- [x] Workshop: sixsite\_mcmc.py v1.1, seed 20261112 — dry run reproduced digit for digit; code sha256 ebf8f75b…f00c7.

- [x] Workshop: consequence\_mcmc.py — Parts A, B and C reproduced digit for digit; code sha256 b5c3882b…2663e.

- [x] This edition: all 240 roots of E₈ project to eight rings of thirty in the Coxeter plane (asserted in the figure code).


---

<p align="center">[← Corrections and Open Accounts](04-corrections-and-open-accounts.md) · [Contents](../README.md) · [PDF ↓](../../edition/README.md) · [Colophon →](06-colophon.md)</p>
