#!/usr/bin/env python3
"""verify_all.py — re-run every computation The Geometry of Existence relies on.

    python3 checks/verify_all.py          # run everything
    python3 checks/verify_all.py -v       # show each computed value
    python3 checks/verify_all.py -k e8    # run the checks whose name contains "e8"

"The Checks" (pages 212–213 of the complete edition) lists every computation
the book relies on and says the first group is run by a program, verify_all.py,
that "uses nothing outside the standard Python library". This file is that
program, rebuilt for this repository from the definitions printed in the book:
each check names the page or section it answers to, computes the value from the
stated model, and compares it with the printed figure.

The second group on that page is the frozen workshop code (sixsite_mcmc.py,
consequence_mcmc.py, sophonticism_consequence_test.py). That code is not part of
this repository, so those lines are reported as NOT RUN here, never as passed.

A failure is, in the book's own words, "an error in Level Five". Report it with
the issue template "A check failed".
"""
from __future__ import annotations

import argparse
import cmath
import itertools
import math
import random
import sys
from fractions import Fraction as F

CHECKS = []


def check(name, where):
    def deco(fn):
        CHECKS.append((name, where, fn))
        return fn
    return deco


class Report:
    def __init__(self, verbose):
        self.verbose = verbose
        self.lines = []

    def note(self, msg):
        self.lines.append(msg)


def close(a, b, tol):
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# §12  Balanced ternary, corrected
# ---------------------------------------------------------------------------

D3 = (-1, 0, 1)


@check("balanced ternary: each of the nine digit sums has exactly one (result, carry)", "§12, p.157")
def _(r):
    for a, b in itertools.product(D3, D3):
        sols = [(res, c) for res in D3 for c in D3 if a + b == res + 3 * c]
        assert len(sols) == 1, (a, b, sols)
        r.note(f"{a:+d} + {b:+d} = {sols[0][0]:+d} + 3·{sols[0][1]:+d}")


@check("(+1) + (−1) = 0 with no carry; zero is the only digit fixed by negation", "§12, p.157")
def _(r):
    sols = [(res, c) for res in D3 for c in D3 if 1 + (-1) == res + 3 * c]
    assert sols == [(0, 0)]
    assert [d for d in D3 if -d == d] == [0]


def balanced_digits(radix):
    h = radix // 2
    return tuple(range(-h, h + 1))


def truncation_holds(radix, max_len):
    """For every balanced word up to max_len digits and every cut k,
    the discarded tail is strictly less than half the kept unit radix**k."""
    digits = balanced_digits(radix)
    for n in range(1, max_len + 1):
        for word in itertools.product(digits, repeat=n):     # word[i] is digit of radix**i
            for k in range(1, n + 1):
                tail = sum(d * radix ** i for i, d in enumerate(word[:k]))
                if not 2 * abs(tail) < radix ** k:
                    return False
                if not abs(tail) <= (radix ** k - 1) // 2:
                    return False
    return True


@check("truncation: discarded tail < half the kept unit, every word up to length 7, radix 3", "§12, p.157")
def _(r):
    assert truncation_holds(3, 7)
    r.note(f"{sum(3 ** n for n in range(1, 8))} words checked")


@check("the same holds in balanced radix 5 and radix 7 (smallest such radix is 3, not the only one)", "§12, p.157")
def _(r):
    assert truncation_holds(5, 6)
    assert truncation_holds(7, 5)
    # radix 3 is the smallest odd radix > 1, and a balanced radix must be odd
    assert min(b for b in range(2, 8) if b % 2 == 1) == 3
    r.note("radix 5 to length 6, radix 7 to length 5")


@check("nearest rounding is not error-free on average: V = 1 truncated at k = 1 errs by +1", "§12, p.157")
def _(r):
    # V = 1 has the single balanced-ternary word (1); keeping places >= 3**1 leaves 0
    words = [w for n in range(1, 6) for w in itertools.product(D3, repeat=n)
             if sum(d * 3 ** i for i, d in enumerate(w)) == 1]
    errs = set()
    for w in words:
        kept = sum(d * 3 ** i for i, d in enumerate(w) if i >= 1)
        errs.add(1 - kept)
    assert errs == {1}, errs


@check("signed binary {−1,0,+1} in radix 2: 1 is equally near 0 and 2, so nearest truncation is not unique", "§12, p.157")
def _(r):
    assert abs(1 - 0) == abs(1 - 2)
    # two signed-binary spellings of 1 truncate at k = 1 to different multiples of 2
    spellings = [w for w in itertools.product(D3, repeat=2) if w[0] + 2 * w[1] == 1]
    kept = {2 * w[1] for w in spellings}
    assert kept == {0, 2}, kept


# ---------------------------------------------------------------------------
# §4  Geometry is constraint, not destiny
# ---------------------------------------------------------------------------

@check("simplex identities: p₀ = 1 − q and p± = (q ± m)/2", "§4, p.145")
def _(r):
    rng = random.Random(4)
    for _ in range(500):
        a, b = sorted(F(rng.randint(0, 1000), 1000) for _ in range(2))
        pm, p0, pp = a, b - a, 1 - b
        m = pp - pm                 # ⟨S⟩
        q = pp + pm                 # ⟨S²⟩
        assert p0 == 1 - q
        assert pp == (q + m) / 2 and pm == (q - m) / 2
        assert abs(m) <= q <= 1


# ---------------------------------------------------------------------------
# §14  Zero as a measurable physical occupation
# ---------------------------------------------------------------------------

@check("Blume–Capel conditional zero probability at β = 1, Δ = 0: 0.3333, 0.2447, 0.1173 for field 0, 1, 2", "§14 · The Checks, p.212")
def _(r):
    got = [1 / (1 + 2 * math.cosh(h)) for h in (0, 1, 2)]
    for g, want in zip(got, (0.3333, 0.2447, 0.1173)):
        assert close(g, want, 5e-5), (g, want)
    r.note(", ".join(f"{g:.6f}" for g in got))


def p_zero_exact(bJ_pow, bD_pow, bK_pow, a, b, bchi_pow=0, C=0):
    """P(s=0|a,b) when βJ, βD, βK, βχ are integer multiples of ln 2.
    Every Boltzmann factor is then a power of two, so the answer is exact."""
    two = F(2)
    w0 = two ** (bchi_pow * C)                                 # zero state: energy −χC
    wpm = two ** (-(bD_pow + bK_pow * a * b))                  # e^{−β(D + Kab)}
    cosh = (two ** (bJ_pow * (a + b)) + two ** (-bJ_pow * (a + b))) / 2
    return w0 / (w0 + 2 * wpm * cosh)


@check("three-spin model at βJ = βD = ln 2, βK = 2 ln 2: P(0) = 32/49 aligned and 1/5 opposed", "§14, p.159")
def _(r):
    assert p_zero_exact(1, 1, 2, +1, +1) == F(32, 49)
    assert p_zero_exact(1, 1, 2, +1, -1) == F(1, 5)
    assert F(32, 49) - F(1, 5) == F(111, 245)


@check("with K = 0 the model gives 8/25 and 1/2 — the ordering reverses; threshold βK = ½ ln cosh 2βJ ≈ 0.3769", "§14, p.159")
def _(r):
    assert p_zero_exact(1, 1, 0, +1, +1) == F(8, 25)
    assert p_zero_exact(1, 1, 0, +1, -1) == F(1, 2)
    thr = 0.5 * math.log(math.cosh(2 * math.log(2)))
    assert close(thr, 0.3769, 5e-5), thr
    # just above / below the threshold the ordering flips
    def p(bK, a, b):
        bJ = bD = math.log(2)
        return 1 / (1 + 2 * math.exp(-(bD + bK * a * b)) * math.cosh(bJ * (a + b)))
    assert p(thr + 1e-6, 1, 1) > p(thr + 1e-6, 1, -1)
    assert p(thr - 1e-6, 1, 1) < p(thr - 1e-6, 1, -1)
    r.note(f"threshold {thr:.6f}")


# ---------------------------------------------------------------------------
# §15  Consequence — the third term in time
# ---------------------------------------------------------------------------

@check("consequence model at βχ = ln 2, other couplings off: 1/3 with no record, 1/2 with one; difference 1/6", "§15.2, p.164")
def _(r):
    p0 = p_zero_exact(0, 0, 0, 1, 1, bchi_pow=1, C=0)
    p1 = p_zero_exact(0, 0, 0, 1, 1, bchi_pow=1, C=1)
    assert (p0, p1, p1 - p0) == (F(1, 3), F(1, 2), F(1, 6))


def p_zero_float(bJ, bD, bK, bchi, C, a, b):
    return 1 / (1 + 2 * math.exp(-(bD + bK * a * b + bchi * C)) * math.cosh(bJ * (a + b)))


def logit(p):
    return math.log(p / (1 - p))


@check("the log-odds shift equals βχ·ΔC for every tested J, D, K and boundary, and vanishes when χ = 0", "§15.1, p.162")
def _(r):
    grid = (-1.0, -0.3, 0.0, 0.7, 1.5)
    n = 0
    for bJ, bD, bK in itertools.product(grid, repeat=3):
        for a, b in itertools.product((-1, 1), repeat=2):
            for bchi in (0.0, 0.4, math.log(2), 2.0):
                for C1, C2 in ((0, 1), (0.5, 3.0), (2, 0)):
                    shift = logit(p_zero_float(bJ, bD, bK, bchi, C2, a, b)) - \
                        logit(p_zero_float(bJ, bD, bK, bchi, C1, a, b))
                    assert close(shift, bchi * (C2 - C1), 1e-9)
                    n += 1
    r.note(f"{n} cases")


@check("the record stays bounded: 0 ≤ Cₜ ≤ ρᵗC₀ + (1 − ρᵗ)/(1 − ρ), on 200 random histories", "§15.3, p.165")
def _(r):
    rng = random.Random(15)
    for _ in range(200):
        rho = F(rng.randint(0, 99), 100)
        C = C0 = F(rng.randint(0, 50), 10)
        for t in range(1, 61):
            s = rng.choice(D3)
            C = rho * C + (1 - s * s)              # n₀(s) = 1 − s²
            bound = rho ** t * C0 + (1 - rho ** t) / (1 - rho)
            assert 0 <= C <= bound


@check("frozen record C = 1 with K = 0 and βχ = 2 ln 2: P(0) = 32/49 aligned and 4/5 opposed", "Ch. 23, p.191")
def _(r):
    assert p_zero_exact(1, 1, 0, +1, +1, bchi_pow=2, C=1) == F(32, 49)
    assert p_zero_exact(1, 1, 0, +1, -1, bchi_pow=2, C=1) == F(4, 5)


# ---------------------------------------------------------------------------
# §16 / Appendix B  The geometry experiment
# ---------------------------------------------------------------------------

PRISM = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)]
K33 = [(i, j) for i in (0, 1, 2) for j in (3, 4, 5)]
DELTA = F(3, 4)          # Δ/J
BETA_J = 3


def energy(edges, s):
    return sum(s[i] * s[j] for i, j in edges) + DELTA * sum(x * x for x in s)


def ensemble(edges):
    states = list(itertools.product(D3, repeat=6))
    E = [energy(edges, s) for s in states]
    e0 = min(E)
    w = [math.exp(-BETA_J * float(e - e0)) for e in E]
    Z = sum(w)
    zero_frac = sum(wi * s.count(0) / 6 for wi, s in zip(w, states)) / Z
    any_zero = sum(wi for wi, s in zip(w, states) if 0 in s) / Z
    return states, E, e0, zero_frac, any_zero


@check("both six-site graphs have nine edges and degree three at every site", "§16, p.167")
def _(r):
    for g in (PRISM, K33):
        assert len(g) == 9 and len(set(map(frozenset, g))) == 9
        deg = [sum(v in e for e in g) for v in range(6)]
        assert deg == [3] * 6


@check("minimum energy −J with six ground states on the prism; −9J/2 with two on K₃,₃ (all 729 states)", "§16, p.167")
def _(r):
    for g, want_e, want_n in ((PRISM, F(-1), 6), (K33, F(-9, 2), 2)):
        states, E, e0, *_ = ensemble(g)
        assert len(states) == 729
        assert e0 == want_e and E.count(e0) == want_n, (e0, E.count(e0))


@check("zero-site fraction 0.278246795804 (prism), 0.001256340995 (K₃,₃); difference 0.276990454809", "§16, p.167")
def _(r):
    fp = ensemble(PRISM)[3]
    fk = ensemble(K33)[3]
    assert close(fp, 0.278246795804, 5e-13), fp
    assert close(fk, 0.001256340995, 5e-13), fk
    assert close(fp - fk, 0.276990454809, 5e-13), fp - fk
    r.note(f"{fp:.12f} − {fk:.12f} = {fp - fk:.12f}")


@check("probability of at least one zero site: 0.883127466845 and 0.007244882875", "§16, p.167")
def _(r):
    ap = ensemble(PRISM)[4]
    ak = ensemble(K33)[4]
    assert close(ap, 0.883127466845, 5e-13), ap
    assert close(ak, 0.007244882875, 5e-13), ak


@check("two zeros frozen in advance on the prism: 3 of 15 placements reach −J; mean best energy +J/5", "§16, p.168")
def _(r):
    best = []
    for pair in itertools.combinations(range(6), 2):
        free = [v for v in range(6) if v not in pair]
        e = None
        for spins in itertools.product((-1, 1), repeat=4):
            s = [0] * 6
            for v, x in zip(free, spins):
                s[v] = x
            ee = energy(PRISM, s)
            e = ee if e is None else min(e, ee)
        best.append(e)
    assert len(best) == 15
    assert sum(1 for e in best if e == -1) == 3
    assert sum(best, F(0)) / 15 == F(1, 5)


@check("dry-run arithmetic: (0.27485 − 0.001416667 − 0.276990454809) / 0.001500182 = −2.371", "Ch. 23, p.190")
def _(r):
    z = (0.27485 - 0.001416667 - 0.276990454809) / 0.001500182
    assert close(z, -2.371, 5e-4), z
    r.note(f"{z:.4f}")


# ---------------------------------------------------------------------------
# §17  E8, fractals
# ---------------------------------------------------------------------------

def e8_roots():
    roots = []
    for i, j in itertools.combinations(range(8), 2):
        for si, sj in itertools.product((-1, 1), repeat=2):
            v = [F(0)] * 8
            v[i], v[j] = F(si), F(sj)
            roots.append(tuple(v))
    n_int = len(roots)
    for signs in itertools.product((-1, 1), repeat=8):
        if signs.count(-1) % 2 == 0:
            roots.append(tuple(F(s, 2) for s in signs))
    return roots, n_int


def dot(u, v):
    return sum(a * b for a, b in zip(u, v))


@check("E₈: 112 + 128 = 240 roots, each of squared length 2; every pair with inner product −1 sums to a root", "§17, p.169")
def _(r):
    roots, n_int = e8_roots()
    assert (n_int, len(roots) - n_int, len(roots)) == (112, 128, 240)
    rs = set(roots)
    assert all(dot(v, v) == 2 for v in roots)
    pairs = 0
    for u, v in itertools.combinations(roots, 2):
        if dot(u, v) == -1:
            assert tuple(a + b for a, b in zip(u, v)) in rs
            pairs += 1
    r.note(f"{pairs} pairs with inner product −1")


@check("Hausdorff dimension of the Cantor set: log 2 / log 3 = 0.630930", "§17, p.170")
def _(r):
    d = math.log(2) / math.log(3)
    assert close(d, 0.630930, 5e-7), d
    # self-similarity: two copies at scale 1/3 → 2·(1/3)^d = 1
    assert close(2 * (1 / 3) ** d, 1.0, 1e-12)


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


@check("all 240 roots of E₈ project to eight rings of thirty in the Coxeter plane", "§17 figure, p.171")
def _(r):
    roots, _ = e8_roots()
    # simple roots (Bourbaki convention in the even coordinate system)
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
    # W has order 30 (the Coxeter number of E8)
    P = W
    for k in range(2, 31):
        P = mul(P, W)
        if all(P[i][j] == (1 if i == j else 0) for i in range(8) for j in range(8)):
            break
    assert k == 30, k
    lam = cmath.exp(2j * math.pi / 30)
    M = [[complex(W[i][j]) - (lam if i == j else 0) for j in range(8)] for i in range(8)]
    v = _solve_null(M)
    re = [x.real for x in v]
    im = [x.imag for x in v]
    # orthonormalise the plane
    nr = math.sqrt(sum(x * x for x in re))
    e1 = [x / nr for x in re]
    im = [b - sum(p * q for p, q in zip(im, e1)) * a for a, b in zip(e1, im)]
    ni = math.sqrt(sum(x * x for x in im))
    e2 = [x / ni for x in im]
    radii = sorted(math.hypot(sum(float(a) * b for a, b in zip(rt, e1)),
                              sum(float(a) * b for a, b in zip(rt, e2))) for rt in roots)
    rings = []
    for x in radii:
        if rings and abs(rings[-1][0] - x) < 1e-6:
            rings[-1][1] += 1
        else:
            rings.append([x, 1])
    assert [n for _, n in rings] == [30] * 8, rings
    r.note("ring radii " + ", ".join(f"{x:.4f}" for x, _ in rings))


# ---------------------------------------------------------------------------
# §13  The learning study (source-reported table)
# ---------------------------------------------------------------------------

TABLE = {   # H = 16, 64, 256 — transcribed from §13, source-reported
    "float": (92.53, 94.73, 96.58),
    "binary": (90.09, 93.18, 95.05),
    "ternary": (91.13, 93.92, 95.83),
    "mask": (87.39, 91.99, 93.87),
    "wide": (91.43, 93.90, 95.62),
}


@check("learning-study arithmetic: ternary leads binary by 1.04, 0.74, 0.78 and the mask by 3.74, 1.93, 1.96", "§13, p.158")
def _(r):
    t, b, m = TABLE["ternary"], TABLE["binary"], TABLE["mask"]
    assert [round(x - y, 2) for x, y in zip(t, b)] == [1.04, 0.74, 0.78]
    assert [round(x - y, 2) for x, y in zip(t, m)] == [3.74, 1.93, 1.96]


@check("at width 16 the float gap is 1.40 and wider binary leads ternary by 0.30", "§13, p.158")
def _(r):
    assert round(TABLE["float"][0] - TABLE["ternary"][0], 2) == 1.40
    assert round(TABLE["wide"][0] - TABLE["ternary"][0], 2) == 0.30


# ---------------------------------------------------------------------------
# Level Three  The Degree / The Weakest Link
# ---------------------------------------------------------------------------

AND_FORMS = {
    "the smaller": lambda a, b: min(a, b),
    "the product": lambda a, b: a * b,
    "the strictest": lambda a, b: max(F(0), a + b - 1),
}


@check("graded “and” of 0.9 with 0.2: 0.2 (smaller), 0.18 (product), 0.1 (strictest); the average is 0.55", "Ch. 17, p.112")
def _(r):
    a, b = F(9, 10), F(2, 10)
    got = [f(a, b) for f in AND_FORMS.values()]
    assert got == [F(2, 10), F(18, 100), F(1, 10)], got
    assert (a + b) / 2 == F(55, 100)


@check("each of the three forms of “and” is at most the smaller input, across a full grid", "Ch. 17, p.112")
def _(r):
    grid = [F(i, 20) for i in range(21)]
    for a, b in itertools.product(grid, grid):
        for f in AND_FORMS.values():
            assert f(a, b) <= min(a, b)


@check("standard operators: “A and not-A” is never more than half true, exactly half only at one half", "Ch. 16 · The Checks, p.213")
def _(r):
    grid = [F(i, 1000) for i in range(1001)]
    vals = [(a, min(a, 1 - a)) for a in grid]
    assert all(v <= F(1, 2) for _, v in vals)
    assert [a for a, v in vals if v == F(1, 2)] == [F(1, 2)]


@check("Łukasiewicz operators: “A and not-A” is 0 and “A or not-A” is 1 at every degree", "Ch. 16, p.108 · The Checks, p.213")
def _(r):
    for i in range(1001):
        a = F(i, 1000)
        assert max(F(0), a + (1 - a) - 1) == 0
        assert min(F(1), a + (1 - a)) == 1


# ---------------------------------------------------------------------------
# Chapter 24  What the Axiom Does Not Prove
# ---------------------------------------------------------------------------

def satisfies_S0(model):
    """S₀: for every x, if E(x) then L(x)."""
    return all((not model["E"][x]) or model["L"][x] for x in model["dom"])


@check("axiom S₀ by model checking: Theorems 1, 2 and 4 of Chapter Twenty-Four", "Ch. 24, p.196")
def _(r):
    # Theorem 1: something exists and is not conscious
    m1 = dict(dom=["a"], E={"a": True}, L={"a": True}, C={"a": False})
    assert satisfies_S0(m1) and not all(m1["C"][x] for x in m1["dom"] if m1["E"][x])
    # Theorem 2: two existing things differ in a further property M
    m2 = dict(dom=["a", "b"], E={"a": True, "b": True}, L={"a": True, "b": True},
              M={"a": True, "b": False})
    assert satisfies_S0(m2) and m2["M"]["a"] != m2["M"]["b"]
    # Theorem 4: all eight settings of E, C, R on one thing are consistent,
    # with L following E alone
    n = 0
    for e, c, rel in itertools.product((False, True), repeat=3):
        m = dict(dom=["a"], E={"a": e}, L={"a": e}, C={"a": c}, R={("a", "a"): rel})
        assert satisfies_S0(m)
        n += 1
    assert n == 8
    # with L defined from E alone, flipping C or R never changes L
    legit = lambda m: m["E"]["a"]                      # noqa: E731
    for e, c, rel in itertools.product((False, True), repeat=3):
        base = dict(E={"a": e}, C={"a": c}, R={("a", "a"): rel})
        flipped_c = dict(base, C={"a": not c})
        flipped_r = dict(base, R={("a", "a"): not rel})
        assert legit(base) == legit(flipped_c) == legit(flipped_r)


# ---------------------------------------------------------------------------
# Chapter 21  Change Without Erasure
# ---------------------------------------------------------------------------

def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


def inverse(A):
    n = len(A)
    M = [row[:] + [F(int(i == j)) for j in range(n)] for i, row in enumerate(A)]
    for c in range(n):
        p = next(i for i in range(c, n) if M[i][c] != 0)
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        M[c] = [x / pv for x in M[c]]
        for i in range(n):
            if i != c and M[i][c] != 0:
                f = M[i][c]
                M[i] = [x - f * y for x, y in zip(M[i], M[c])]
    return [row[n:] for row in M]


@check("protected part: if P² = P and a change is confined to the complement, the protected part is unchanged", "Ch. 21, p.132")
def _(r):
    rng = random.Random(21)
    done = 0
    while done < 100:
        n = rng.randint(2, 5)
        A = [[F(rng.randint(-4, 4)) for _ in range(n)] for _ in range(n)]
        try:
            Ai = inverse(A)
        except StopIteration:
            continue                                   # singular: draw again
        rank = rng.randint(1, n - 1)
        Dg = [[F(int(i == j and i < rank)) for j in range(n)] for i in range(n)]
        P = matmul(matmul(A, Dg), Ai)                  # an (oblique) projection
        assert matmul(P, P) == P
        x = [[F(rng.randint(-9, 9))] for _ in range(n)]
        d = [[F(rng.randint(-9, 9))] for _ in range(n)]
        I_P = [[F(int(i == j)) - P[i][j] for j in range(n)] for i in range(n)]
        change = matmul(I_P, d)                        # confined to the complement
        x2 = [[a[0] + b[0]] for a, b in zip(x, change)]
        assert matmul(P, x2) == matmul(P, x)
        done += 1
    r.note("100 random cases, exact rational arithmetic")


# ---------------------------------------------------------------------------
# second group: frozen workshop code (not in this repository)
# ---------------------------------------------------------------------------

NOT_RUN = [
    ("workshop: sophonticism_consequence_test.py — analytic identities and zero-coupling controls",
     "The Checks, p.213"),
    ("workshop: sixsite_mcmc.py v1.1, seed 20261112 — dry run reproduced digit for digit",
     "The Checks, p.213"),
    ("workshop: consequence_mcmc.py — Parts A, B and C reproduced digit for digit",
     "The Checks, p.213"),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("-v", "--verbose", action="store_true", help="print computed values")
    ap.add_argument("-k", dest="pattern", default="", help="run checks whose name contains this")
    args = ap.parse_args(argv)

    passed = failed = 0
    for name, where, fn in CHECKS:
        if args.pattern and args.pattern.lower() not in name.lower():
            continue
        rep = Report(args.verbose)
        try:
            fn(rep)
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL  {name}   [{where}]")
            if exc.args:
                print(f"        {exc.args}")
            continue
        passed += 1
        print(f"  pass  {name}   [{where}]")
        if args.verbose:
            for line in rep.lines:
                print(f"        {line}")
    if not args.pattern:
        for name, where in NOT_RUN:
            print(f"  ----  {name}   [{where}]  NOT RUN: frozen code not in this repository")
    print()
    print(f"{passed} passed, {failed} failed" + ("" if args.pattern else f", {len(NOT_RUN)} not run"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
