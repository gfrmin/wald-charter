# SURFACE v0.2 — amendment: declaring what is learned between episodes

Status: **draft 2, unsigned.** In force from the author-signed tag `surface-v0.2`, together with `surface-v0` and `surface-v0.1`. Where the pages speak of the same thing, the later decides; everything this page does not mention stands as signed. This page gives syntax to what CHARTER v0.2 (signed, tag `charter-v0.2`) adds — Globals, P(local | Global), the After-act, shipped Counts with their digest, Score and falsifier — and nothing else. `laws/surface_check.py` is amended to be its reference checker, `laws/counts_check.py` supplies the charter's refusals, and `laws/packs/{ok,poison}` gain its corpus.

Marks **[K19]–[K24]** are author judgements, ruled in §8.

## 1. Five declarations, and one changed

| declaration | says |
| --- | --- |
| `globals(["component", ...])` | which components of the space are **Global**; every other component is local. After `space`, before `prior`. At least one component stays local: a World whose every component persists has no episode, and is refused NOT_A_DECLARATION. **[K19]** |
| `prior({g: p, ...}, source=…)` | **changed when Globals are declared:** P(Global), keyed by Global value — a name when one component is Global, a tuple in the space's order when several are. Without `globals` it is v0's prior over states, unchanged. **[K20]** |
| `local_prior({g: {l: p, ...}, ...}, source=…)` | P(local \| Global): one row for exactly the Global values the prior names, each keyed by local value, with its own source (K6: every table is sourced). After `prior`. Together the two give the joint prior, and **the states are the pairs it gives positive probability**; every other table over states — `utility`, a kernel, `by(...)` — is keyed by those states exactly as in v0, a state being the tuple of its components in the space's order. |
| `after(name, kernel=table({end: {state: {outcome: p}}}, source=…))` | the After-act, at most once. Its kernel has a row for every end — every terminal, and for an ending outcome the key `(act, outcome)` — and its price is a cell of `price` under its name. **[K21]** |
| `counts([[draws, end, after, n], ...], sha256="…", source="data")` | shipped Counts, inline. A row is a record — `draws` a list of `[act, outcome]` in the order taken, `end` a terminal or `"end:act=outcome"`, `after` the after-report or `None` — and `n`, a whole number written out, at least 1. Each record at most once. The source is `data`: Counts are facts. **[K22]** |
| `falsifier([draws, end, after])` | the falsifying record of the plate the Counts came from (CHARTER v0.2 J26). Only with `counts`. |
| `score(value, of="counts", source="data")` | the Score of shipped Counts: the leave-one-out predictive probability, which the kernel recomputes (CHARTER v0.2 S14). v0.1's `score` gains `of="counts"`. |

`local_prior`, `after`, `counts` and `falsifier` are for a World that declares Globals; in one that does not, each is refused MISSING (`globals`).

**Reads.** v0's rule stands and now does work: a kernel that depends on a Global component must name it in `reads`, or the pack is refused UNDECLARED_READ. A pack therefore says, in the open, which instruments' laws the World learns about.

## 2. Numbers (S3)

To the tables of v0 §3 and v0.1 §2 add: every cell of `local_prior`, every cell of the After-act's kernel, each multiplicity `n` of `counts`, and a counts `score`. Each is a cell in the sense of v0 §3 and counts once in the census under its table's source; a multiplicity counts under `data`. A record's names — acts, outcomes, ends — are names, not numerals, and so is the digest.

## 3. The canonical encoding (CHARTER v0.2 S13)

The digest `sha256` of shipped Counts is the SHA-256, written as 64 lowercase hex digits, of the ASCII bytes of one JSON array. Each distinct record is one element, `[draws, end, after, n]`: `draws` an array of `[act, outcome]` arrays in the order taken, `end` a string, `after` a string or `null`, `n` an integer. The JSON is **compact** — no whitespace anywhere, `,` between items and `:` after keys — and every character outside ASCII is written as a `\uXXXX` escape with lowercase hex, a surrogate pair for a character beyond U+FFFF. The elements are sorted by their own compact JSON text, and since that text is ASCII the order is byte order in any language. `laws/counts_check.counts_sha` is the reference, and a pack whose digest uses any other encoding — Python's default `json.dumps`, say — is refused PLATE (`v02_counts_python_default_digest.py`). **[K23]**

## 4. What a pack still cannot say

A drift of the Globals between episodes; Counts shared between Worlds; a utility that reads a Global (CHARTER v0.2 S11, refused GLOBAL); a second After-act (refused AFTER); Counts read from a file rather than written in the pack (**[K24]**: a pack that learns carries its data, so its digest is checkable from the pack alone). Nothing here lets a pack choose when to grade: the After-act is taken whenever declared (CHARTER v0.2 J27).

## 5. Refusals, by name

Of the surface: MISSING (`globals` after `prior`; `local_prior` absent; an After-act with no price; a `falsifier` or a counts `score` without `counts`; any v0.2 declaration without `globals`), NOT_A_DECLARATION (every component Global; a record or row of the wrong shape; a multiplicity not a whole number ≥ 1), UNKNOWN_NAME (a Global component not in the space), TABLE_SHAPE (a `local_prior` row missing or naming a value outside the space), TABLE_SOURCE (Counts not `data`), FLOAT (a decimal multiplicity), DUPLICATE (a declaration or a record twice). Of the World, from the charter: GLOBAL, AFTER, PLATE (a wrong digest; a record no episode can write; a multiset impossible under every Global value), UNSCORED (no Score, or not the leave-one-out one), PRIOR (a `local_prior` row that does not sum to 1). K7 stands: one broken rule, that rule's name.

## 6. Consequences — what the kit will check

- **R6 extended.** Every lawful v0.2 pack elaborates to the reference's World, and its first act at the prior its Counts give is the frozen one.
- **R7 Round trip, with Globals.** Every v0.2 World of `counts_check.py` prints as a pack that elaborates back to the same World — dimensions, both prior factors, utilities, kernels, the After-act, and shipped Counts with their digest and Score. Measured: 100 of 100, half shipping Counts.
- R2 and R3 extend to the new corpus; R4 and R5 are unchanged.

## 7. Residues

The canonical encoding is fixed byte for byte by §3, so a second implementation reproduces it from this page alone; the kit's digest vectors test that it does.

## 8. Rulings

| mark | question | ruling | date |
| --- | --- | --- | --- |
| K19 | `globals([...])` names components of the one space, rather than a second space; at least one component stays local | accept | 2026-09-23 |
| K20 | with Globals declared, `prior` is P(Global) and `local_prior` is P(local \| Global), two tables with two sources; the states are the joint's support, and every other table keeps v0's keys | accept | 2026-09-23 |
| K21 | the After-act is a declaration with its own kernel table, and its price a cell of `price` | accept | 2026-09-23 |
| K22 | Counts are written inline as records with whole multiplicities, source `data`, each record once | accept | 2026-09-23 |
| K23 | the digest's canonical encoding is compact, ASCII-escaped JSON of the records sorted by their own text — language-neutral, byte for byte | amend (draft 1 had Python's default `json.dumps`, which a second implementation would have had to imitate) | 2026-09-23 |
| K24 | no Counts from files in v0.2: a pack that learns carries its data | accept | 2026-09-23 |

Ruled by the owner, 2026-09-23.

Attack sessions: none yet on this page.

## Appendix — CHARTER v0.2's appendix A, as a pack

`laws/packs/ok/appendix_a.py`: the space `{"answer": [a1, a2], "rel": [9/10, 3/5]}`, `globals(["rel"])`, P(rel) uniform, P(answer \| rel) uniform, `ask` reading `answer` and `rel`, the After-act `grade` revealing the answer at every end. It elaborates to exactly the World of `counts_check.reliability_world`, its first act is `ask` at 1/4, one right grade moves the reliability to (3/5, 2/5), and its census is data 12, elicited 24. `laws/packs/ok/appendix_a_shipped.py` is the same pack shipping that grade — digest, Score and all — and starts its plate at (3/5, 2/5), its first act `ask` at 17/50, as the charter's appendix A derives by hand.
