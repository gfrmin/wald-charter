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

- `wald.__all__` ⊆ `{declare, run, Door, report, Display, refusals}` at kit v0.1; the kit v0.10 and v0.11 sections below add five names, and `wald.__all__` lists all eleven (ST1 as of kit v0.11). The verbs `push`, `condition`, `expect` and `decide` are not exported: a host or pack never holds a probability (S1, E5).
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

## The library and the wire (kit v0.10, brief 006)

- `import wald` exposes `declare`, `run`, `Door`, `report`, `Display`, `refusals`, and three more: `load_pack(text, data_dir)` (the surface's `check`), `from_json(text)` (the wire spec: this file's World dict with every rational a string `"p/q"`, `ops` keys as strings, plus `closed` and `table_sources`), `to_json(result, world)` (a Result as JSON: `acts`, `outcomes`, `status`, `paid` as `"p/q"`, `thought`, `steps`, `operations`, and `final` as the TEXT of `report(final, world)` — the belief never crosses as values, S1), and `law`, a dict `{"charter", "surface", "kit"}` naming the signed tags and the kit tag this package conforms to; the kit checks `law["kit"]` against `cage/charter.lock`.
- `tools/serve.py` speaks JSON lines on stdin/stdout, one object per line. Client → server ops: `{"op":"hello"}` → `{"law":…}`; `{"op":"declare","spec":…}` → `{"ok":true,"world":id}` or `{"refused":NAME,"detail":…}`; `{"op":"load_pack","text":…,"data_dir":…}` likewise; `{"op":"run","world":id}` → the server becomes the kernel's side of the Door: it sends `{"observe":act,"id":n}` and waits for `{"outcome":…,"id":n}`, sends `{"fire":act,"id":n}` and waits for `{"fired":true,"id":n}`, then `{"result":…}` as `to_json` gives it; `{"op":"bye"}` ends. An unknown op answers `{"refused":"UNKNOWN_OP"}`; an unknown world id `{"refused":"UNKNOWN_WORLD"}`; a reply out of order is `WIRE`. On the way in, a JSON float is refused `FLOAT` — the name SURFACE gives a decimal — and anything else the wire can get wrong, an unknown key included, is `WIRE`: an unknown key is refused, not ignored, so a misspelt `dplus` cannot declare a v0 World in silence (brief 006, Q6, adopted at kit v0.11). The kernel does no I/O; the tool is outside `src/wald` and may import what it needs.

## What is learned between episodes (kit v0.11, under the signed page `CHARTER-v0.2.md`, tag `charter-v0.2`)

`laws/counts_check.py` is the reference and the definition; `laws/kit_counts.py` is the judge. Nothing here needs SURFACE v0.2: the kernel implements the semantics through this dict, as brief 005a did before SURFACE v0.1.

**The v0.2 World dict.** A probe, not a pack: the adapter converts it and never declares it as a pack.
- `locals` and `globals`: lists of `(name, [values])`, the dimensions of Ω. A state is the pair `(l, g)` of tuples of values, locals then Globals. A World with `globals: []` has one Global value, `()`.
- `prior_global`: `{g: Fraction}`; `prior_local`: `{g: {l: Fraction}}` — P(local | Global), each row summing to 1; a zero leaves the state out of Ω.
- `T`: `{terminal: {(l, g): Fraction}}`; `O`: `{act: {"K": {(l, g): {outcome: Fraction}}, "price": Fraction, "once": bool}}`, optionally `"ends"` (a set of ending outcomes) and `"u_end"` (`{outcome: Fraction}`, the ending utility). `N`, `d`, and optionally `dplus`, `fraction`, `rate`, `ops` (CHARTER v0.1).
- `after`, optional: `{"K": {end: {(l, g): {outcome: Fraction}}}, "price": Fraction, "name": str}` — the After-act, a kernel for every end; `name` defaults to `"after"`.
- Shipped Counts, optional: `counts` (a `Counter` of records), `counts_sha` (hex), `score` (Fraction), `falsifier` (one record).
- **A record** is `(((act, outcome), ...), end, after_outcome)`: the draws in order, the terminal fired (or, for an ending outcome, `"end:act=outcome"`), and the after-report or `None`.

**The adapter gains seven methods**, each conversion around one kernel call (E5):
- `prior(world, records) -> {(l, g): Fraction}` — the next episode's prior after those records, P(Global | Counts) · P(local | Global) (§4).
- `persist(records)` — what the kernel keeps after those records: its Counts. The kit checks it is bounded by the distinct records (S13).
- `declare(world)` — the World the dict declares, or `Refused` with `.name` one of `GLOBAL`, `AFTER`, `PLATE`, `UNSCORED` (S11–S14). S15 refuses nothing.
- `disclose(world) -> [ {g: Fraction}, ... ]` — S15's classes, each with its declared prior mass, exactly as `counts_check.unwashable` gives them.
- `e7(world, counts) -> {(history, act, end): Fraction}` — E7's lines, keyed as `counts_check.diagnostic` keys them (`act` is `"<after>"` for an after-report, `end` then the terminal fired, else `None`).
- `score(world, counts) -> Fraction` — S14's leave-one-out predictive probability.
- `world(world)` — the kernel's World for the dict, for `wald.plate`.

`decide(b, world, n, used)` is unchanged: the kit hands it v0 episode Worlds built from `prior`.

**The public plate** — the one new public name. `wald.plate(world) -> Plate`, with:
- `Plate.run(door) -> Result` — one episode: the prior from the plate's Counts (§4), v0's loop at the floor, the terminal fired by `door.fire(t)`, then, if an After-act is declared, its report from `door.outcome(name)`; the record enters the Counts. A report of probability zero, during the episode or after it, ends the plate: `Result.status` names WORLD_FALSIFIED, the Counts stay as they were, and the falsifying record is kept (J26); a further `run` refuses.
- `Plate.counts() -> Counter` — the plate's Counts. They are facts, not probabilities, so S1 lets a host hold them.
- `Plate.falsifier()` — the falsifying record, or `None`.
- `Plate.disclosure() -> Display` — S15's disclosure as inert text, as `report` gives a belief (S1).

`Result` gains `record`. The Door is unchanged: the After-act is an observational act the door answers by name, asked only after the terminal has fired.

