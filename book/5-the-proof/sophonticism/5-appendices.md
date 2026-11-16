<p align="center"><sub>THE GEOMETRY OF EXISTENCE · LEVEL FIVE · THE PROOF AND ITS LIMITS · PAGES 180–187</sub></p>

### Appendices · Appendix A — Derivation of the three-state conditional probability

`DEMONSTRATED` Write H(s|a,b)=Ds²−Js(a+b)+Ks²ab, where a,b∈{−1,+1}, s∈{−1,0,+1}. The three energies are E<sub>0</sub>=0 and E<sub>±</sub>=D+Kab∓J(a+b). Their Boltzmann weights are 1 and exp[−β(D+Kab)]exp[±βJ(a+b)]. Summing gives Z=1+2 exp[−β(D+Kab)]cosh[βJ(a+b)]. Since the zero weight is 1, P<sub>0</sub>=1/Z.

For aligned boundaries, a+b=2 and ab=1. Therefore Z<sub>align</sub>=1+2 exp[−β(D+K)]cosh(2βJ). For opposing boundaries, a+b=0 and ab=−1. Therefore Z<sub>opp</sub>=1+2 exp[−β(D−K)]. We have P<sub>align</sub>>P<sub>opp</sub> exactly when Z<sub>align</sub>&lt;Z<sub>opp</sub>,

equivalently

exp(−βK)cosh(2βJ)&lt;exp(βK),

or

2βK>ln cosh(2βJ). This yields the threshold in §14. A dimensional audit confirms that βJ, βD and βK are dimensionless.

Insert

βJ=ln2,

βD=ln2,

βK=2ln2.

Since

cosh(ln4)=17/8, Z<sub>align</sub>=1+2(1/8)(17/8)=49/32 and P<sub>align</sub>=32/49. Since exp[−β(D−K)]=2, Z<sub>opp</sub>=5 and P<sub>opp</sub>=1/5. The difference is (160−49)/245=111/245. At K=0, Z<sub>align</sub>=1+(17/8)=25/8 giving P<sub>align</sub>=8/25, while Z<sub>opp</sub>=2 giving P<sub>opp</sub>=1/2.

**Strongest objection.** The model assumes equilibrium, fixed boundaries and the specified coupling; any laboratory system may violate those assumptions. The algebra remains true of the stipulated Hamiltonian, not automatically of the device.

<p align="center"><i>A2. Exact consequence-memory probability and bounds</i></p>

`DEMONSTRATED` Define n₀(s)=1−s² and Ht(s)=Ds²−Js(a+b)+Ks²ab−χ Ct n₀(s). At fixed C<sub>t</sub>=C, the energies are E₀=−χC and E<sub>±</sub>=D+Kab∓J(a+b). The

conditional

partition

function

is

Z(C)=exp(βχC)+2 exp[−β(D+Kab)]cosh[βJ(a+b)]. Consequently P₀(C)=exp(βχC)/Z(C). Dividing numerator and denominator by exp(βχC) gives the formula in §15. The odds satisfy P₀(C)/(1−P₀(C))=exp[β(D+Kab+χC)]/{2cosh[βJ(a+b)]}. Taking logarithms yields Δlog-odds=βχΔC at fixed a,b,J,D,K,T. With J=D=K=0 and βχ=ln2, a reset record C=0 produces P₀=1/3, while a record C=1 yields P₀=2/(2+1+1)=1/2. The shift is exactly 1/6. No test data were used.

Iteration of C<sub>t+1</sub>=ρC<sub>t</sub>+n₀(s<sub>t</sub>) gives C<sub>t</sub>=ρ<sup>t</sup> C₀+Σ<sub>k=0</sub><sup>t−1</sup>ρ<sup>t−1−k</sup>n₀(s<sub>k</sub>). Because every n₀ belongs to {0,1}, 0≤C<sub>t</sub>≤ρ<sup>t</sup> C₀+(1−ρ<sup>t</sup>)/(1−ρ) for C₀≥0 and 0≤ρ&lt;1. For χ>0 the feedback favors zero occupancy but does not generate new allowed spin states or spatial dimensions. For χ=0 the memory is decoupled and its conditional observable effect vanishes.

**Strongest objection.** A memory update and conditional Gibbs sampling are not a fully closed dynamical theory. An implementation must characterize relaxation times, drive, heat and work. Standard memory-bearing models can reproduce the same effect. This calculation illustrates, rather than establishes the originality of, the proposed notion of consequence.

### Appendix B — Exhaustive six-site computation, and what it checks

`DEMONSTRATED — REPRODUCIBLE COMPUTATION` The companion Python source enumerates every spin assignment for both graphs: 3⁶=729 states. It asserts the graphs’ equal degrees and edge counts, computes ground-state energy exactly using fractions, normalizes Boltzmann weights by subtracting the minimum energy for numerical stability, computes zero occupancy, and enumerates all 15 two-site frozen masks on the prism. Source code is supplied as a separate plain-text Python file with the book, and the results in §16 can be regenerated without external packages.

The

graphs

are

defined

explicitly.

Prism

edges: (0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5). Bipartite edges: every pair (i,j) with i∈{0,1,2} and j∈{3,4,5}. Energy: JΣ<sub>i,j</sub> s<sub>i</sub> s<sub>j</sub>+(3J/4)Σ<sub>i</sub> s<sub>i</sub>². βJ=3. These definitions suffice for an independent implementation in any language.

The minimum for K₃,₃ is −9J+6(3J/4)=−9J/2, attained by the two staggered ±1 configurations. The prism has unavoidable odd-cycle frustration; complete enumeration confirms a minimum of −J with six ground configurations. The computed finite-temperature occupancies are not inferred from a continuum limit and involve no statistical sampling error. Numerical transcendental function evaluation contributes only ordinary floating-point rounding at the displayed precision.

**Strongest objection.** Computational exhaustiveness proves the output of a model, not the model’s match to nature. A physical device would need independent characterization of couplings and equilibrium.

### Appendix C — The bridge ledger

| From | To | Preserved or related object | Condition | Not licensed |
|---|---|---|---|---|
| Newtonian mechanics | Lagrangian mechanics | Equations of motion | Well-defined L and suitable boundary conditions | Universal minimum principle |
| Classical oscillator | Quantum oscillator | Certain classical limits, expectation-value relations | Appropriate state and scale | Identical microstates |
| Electromagnetic potential | Electromagnetic field | F=dA | Local regularity, gauge structure | Gauge choice as new physical world |
| General relativity | Quantum effective gravity | Low-energy predictions | Energy and curvature below EFT regime | UV-complete quantum gravity |
| Microstates | Thermodynamics | Ensemble expectations | Ensemble assumptions | All systems equilibrate |
| Fine scales | Coarse-grained physics | Appropriate longdistance observables | Universality class, RG regime | Identical microscopic mechanisms |
| Balanced ternary digits | Three-state spins | Shared alphabet only | Explicitly specified representation | Physical substrate follows from notation |

| From | To | Preserved or related object | Condition | Not licensed |
|---|---|---|---|---|
| E8 roots | Physical observables | None supplied | New coupling or measurement map needed | Universe is E8 |
| Three-state equilibrium | History-dependent feedback | Conditional zerostate log odds change by βχΔC | Independently recorded memory, calibrated χ, conditional equilibration | Fifth fundamental force discovered |
| Adaptive sparse weights | Agency | None established | Controlled operational test needed | Free will is measured |

The ledger is deliberately asymmetrical. Some bridges are empirical and well established; others are mathematical examples; some are simply absent. A responsible unifying book contains all three kinds rather than painting missing connections over.

### Appendix D — Glossary, provenance and references

**Action:** Functional whose stationarity yields equations of motion under appropriate conditions. **Agency:** A contested philosophical and operational notion, not synonymous with complexity. **Coarse-graining:** Reduced description that integrates or averages microscopic details. **Dimension:** Must be qualified: spatial, topological, manifold, Hausdorff, Hilbertspace, simplex or controllability dimension. **E8:** An eight-dimensional even unimodular lattice and associated exceptional root system. **Falsifier:** An observation or calculation that would defeat a specified claim under accepted controls. **Frustration:** Inability to satisfy all competing local interaction preferences simultaneously. **Gauge redundancy:** Multiple mathematical representations of the same physical configuration. **Hamiltonian:** Energygenerating dynamical operator or function, interpreted within a specified framework. **Consequence:** Proposed history-record variable that changes conditional transition preferences; not an established fundamental force. **Load-bearing zero:** The proposed distinction between a symbol merely available and an occupied or dynamically selected state with measurable consequences; not a universal physical law. **Sophonticism:** The philosophical research program as proposed here; no claim of an established academic definition or demonstrated universal physical theory.

<p align="center"><i>Provenance of the source corpus</i></p>

[S1] *Super Physics: A Unified Framework for the Fundamental Forces of Nature*, supplied eightpage manuscript; contents reconstructed and critically audited. Original publication status not independently established.

[S2] *DHARANA: The Load-Bearing Zero*, supplied manuscript, 2026; balanced ternary theorems and source-reported MNIST five-arm comparison. Training code, seed-level results and preregistration timestamp not independently verified here.

[S3] *Opus Enchiridion: Reality, Relation and the Work of Understanding*, Research Edition 1.0, 11 November 2026, supplied manuscript; Appendix A–B correct earlier arithmetic and

evidence statements. Its mathematical conclusions have been checked independently where used here.

[S4] *ISOMORPHIC: The Field Manual*, supplied manuscript; useful analogical boundary and commitment to testing, not treated as a physical result.

<p align="center"><i>External references — established work</i></p>

[R1] CERN, “The Standard Model,” https://home.cern/science/physics/standard-model . Scope of the Standard Model and gravity’s exclusion.

[R2] J. F. Donoghue, “General relativity as an effective field theory: The leading quantum corrections,” *Physical Review D* 50, 3874 (1994), https://doi.org/10.1103/PhysRevD.50.3874 .

[R3] Stanford Encyclopedia of Philosophy, “Gauge Theories in Physics,” section on Noether’s theorem, https://plato.stanford.edu/entries/gauge-theories/ .

[R4] NIST, “Kelvin: Boltzmann Constant,” https://www.nist.gov/si-redefinition/kelvin/kelvin-boltzmann-constant .

[R5] K. G. Wilson, “The renormalization group: Critical phenomena and the Kondo problem,” *Reviews of Modern Physics* 47, 773 (1975), https://doi.org/10.1103/RevModPhys.47.773 .

[R6] M. E. Fisher, “Renormalization group theory: Its basis and formulation in statistical physics,” *Reviews of Modern Physics* 70, 653 (1998), https://doi.org/10.1103/RevModPhys.70.653 .

[R7] “Blume–Capel model,” University of Würzburg/MARQOV notes, https://gitpages.physik.uni-wuerzburg.de/marqov/webmarqov/post/2020-05-15-blume-capel/ ; for original model context and phase behavior see also the literature on spin-1 Blume–Capel systems.

[R8] N. D. Elkies, “Math 55a: Q&A,” Harvard University, note on the eight-dimensional selfdual lattice with kissing number 240, https://people.math.harvard.edu/~elkies/M55a.02/qanda.html .

[R9] Stanford Encyclopedia of Philosophy, “Free Will,” https://plato.stanford.edu/entries/freewill/ ; and “Compatibilism,” https://plato.stanford.edu/entries/compatibilism/ .

[R10] U. Seifert, “From Stochastic Thermodynamics to Thermodynamic Inference,” *Annual Review of Condensed Matter Physics* 10, 171–192 (2019), https://doi.org/10.1146/annurev-conmatphys-031218-013554 . Established trajectory-level thermodynamic concepts.

[R11] C. Cockrell and I. J. Ford, “Stochastic thermodynamics in a non-Markovian dynamical system,” *Physical Review E* 105, 064124 (2022), https://doi.org/10.1103/PhysRevE.105.064124 . Environmental memory and entropy production. **Editorial closure.** The book gives a coherent cross-physics map, an explicit consequence-memory extension, calculable three-state models, a reproducible finite enumeration and falsifiers for specific predictions. It does not contain the missing unified quantum-gravity action or a measured new law. Claiming otherwise would turn the axiom of existence into an evasion of evidence.


---

<p align="center">[← Part IV — The Frontier (§18–§22)](4-the-frontier.md) · [Contents](../../README.md) · [The Program, Preregistered →](../23-the-program-preregistered.md)</p>
