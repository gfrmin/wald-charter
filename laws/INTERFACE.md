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
