# INTERFACE — how the kit talks to an implementation

The kit imports `wald.kit_adapter` from the path given by `--impl` and calls `make_agent()`. The adapter is a thin test-only shim over the real kernel; it converts plain data to the kernel's own types and back. Nothing in the adapter may choose, update or compute on its own (CHARTER E5).

All numbers are `fractions.Fraction`. States, acts and outcomes are hashable values (strings or tuples).

**World** (a plain dict):
- `prior`: `{state: Fraction}`, strictly positive, summing to 1.
- `T`: `{terminal_act: {state: Fraction}}`, in menu order (dict order is the declared order). Non-empty.
- `O`: `{observational_act: spec}`, in menu order, where `spec` is
  `{"K": {state: {outcome: Fraction}}, "price": Fraction, "once": bool, "ends": {outcome: {state: Fraction}}}`.
  `ends` maps each ending outcome to its u_end.

**The agent** returned by `make_agent()` has four methods:
- `push(b, K) -> {outcome: Fraction}` — the predictive P_b(o|k).
- `condition(b, K, o) -> {state: Fraction}` — the posterior. If P_b(o|k) = 0 it raises an exception whose class is named `WorldFalsified`.
- `expect(b, f) -> Fraction` — E_b[f] for `f: {state: Fraction}`.
- `decide(b, world, n, used) -> act` — decide_n(b, M): the first entry of M attaining V_n. `b` is a belief as `{state: Fraction}`; `used` is a frozenset of `once` acts already executed (M is the declared menu without them); `n` is the number of observations left. The kit passes `n = min(d, n)` itself when it tests a floor.

The kit never reads the implementation's source. It checks C1–C11, S5 and E2 of the signed page on worlds drawn from a seed kept in CI, on forced-tie variants of them (J3), and on the appendix vector.

## The structural surface (kit v0.1)

`kit_structural.py` judges the real API below. Names and signatures are fixed here; everything else is the builder's.

- `wald.__all__` ⊆ `{declare, run, Door, report, Display, refusals}`. The verbs `push`, `condition`, `expect` and `decide` are not exported: a host or pack never holds a probability (S1, E5).
- `wald.refusals`: `Refused` (with a string attribute `name`), `WorldFalsified`, `ObsSpent`. Refusal names: `EMPTY_T`, `PRIOR`, `KERNEL_ROW`, `DEPTH`, `ZERO_EVIDENCE`, `SHARED_SOURCE`, `TABLE_SOURCE`, and from kit v0.2 `PRICE` (a negative price) and `TABLE_SHAPE` (a utility, kernel or u_end table that is not total over Ω, or an ending outcome its kernel cannot emit).
- `wald.world.declare(spec) -> World`. `spec` is the World dict above plus: `N` and `d` (ints); either `closed: True` or `bottom: <state>` (that state's kernel rows must be strictly positive everywhere); `table_sources: {prior, utility, price, horizon, depth: tag, kernels: {act: tag}}` with tag in `data | elicited | fitted`; optionally `sources: {act: [source, ...]}` (default: each act reads one private source) and `components: [source, ...]` (the sources that are components of Ω). Two acts naming one source that is not in `components` is `SHARED_SOURCE`, and so is a `fresh` act naming one (its executions read it twice). Identical kernels are not a shared source.
- `wald.belief`: `Belief` (not constructible directly; no public attributes; immutable), `prior(world) -> Belief`, `condition(belief, world, obs) -> Belief`, `expect(belief, f) -> Fraction`, `report(belief) -> Display`. `condition` and `expect` are internal: only the kernel, the adapter and the kit call them.
- `wald.obs.Obs`: not constructible directly; a second `condition` on the same Obs raises `ObsSpent`.
- `wald.display.Display`: not constructible directly; `str()` renders it; every comparison, arithmetic operator, `float`, `int`, `bool`, `hash`, `iter`, `len` and indexing raises `TypeError`.
- `wald.episode.Door`: base class. The host overrides `outcome(act) -> raw value` and `fire(act)`. The base class provides `observe(act) -> Obs`, the only mint.
- `wald.episode.run(world, door) -> result` with `acts` (every act played, in order, the terminal one last), `outcomes`, `status` in `TERMINAL | ENDED | WORLD_FALSIFIED`, `paid` (sum of prices, a Fraction) and `final` (the last Belief).

Deferred to brief 002, because they need the surface syntax: unhoused numerals and unread parameters (S3), and refusing a pack that chooses (E5).

## The surface (kit v0.3, under the signed page `SURFACE.md`, tag `surface-v0`)

- `wald.surface.check(text, data_dir) -> spec`: parses a pack with `ast`, never executes it, and returns the World spec above, ready for `declare`. `data_dir` is where `data` files are looked for. It raises `wald.refusals.Refused` with the names of SURFACE §5 (`DATA_HASH` included). A pack that breaks several rules may be refused under any one of their names.
- `wald.surface.census(text, data_dir) -> {"data": n, "elicited": n, "fitted": n}`: the count of quantities by source (SURFACE §3).
- From kit v0.3 the spec's `table_sources["kernels"][act]` is a sorted **list** of tags (empty for a kernel with no numbers, such as `point`), `sources` holds every act's `reads`, and `components` lists the components of the space. `declare` accepts these.
- `laws/surface_check.py` is the reference checker: it is the definition, not a dependency. `laws/packs/` is the corpus the kit runs.

## The think act (kit v0.7, under the signed page `CHARTER-v0.1.md`, tag `charter-v0.1`)

- The World dict may carry five more keys: `d` (int, the floor), `dplus` (int), `fraction` (Fraction), `rate` (Fraction), `ops` (`{int: Fraction}`, one cell for each s from 1 to |Ω|). A dict without `dplus` is a v0 World. `table_sources` gains `dplus`, `fraction`, `cost` and `rate` (tags as before; `dplus` and `rate` are `elicited` only); a `fitted` fraction or cost needs its entry in `score`, a dict `{"fraction": Fraction, "cost": Fraction}` with one key per fitted table (SURFACE v0.1 K14; kit v0.8 — kit v0.7 took a bare Fraction).
- The agent gains one method: `step(b, world, n, used) -> (act, how, paid)`. `how` is one of `"floor"` (a v0 World: the act is decide_min(d,n)), `"struck_n"` (n ≤ d or no observational act in M), `"struck_cap"` (cap − V_d ≤ c), `"refused"` (Q(θ) formed, θ not bought), `"think"` (θ executed; the act is decide_min(d⁺,n)); these are S7's buckets in order of precedence. `paid` is the predicted cost c charged, 0 unless `"think"`. `decide(b, world, n, used)` is unchanged and equals `step(...)[0]`.
- `wald.world.declare` gains the refusal names `FRACTION` (f outside [0,1], or a source other than `elicited`/`fitted`), `COST` (a missing or negative cell, or a source other than `elicited`/`fitted`), `DEPTH_PLUS` (a World with θ whose (d, d⁺, N) is not (1, 2, ≥2)), `RATE` (a rate below zero — ERRATA on CHARTER v0.1, SURFACE v0.1 K15 — or whose source is not `elicited`), `UNSCORED` (a `fitted` fraction or cost without its `score` entry), `TABLE_SOURCE` (a `dplus` source other than `elicited`, SURFACE v0.1 K18).
- `wald.episode.run(world, door)`'s result gains `thought` (the sum of predicted costs paid, a Fraction), `steps` (the four S7 counts, `{"struck_n", "struck_cap", "refused", "think"}`) and `operations` (a list, one int per think act executed: the operations counted while θ executed, E6). `paid` stays the sum of prices.
- `laws/meta_check.py` is the reference and the definition; `laws/kit_think.py` is the judge. The kit passes the full `n`; the floor is the implementation's to apply.

## SURFACE v0.1 (kit v0.8, under the signed page `SURFACE-v0.1.md`, tag `surface-v0.1`)

- `wald.surface.check` parses the five declarations `depth_plus`, `think`, `cost`, `rate`, `score` and returns the spec above with `dplus`, `fraction`, `rate`, `ops`, `table_sources.{dplus,fraction,cost,rate}` and `score`; it refuses by the names of SURFACE v0.1 §4, K16's provenance rule included. `census` counts the new cells as K17 says (a param once at declaration under its source; a cell once under its table's).
- `laws/packs/ok` and `laws/packs/poison` carry the v0.1 corpus; `kit_surface.py` runs all of it (R2, R3), and R5/R6 through `laws/surface_check.py`.
