#!/usr/bin/env python3
"""verify_all.py: re-run every computation The Geometry of Everything relies on.

    python3 checks/verify_all.py          run everything
    python3 checks/verify_all.py -v       also show each computed value
    python3 checks/verify_all.py -k kamea run only the checks whose name contains "kamea"

The Summit of the book ("The Geometry of Everything", pages 185-193) says that
every figure there "is computed, not sketched" and that "every sum has been
checked". This program checks them again, from the definitions printed in the
book, using nothing but the Python standard library.

It also checks what the book says about itself: 240 teachings numbered
straight through 26 chapters, nine movements in every chapter, the mark each
movement carries, the monthly reading cycle and the Index of Situations. Those
checks read the Markdown book in book/, so they test the text as printed.

Each check names the page it answers to. A failure is an error in the book or
in this repository. Report it with the issue form "A check failed".
"""
from __future__ import annotations

import argparse
import cmath
import itertools
import math
import os
import re
import sys
from fractions import Fraction as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book")
CHECKS = []


def check(name, where):
    def deco(fn):
        CHECKS.append((name, where, fn))
        return fn
    return deco


class Notes:
    def __init__(self):
        self.lines = []

    def __call__(self, msg):
        self.lines.append(msg)


def close(a, b, tol):
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# Reading the Markdown book
# ---------------------------------------------------------------------------

def read(rel):
    with open(os.path.join(BOOK, rel), encoding="utf-8") as f:
        return f.read()


def chapters():
    """[(number, path, text)] for the twenty-six chapters, in order."""
    out = []
    for d in sorted(os.listdir(BOOK)):
        if not re.match(r"[1-5]-", d):
            continue
        for f in sorted(os.listdir(os.path.join(BOOK, d))):
            m = re.match(r"(\d\d)-", f)
            if m:
                out.append((int(m.group(1)), f"{d}/{f}", read(f"{d}/{f}")))
    return sorted(out)


def section(text, heading_regex):
    """The text from a heading matching the regex to the next heading of that level."""
    m = re.search(r"^(#+) " + heading_regex + r".*$", text, re.M)
    if not m:
        raise AssertionError(f"no heading matching {heading_regex!r}")
    level = len(m.group(1))
    rest = text[m.end():]
    n = re.search(r"^#{1,%d} " % level, rest, re.M)
    return rest[: n.start()] if n else rest


def table(text):
    """Rows of the first Markdown table in the text, as lists of plain strings."""
    rows = []
    for line in text.splitlines():
        if re.match(r"^\|(-+\|)+$", line):
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            rows.append([re.sub(r"[*\\]|\[|\]\([^)]*\)", "", c).strip() for c in cells])
        elif rows:
            break
    return rows


# ---------------------------------------------------------------------------
# II. The Trit  (p. 185)
# ---------------------------------------------------------------------------

def to_balanced_ternary(n: int) -> str:
    """Spell n with the digits T (−1), 0 and 1."""
    if n == 0:
        return "0"
    digits = []
    while n:
        r = n % 3
        if r == 2:
            digits.append("T")
            n = n // 3 + 1
        else:
            digits.append(str(r))
            n //= 3
    return "".join(reversed(digits))


def from_balanced_ternary(s: str) -> int:
    v = 0
    for ch in s:
        v = 3 * v + {"T": -1, "0": 0, "1": 1}[ch]
    return v


@check("balanced ternary: 37 = 1101, 111 = 11010, −5 = T11, as printed", "II. The Trit, p. 185")
def _(note):
    want = {37: "1101", 111: "11010", -5: "T11"}
    for n, s in want.items():
        assert to_balanced_ternary(n) == s, (n, to_balanced_ternary(n))
        assert from_balanced_ternary(s) == n
    # the table in the book, read from the Markdown
    rows = table(section(read("6-the-summit/01-the-geometry-of-everything.md"), r"II\. The Trit"))
    head, body = rows[0], rows[1:]
    weights = [int(x) for x in head[1:]]
    assert weights == [81, 27, 9, 3, 1], weights
    for r in body:
        n = int(r[0].replace("=", "").replace("−", "-"))
        value = sum(w * {"T": -1, "0": 0, "1": 1, "": 0}[d] for w, d in zip(weights, r[1:]))
        assert value == n, (r, value)
    note("the printed table spells 37, 111 and −5 correctly")
    # the identities named beside it
    assert 27 + 9 + 1 == 37 and 81 + 27 + 3 == 111 and -9 + 3 + 1 == -5


@check("every whole number has exactly one balanced-ternary spelling (all of −29 524 … 29 524)", "II. The Trit, p. 185")
def _(note):
    k = 10                                   # all spellings of up to ten digits
    seen = {}
    for digits in itertools.product((-1, 0, 1), repeat=k):
        v = 0
        for d in digits:
            v = 3 * v + d
        assert v not in seen, v
        seen[v] = digits
    half = (3 ** k - 1) // 2
    assert sorted(seen) == list(range(-half, half + 1))
    note(f"3^{k} = {3 ** k} spellings, each a different number, covering every number from −{half} to {half}")


@check("cost b / ln b: least at e; base 2 ≈ 2.885, base 3 ≈ 2.731, base 4 = base 2; three is a little over 5% cheaper", "II. The Trit, p. 186")
def _(note):
    def cost(b):
        return b / math.log(b)
    assert close(cost(2), 2.885, 5e-4) and close(cost(3), 2.731, 5e-4)
    assert close(cost(4), cost(2), 1e-12)          # 4 / ln 4 = 2 / ln 2 exactly
    # the minimum of b / ln b is at b = e: the derivative (ln b − 1) / ln² b is zero there
    grid = [1.5 + i / 10000 for i in range(30000)]
    b_min = min(grid, key=cost)
    assert close(b_min, math.e, 1e-3), b_min
    assert min((2, 3, 4, 5, 6), key=cost) == 3
    saving = 1 - cost(3) / cost(2)
    assert 0.05 < saving < 0.06, saving
    note(f"saving of base 3 over base 2: {saving:.2%}; e = {math.e:.3f}")


# ---------------------------------------------------------------------------
# III. Degrees and the Third Axis  (p. 186)
# ---------------------------------------------------------------------------

T_NORMS = {
    "minimum (Zadeh)": lambda a, b: min(a, b),
    "product": lambda a, b: a * b,
    "Łukasiewicz": lambda a, b: max(F(0), a + b - 1),
}


@check("honesty 0.9 AND kindness 0.2: minimum 0.20, product 0.18, Łukasiewicz 0.10; the average 0.55", "III, p. 186; The Kept Middle, p. 18")
def _(note):
    a, b = F(9, 10), F(2, 10)
    got = [f(a, b) for f in T_NORMS.values()]
    assert got == [F(20, 100), F(18, 100), F(10, 100)], got
    assert (a + b) / 2 == F(55, 100)
    note("0.20, 0.18, 0.10 — and 0.55 for the average")


@check("every one of the three ANDs is at most the smaller input (checked on a 0.01 grid)", "III, p. 186")
def _(note):
    grid = [F(i, 100) for i in range(101)]
    for f in T_NORMS.values():
        for a in grid:
            for b in grid:
                v = f(a, b)
                assert 0 <= v <= min(a, b), (a, b, v)
                assert f(a, 1) == a                      # 1 is neutral
                assert f(a, b) == f(b, a)                # order does not matter
    note(f"{len(grid) ** 2 * 3} values checked")


# ---------------------------------------------------------------------------
# V. Why Earned Power Holds When the Game Repeats  (pp. 187-189)
# ---------------------------------------------------------------------------

T_, R_, P_, S_ = 5, 3, 1, 0          # temptation, reward, punishment, sucker


def play(a, b, w, rounds=4000):
    """Discounted payoff to strategy a against b; w is the chance of meeting again."""
    hist_a, hist_b, total, weight = [], [], 0.0, 1.0
    pay = {("C", "C"): R_, ("C", "D"): S_, ("D", "C"): T_, ("D", "D"): P_}
    for _ in range(rounds):
        x, y = a(hist_a, hist_b), b(hist_b, hist_a)
        total += weight * pay[(x, y)]
        hist_a.append(x)
        hist_b.append(y)
        weight *= w
    return total


def tit_for_tat(mine, theirs):
    return theirs[-1] if theirs else "C"


def always_defect(mine, theirs):
    return "D"


def alternator(mine, theirs):
    return "D" if len(mine) % 2 == 0 else "C"


@check("the classic payoffs make a prisoner's dilemma: 5 > 3 > 1 > 0 and 2·3 > 5 + 0", "V, p. 188")
def _(note):
    assert T_ > R_ > P_ > S_ and 2 * R_ > T_ + S_


@check("tit-for-tat earns 3/(1−w); the defector 5 + w/(1−w); the alternator 5/(1−w²)", "V, p. 188")
def _(note):
    for w in (0.3, 0.5, 0.6, 2 / 3, 0.8, 0.9):
        assert close(play(tit_for_tat, tit_for_tat, w), 3 / (1 - w), 1e-6)
        assert close(play(always_defect, tit_for_tat, w), 5 + w / (1 - w), 1e-6)
        assert close(play(alternator, tit_for_tat, w), 5 / (1 - w * w), 1e-6)
    note("simulated games agree with the three formulas at w = 0.3 … 0.9")


@check("the steady defector is held off exactly when w ≥ 1/2; the alternator exactly when w ≥ 2/3", "V, p. 188")
def _(note):
    assert F(T_ - R_, T_ - P_) == F(1, 2)
    assert F(T_ - R_, R_ - S_) == F(2, 3)
    for i in range(1, 1000):
        w = F(i, 1000)
        tft = F(3) / (1 - w)
        defector = 5 + w / (1 - w)
        alt = F(5) / (1 - w * w)
        assert (tft >= defector) == (w >= F(1, 2)), w
        assert (tft >= alt) == (w >= F(2, 3)), w
    note("exact arithmetic on every w = 0.001 … 0.999")


@check("a lone cooperator among defectors still loses", "V, p. 188")
def _(note):
    for w in (0.5, 0.9, 0.99):
        assert play(tit_for_tat, always_defect, w) < play(always_defect, always_defect, w)


# ---------------------------------------------------------------------------
# VI. Isomorphism  (p. 189)
# ---------------------------------------------------------------------------

@check("the logarithm turns multiplication into addition, one-to-one", "VI, p. 189")
def _(note):
    xs = [F(1, 7), F(1, 2), 1, 2, 3, F(22, 7), 10, 1000]
    for x in xs:
        for y in xs:
            assert close(math.log(x * y), math.log(x) + math.log(y), 1e-12)
    logs = [math.log(x) for x in xs]
    assert len(set(logs)) == len(xs)               # nothing is lost: no two collide
    # the figure: 1, 2, 4, 8 under ×2 go to 0, 1, 2, 3 under +1 (log base 2)
    assert [math.log2(x) for x in (1, 2, 4, 8)] == [0, 1, 2, 3]


# ---------------------------------------------------------------------------
# VII. The Kamea of the Sun  (pp. 189-190)
# ---------------------------------------------------------------------------

def kamea():
    rows = table(section(read("6-the-summit/01-the-geometry-of-everything.md"), r"VII\. The Kamea"))
    sq = [[int(x) for x in r] for r in rows if all(r)]
    assert len(sq) == 6 and all(len(r) == 6 for r in sq), sq
    return sq


@check("the Kamea of the Sun: 1 to 36 once each; every row, column and diagonal 111; the whole 666", "VII, p. 190")
def _(note):
    sq = kamea()
    flat = [x for r in sq for x in r]
    assert sorted(flat) == list(range(1, 37))
    lines = sq + [list(c) for c in zip(*sq)] + \
        [[sq[i][i] for i in range(6)], [sq[i][5 - i] for i in range(6)]]
    assert all(sum(line) == 111 for line in lines), [sum(line) for line in lines]
    assert sum(flat) == 666
    note(f"{len(lines)} lines, each 111")


@check("its 18 pairs summing to 37: the 12 diagonal numbers face theirs across the centre, the other 24 across a midline", "VII, p. 190")
def _(note):
    sq = kamea()
    pos = {sq[i][j]: (i, j) for i in range(6) for j in range(6)}
    centre = mid_v = mid_h = 0
    for a in range(1, 19):
        (i, j), (k, l) = pos[a], pos[37 - a]
        on_diag = i == j or i + j == 5
        if (k, l) == (5 - i, 5 - j):
            centre += 2
            assert on_diag and (k == l or k + l == 5)
        elif (k, l) == (i, 5 - j):
            mid_v += 2
            assert not on_diag
        elif (k, l) == (5 - i, j):
            mid_h += 2
            assert not on_diag
        else:
            raise AssertionError(f"{a} and {37 - a} are not set symmetrically")
    assert centre == 12 and mid_v + mid_h == 24, (centre, mid_v, mid_h)
    note(f"across the centre {centre}, across the vertical midline {mid_v}, across the horizontal {mid_h}")


# ---------------------------------------------------------------------------
# VIII. The Rose and the Law of the Third  (pp. 190-191)
# ---------------------------------------------------------------------------

STEMS = list(range(1, 24, 2))               # the twelve odd orders 1, 3, … 23


def rose_symmetry(k1, k2):
    """The rotational order of the curve r = cos(k1·θ) + cos(k2·θ).

    Turning the curve by α maps it onto itself when r(θ + α) = r(θ) for every θ,
    or when r(θ + α + π) = −r(θ) for every θ (the same point, reached with a
    negative radius). Returns the largest n ≤ 30 for which α = 2π/n works.
    """
    def r(t):
        return math.cos(k1 * t) + math.cos(k2 * t)
    ts = [i * 0.0137 for i in range(2000)]
    best = 1
    for n in range(2, 31):
        a = 2 * math.pi / n
        if all(abs(r(t + a) - r(t)) < 1e-9 for t in ts) or \
                all(abs(r(t + a + math.pi) + r(t)) < 1e-9 for t in ts):
            best = n
    return best


@check("twelve odd stems make 66 pairs; 58 share no factor; 8 share one: 3·9, 3·15, 3·21, 5·15, 7·21, 9·15, 9·21, 15·21", "VIII, p. 191")
def _(note):
    assert len(STEMS) == 12 and STEMS[-1] == 23
    pairs = list(itertools.combinations(STEMS, 2))
    assert len(pairs) == 66
    sharing = [(a, b) for a, b in pairs if math.gcd(a, b) > 1]
    assert sharing == [(3, 9), (3, 15), (3, 21), (5, 15), (7, 21), (9, 15), (9, 21), (15, 21)], sharing
    assert len(pairs) - len(sharing) == 58


@check("a rose cos(kθ) with odd k has k petals' symmetry; a compound's rotational order is the gcd of its orders", "VIII, p. 191")
def _(note):
    for k in (3, 5, 7):
        assert rose_symmetry(k, k) == k
    tested = [(3, 9), (3, 15), (5, 15), (9, 15), (3, 5), (5, 7), (7, 9), (1, 3)]
    for a, b in tested:
        assert rose_symmetry(a, b) == math.gcd(a, b), (a, b, rose_symmetry(a, b))
    # and every compound keeps a mirror: r(−θ) = r(θ)
    for a, b in tested:
        for i in range(50):
            t = i / 7
            assert close(math.cos(a * t) + math.cos(b * t), math.cos(-a * t) + math.cos(-b * t), 1e-12)
    note("rotations tested for " + ", ".join(f"{a}·{b}" for a, b in tested))


# ---------------------------------------------------------------------------
# IX. The Ground Ring  (pp. 191-192)
# ---------------------------------------------------------------------------

def e8_roots():
    roots = []
    for i, j in itertools.combinations(range(8), 2):
        for si, sj in itertools.product((-1, 1), repeat=2):
            v = [F(0)] * 8
            v[i], v[j] = F(si), F(sj)
            roots.append(tuple(v))
    for signs in itertools.product((-1, 1), repeat=8):
        if signs.count(-1) % 2 == 0:
            roots.append(tuple(F(s, 2) for s in signs))
    return roots


def _solve_null(M):
    """A non-zero vector in the null space of a (numerically) singular complex matrix."""
    n = len(M)
    A = [row[:] for row in M]
    piv_cols, r_ = [], 0
    for c in range(n):
        p = max(range(r_, n), key=lambda i: abs(A[i][c]))
        if abs(A[p][c]) < 1e-9:
            continue
        A[r_], A[p] = A[p], A[r_]
        pv = A[r_][c]
        A[r_] = [x / pv for x in A[r_]]
        for i in range(n):
            if i != r_ and abs(A[i][c]) > 0:
                f = A[i][c]
                A[i] = [x - f * y for x, y in zip(A[i], A[r_])]
        piv_cols.append(c)
        r_ += 1
    free = [c for c in range(n) if c not in piv_cols][0]
    v = [0j] * n
    v[free] = 1
    for i, c in enumerate(piv_cols):
        v[c] = -A[i][free]
    return v


def coxeter_rings():
    roots = e8_roots()
    simple = [
        (F(1, 2), F(-1, 2), F(-1, 2), F(-1, 2), F(-1, 2), F(-1, 2), F(-1, 2), F(1, 2)),
        (1, 1, 0, 0, 0, 0, 0, 0), (-1, 1, 0, 0, 0, 0, 0, 0), (0, -1, 1, 0, 0, 0, 0, 0),
        (0, 0, -1, 1, 0, 0, 0, 0), (0, 0, 0, -1, 1, 0, 0, 0), (0, 0, 0, 0, -1, 1, 0, 0),
        (0, 0, 0, 0, 0, -1, 1, 0),
    ]
    simple = [tuple(F(x) for x in s) for s in simple]
    assert all(s in set(roots) for s in simple)

    def refl(a):
        return [[(1 if i == j else 0) - a[i] * a[j] for j in range(8)] for i in range(8)]

    def mul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(8)) for j in range(8)] for i in range(8)]

    W = refl(simple[0])
    for s in simple[1:]:
        W = mul(W, refl(s))
    P, order = W, 1
    while not all(P[i][j] == (1 if i == j else 0) for i in range(8) for j in range(8)):
        P, order = mul(P, W), order + 1
    lam = cmath.exp(2j * math.pi / order)
    M = [[complex(W[i][j]) - (lam if i == j else 0) for j in range(8)] for i in range(8)]
    v = _solve_null(M)
    re_, im_ = [x.real for x in v], [x.imag for x in v]
    nr = math.sqrt(sum(x * x for x in re_))
    e1 = [x / nr for x in re_]
    im_ = [b - sum(p * q for p, q in zip(im_, e1)) * a for a, b in zip(e1, im_)]
    ni = math.sqrt(sum(x * x for x in im_))
    e2 = [x / ni for x in im_]
    radii = sorted(math.hypot(sum(float(a) * b for a, b in zip(rt, e1)),
                              sum(float(a) * b for a, b in zip(rt, e2))) for rt in roots)
    rings = []
    for x in radii:
        if rings and abs(rings[-1][0] - x) < 1e-6:
            rings[-1][1] += 1
        else:
            rings.append([x, 1])
    return roots, order, rings


@check("E8: 240 roots in eight dimensions, each of squared length 2", "IX, p. 191")
def _(note):
    roots = e8_roots()
    assert len(roots) == len(set(roots)) == 240
    assert all(sum(x * x for x in v) == 2 for v in roots)
    assert all(len(v) == 8 for v in roots)


@check("in the Coxeter plane the 240 roots fall into eight rings of thirty; one ring lies at 0.618 of the outermost", "IX, pp. 191-192")
def _(note):
    _, order, rings = coxeter_rings()
    assert order == 30, order                                 # the Coxeter number of E8
    assert [n for _, n in rings] == [30] * 8, rings
    outer = rings[-1][0]
    ratios = [r / outer for r, _ in rings]
    golden = (math.sqrt(5) - 1) / 2                            # 1/φ = 0.6180…
    assert any(close(x, golden, 1e-9) for x in ratios), ratios
    note("ring radii / outermost: " + ", ".join(f"{x:.4f}" for x in ratios))


# ---------------------------------------------------------------------------
# What the book says about itself
# ---------------------------------------------------------------------------

MOVEMENTS = [("I", "◆", "The Teaching"), ("II", "◇", "The Five Scales"), ("III", "", "The Witnesses"),
             ("IV", "●", "The Tale"), ("V", "●", "The Energy"), ("VI", "", "The Reversal"),
             ("VII", "◆", "The Practice"), ("VIII", "", "The Ledger"), ("IX", "", "The Song")]


@check("26 chapters; 240 teachings numbered straight through, 1 to 240", "How to Carry This Book, p. 10; Colophon, p. 216")
def _(note):
    chs = chapters()
    assert [n for n, _, _ in chs] == list(range(1, 27)), [n for n, _, _ in chs]
    numbers = []
    for n, path, text in chs:
        teaching = section(text, r"I · ◆ The Teaching")
        numbers += [int(x) for x in re.findall(r"^(\d+)\. ", teaching, re.M)]
    assert numbers == list(range(1, 241)), numbers[:5]
    note("240 teachings in order")


@check("every chapter moves in the same nine steps, in the same order", "How to Carry This Book, p. 10; VI, p. 189")
def _(note):
    for n, path, text in chapters():
        got = re.findall(r"^## (I|II|III|IV|V|VI|VII|VIII|IX) · (?:([◆●◇]) )?(.+)$", text, re.M)
        want = [(r, "", name) for r, _, name in MOVEMENTS]
        assert [(r, "", nm) for r, _, nm in got] == want, (path, got)


@check("in every chapter the Teaching and the Practice are commitments ◆, the Five Scales analogies ◇, the Tale and the Energy evidence ●", "How to Carry This Book, p. 9")
def _(note):
    for n, path, text in chapters():
        got = re.findall(r"^## (I|II|III|IV|V|VI|VII|VIII|IX) · (?:([◆●◇]) )?(.+)$", text, re.M)
        assert [(r, m, nm) for r, m, nm in got] == MOVEMENTS, (path, got)


@check("every chapter: five scales (cell to cosmos), a daily and a weekly practice, four ledger questions (peace, love, unity, respect)", "How to Carry This Book, p. 10")
def _(note):
    for n, path, text in chapters():
        scales = [r[0] for r in table(section(text, r"II · ◇ The Five Scales")) if r[0]]
        practice = [r[0] for r in table(section(text, r"VII · ◆ The Practice")) if r[0]]
        ledger = [r[0] for r in table(section(text, r"VIII · The Ledger")) if r[0]]
        assert scales == ["CELL", "SELF", "BOND", "COMMUNITY", "COSMOS"], (path, scales)
        assert practice == ["DAILY", "WEEKLY"], (path, practice)
        assert ledger == ["PEACE", "LOVE", "UNITY", "RESPECT"], (path, ledger)


@check("the monthly reading cycle: 31 days, every chapter on its own day", "The Monthly Reading Cycle, p. 207")
def _(note):
    text = read("7-at-the-back/02-the-monthly-reading-cycle.md")
    days = re.findall(r"^(\d+)\. (.+)$", text, re.M)
    assert [int(d) for d, _ in days] == list(range(1, 32))
    chapter_days = {}
    for d, line in days:
        m = re.match(r"(\d+) · ", line)
        if m:
            chapter_days[int(m.group(1))] = int(d)
    assert chapter_days == {c: c + 3 for c in range(1, 27)}, chapter_days


@check("the Index of Situations points only at chapters that exist, and its links reach them", "Index of Situations, pp. 211-212")
def _(note):
    text = read("7-at-the-back/04-index-of-situations.md")
    links = re.findall(r"\[(\d+)\]\(([^)]+)\)", text)
    assert len(links) > 50
    for n, target in links:
        assert 1 <= int(n) <= 26
        path = os.path.normpath(os.path.join(BOOK, "7-at-the-back", target))
        assert os.path.exists(path) and os.path.basename(path).startswith(f"{int(n):02d}-"), (n, target)
    note(f"{len(links)} references")


@check("the Ninety-Day Trial's stages cover days 1 to 90 without a gap, with one pause week of seven days", "The Ninety-Day Trial, pp. 205-206")
def _(note):
    text = read("7-at-the-back/01-the-ninety-day-trial.md")
    spans = [(int(a), int(b)) for a, b in re.findall(r"DAYS (\d+)–(\d+)", text)]
    assert spans == [(1, 30), (31, 37), (38, 90)], spans
    assert spans[1][1] - spans[1][0] + 1 == 7
    grid = [int(x) for x in re.findall(r"\| (\d+) (?=\|)", section(text, r"Ninety Days, Marked"))]
    assert grid == list(range(1, 91)), grid[:12]


@check("twelve predictions, numbered 1 to 12", "How This Book Could Be Wrong, pp. 200-201")
def _(note):
    text = section(read("6-the-summit/02-how-this-book-could-be-wrong.md"), r"Twelve predictions")
    assert [int(x) for x in re.findall(r"^(\d+)\. ", text, re.M)] == list(range(1, 13))


NOT_RUN = [
    ("no six-by-six magic square can place every pair directly across the centre",
     "VII, p. 190",
     "a theorem (no associative magic square of singly even order exists), cited, not searched"),
    ("the habit curve: median 66 days, range 18 to 254, among 39 participants",
     "X, p. 192",
     "a measurement reported by Lally et al. (2010); there is nothing to recompute"),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("-v", "--verbose", action="store_true", help="show each computed value")
    ap.add_argument("-k", dest="pattern", default="", help="run only the checks whose name contains this")
    args = ap.parse_args(argv)

    passed = failed = 0
    for name, where, fn in CHECKS:
        if args.pattern and args.pattern.lower() not in name.lower():
            continue
        note = Notes()
        try:
            fn(note)
        except (AssertionError, FileNotFoundError) as exc:
            failed += 1
            print(f"  FAIL  {name}   [{where}]")
            if exc.args:
                print(f"        {str(exc.args)[:400]}")
            continue
        passed += 1
        print(f"  pass  {name}   [{where}]")
        if args.verbose:
            for line in note.lines:
                print(f"        {line}")
    if not args.pattern:
        for name, where, why in NOT_RUN:
            print(f"  ----  {name}   [{where}]\n        not run: {why}")
    print()
    print(f"{passed} passed, {failed} failed" + ("" if args.pattern else f", {len(NOT_RUN)} not run"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
