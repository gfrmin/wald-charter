# SURFACE v0.2 — amendment: declaring what is learned between episodes

Status: **draft 3, unsigned.** In force from the author-signed tag `surface-v0.2`, together with `surface-v0` and `surface-v0.1`. Where the pages speak of the same thing, the later decides; everything this page does not mention stands as signed. This page gives syntax to what CHARTER v0.2 (signed, tag `charter-v0.2`) adds — Globals, P(local | Global), the After-act, shipped Counts with their falsifying records, digest and Score — and nothing else. `laws/surface_check.py` is amended to be its reference checker, `laws/counts_check.py` supplies the charter's refusals, and `laws/packs/{ok,poison}` gain its corpus.

Marks **[K19]–[K26]** are author judgements, ruled in §8.

## 1. Five declarations, and one changed

| declaration | says |
| --- | --- |
| `globals(["component", ...])` | which components of the space are **Global**; every other component is local. After `space`, before `prior`. At least one component stays local: a World whose every component persists has no episode, and is refused NOT_A_DECLARATION. **[K19]** |
| `prior({g: p, ...}, source=…)` | **changed when Globals are declared:** P(Global), keyed by Global value — a name when one component is Global, a tuple in the space's order when several are. Without `globals` it is v0's prior over states, unchanged. **[K20]** |
| `local_prior({g: {l: p, ...}, ...}, source=…)` | P(local \| Global): one row for exactly the Global values the prior names, each keyed by local value, with its own source (K6). After `prior`; only with `globals`. Together the two give the joint prior, and **the states are the pairs it gives positive probability**. Every other table over states — `utility`, a kernel, `by(...)` — is keyed by those states exactly as in v0, a state being the tuple of its components in the space's order; and wherever an earlier page counts states — "\|Ω\|", or "what the prior names", as the length of v0.1's `cost` list — it means this joint support. |
| `after(name, kernel=table({end: {state: {outcome: p}}}, source=…), reads=[...])` | the After-act, at most once. Its kernel has rows for **exactly** the ends — every terminal, and for each ending outcome the key `(act, outcome)` — each end with a row for every state; a row keyed by anything that is not an end is refused AFTER. `reads` names the components the kernel depends on, under v0's rule for an act: a kernel that depends on a component it does not name is refused UNDECLARED_READ. Its price is a cell of `price` under its name. An After-act needs no Global: in a World without one it only checks the model (CHARTER v0.2 C21, J27). **[K21]** |
| `counts([[draws, end, after, n], ...], sha256="…", source="data")` | shipped Counts, inline. A row is a record — `draws` a list of `[act, outcome]` in the order taken, `end` a terminal or `"end:act=outcome"`, `after` the after-report or `None` — and `n`, a whole number **written as a literal**, at least 1: not a `param`, not arithmetic. Each record at most once; the list may be empty. The source is `data`: Counts are facts. **[K22]** |
| `falsifiers([[draws, end, after], ...])` | the falsifying records of the plates the Counts passed through (CHARTER v0.2 J26): one per plate that ended WORLD_FALSIFIED, so a chain of refits ships several. A report that falsified the World inside an episode leaves `[draws, None, None]`: the draws up to and including it, with no end. Only with `counts`; each record once; covered by the digest. |
| `score(value, of="counts", source="data")` | the Score of the shipped facts: the leave-one-out predictive probability of every shipped record and every falsifying record, each under the prior conditioned on all the others (CHARTER v0.2 S14), which the kernel recomputes. v0.1's `score` gains `of="counts"`. |

A World that declares `after`, `counts` or `falsifiers` without `globals` has one Global value and learns nothing across episodes; its Counts still travel, and its grades still check the model.

**Reads.** v0's rule stands: every kernel, the After-act's included, names every component it depends on. It does not show everything the World learns about. A local whose values are spelt per Global value — `"a1 good"`, `"a1 poor"`, with P(local \| Global) zero off the diagonal — carries the Global into a kernel that reads only the local. What can be learned is shown by CHARTER v0.2 S15's disclosure, not by `reads`.

## 2. Text and numbers

A pack is **UTF-8** text. A coding declaration naming any other encoding is refused NOT_A_DECLARATION, and so is any name holding a lone surrogate (U+D800–U+DFFF), which no text can hold. **[K26]**

To the tables of v0 §3 and v0.1 §2 add: every cell of `local_prior`, every cell of the After-act's kernel, each multiplicity `n` of `counts`, and a counts `score`. Each counts once in the census under its table's source; a multiplicity counts under `data`. A record's names — acts, outcomes, ends — are names, not numerals, and so is the digest.

## 3. The canonical encoding (CHARTER v0.2 S13)

The digest `sha256` of shipped Counts is the SHA-256, in lowercase hex, of the bytes of one compact JSON array `[counts, falsifiers]`: `counts` the array of the distinct records `[draws,end,after,n]`, `falsifiers` the array of the falsifying records `[draws,end,after]`, each array's elements sorted by their own bytes, ascending. Compact means no whitespace anywhere. Strings are written with exactly these escapes: `\"` and `\\`; `\b`, `\f`, `\n`, `\r`, `\t` for those five; `\u` and four lowercase hex digits for every other character below U+0020 and for every character outside ASCII, a surrogate pair beyond U+FFFF; every other character — `/` and DEL (U+007F) included — as itself. `null` stands for an absent end or after-report. No language's writer is assumed: the bytes are the definition. `laws/counts_check.counts_sha` is the reference, and five vectors pin it, each reproducible with `printf '%s'` and `sha256sum` alone: **[K23]**

| case | the bytes | the digest |
| --- | --- | --- |
| one record | `[[[[["ask","a1"]],"say a1","a1",1]],[]]` | `c0cd11a6dbce579fb5a0ccc1e157fd2316358b4d31bcb47889e8072c50b53dba` |
| no after-report | `[[[[["ask","a1"]],"abstain",null,2]],[]]` | `0b23b8d5964a7ca207fc9c3c2a19a2126e60368254c493b1896cf4538bee6bf9` |
| a non-ASCII name | `[[[[["ask","\u00e9"]],"say \u00e9","\u00e9",1]],[]]` | `d9fa0f5f5548a1aa1e95c10b51a5cfdc9f6b02ab0bf8e0a6725565f956f7ffeb` |
| a falsifier inside an episode | `[[[[["ask","a1"]],"say a1","a1",1]],[[[["ask","a3"]],null,null]]]` | `dd1eaa3a4086b8bdf45c0c114f9b3505a15d69daa233c9940fa5984d5af519d0` |
| a slash and a tab | `[[[[["ask","a/b\t"]],"say a1","a1",1]],[]]` | `710e0cda6e91f6f52f4b8a6ef6898adb2948075a12fd29b4889908abfb55e8e9` |

## 4. What a pack still cannot say

A drift of the Globals between episodes; Counts shared between Worlds; a utility that reads a Global (CHARTER v0.2 S11, refused GLOBAL); a second After-act (refused AFTER); Counts read from a file rather than written in the pack (**[K24]**: a pack that learns carries its data, so its digest is checkable from the pack alone); and a catch-all state ⊥ beside Globals (**[K25]**: CHARTER v0.2 makes ⊥ a local value with P(⊥ \| Global) declared under each Global, and SURFACE v0's `bottom` names a state; the syntax that joins them is deferred, and `bottom` beside `globals` is refused NOT_A_DECLARATION). Nothing here lets a pack choose when to grade: the After-act is taken whenever declared (J27).

## 5. Refusals, by name

Of the surface: MISSING (`globals` after `prior`; `local_prior` without `globals`, or absent with it; an After-act with no price; `falsifiers` or a counts `score` without `counts`), NOT_A_DECLARATION (every component Global; a record or row of the wrong shape; a multiplicity that is not a whole-number literal ≥ 1; a coding declaration other than UTF-8; a lone surrogate; `bottom` beside `globals`), UNKNOWN_NAME (a Global component, or a component the After-act reads, not in the space), UNDECLARED_READ (an After-act kernel depending on a component it does not read), TABLE_SHAPE (a `local_prior` row missing or naming a value outside the space), TABLE_SOURCE (Counts not `data`), FLOAT (a decimal multiplicity), DUPLICATE (a declaration, a record or a falsifying record twice). Of the World, from the charter: GLOBAL, AFTER (an end without a row, a row that is no end, a second After-act), PLATE (a digest that is not the canonical one over the Counts and falsifiers; a record, or falsifier, no episode here can write; a multiset impossible under every Global value), UNSCORED (no Score, or not the leave-one-out one), PRIOR (a `local_prior` row that does not sum to 1). K7 stands.

## 6. Consequences — what the kit will check

- **R6 extended.** Every lawful v0.2 pack elaborates to the reference's World, and its first act, at the prior its Counts and falsifiers give, is the frozen one.
- **R7 Round trip, with Globals.** Every v0.2 World of `counts_check.py` prints as a pack that elaborates back to the same World — dimensions, both prior factors, utilities, kernels, the After-act with its reads, and shipped Counts and falsifiers with their digest and Score. Measured: 100 of 100, half shipping Counts.
- **R8 The digest.** The five vectors of §3, from their bytes.
- R2 and R3 extend to the new corpus; R4 and R5 are unchanged.

## 7. Residues

None beyond those of the signed pages: the canonical encoding is defined by its bytes (§3).

## 8. Rulings

| mark | question | ruling | date |
| --- | --- | --- | --- |
| K19 | `globals([...])` names components of the one space, rather than a second space; at least one component stays local | accept | 2026-09-23 |
| K20 | with Globals declared, `prior` is P(Global) and `local_prior` is P(local \| Global), two tables with two sources; the states are the joint's support, every other table keeps v0's keys, and every earlier count of states means that support | accept (draft 3 adds the last clause) | 2026-09-23 |
| K21 | the After-act is a declaration with its own kernel table over exactly the ends, its own `reads`, and its price a cell of `price`; it needs no Global | re-rule: draft 2 had no `reads`, and required Globals | |
| K22 | Counts are written inline as records with whole-number literal multiplicities, source `data`, each record once | accept (draft 3 says "literal") | 2026-09-23 |
| K23 | the digest's canonical encoding is defined by its bytes — compact JSON of `[counts, falsifiers]`, every escape pinned, arrays in byte order | re-rule: draft 2 left out the falsifiers and left ASCII escapes open | |
| K24 | no Counts from files in v0.2: a pack that learns carries its data | accept | 2026-09-23 |
| K25 | ⊥ beside Globals is deferred: refused until a syntax joins SURFACE v0's `bottom` to CHARTER v0.2's local ⊥ | | |
| K26 | a pack is UTF-8 text with no lone surrogate | | |

Ruled by the owner, 2026-09-23, on the author's recommendations. K21 and K23 are re-ruled and K25 and K26 are new after attack session 1.

Attack sessions:

- Session 1, on draft 2 (2026-09-24) — attacking an intermediate text of draft 2 whose §3 defined the same encoding without its vector table; every claim that text makes was reproduced, by two independent encoders for the digest. Category 5: nothing. Findings: 1.1 (a lone-surrogate name and an astral name share a digest); 1.2 (the falsifying record lay outside the digest); 1.3 (a multiplicity as a cell reading an elicited param); 1.4 (After-act rows under a key that is no end); 2.1 (an After-act in a World with no Global was unsayable); 2.2 (a chain of refits ships two falsifying records); 3.1 (a coding cookie gives one pack's bytes two sets of names); 3.2 (ASCII escapes not pinned); 3.3 (whether the Score scores the falsifier); 4.1 (\|Ω\| for `cost` under Globals); 4.2 (the After-act's kernel reading a Global, with no `reads`); 4.3 (⊥ beside Globals); 4.4 (`reads` against the joint support). Reproduced against the reference, which also showed it demanding After-act rows for states outside the joint support. With the builder's Q8 and Q9 from brief 007 — After-act rows at ending outcomes, and a falsifier from inside an episode — resolved in draft 3: 1.2 and 2.2 by `falsifiers` inside the digest; 1.1 and 3.1 by K26; 3.2 by pinning every escape; 3.3 by scoring every shipped fact; 1.3 by a literal multiplicity; 1.4 and Q8 by rows for exactly the ends; 2.1 and 4.2 by K21; 4.1 by K20's last clause; 4.3 by K25; 4.4 by restating what `reads` shows; Q9 by prefix falsifiers.

## Appendix — CHARTER v0.2's appendix A, as a pack

`laws/packs/ok/appendix_a.py`: the space `{"answer": [a1, a2], "rel": [9/10, 3/5]}`, `globals(["rel"])`, P(rel) uniform, P(answer \| rel) uniform, `ask` reading `answer` and `rel`, the After-act `grade` reading `answer` and revealing it at every end. It elaborates to exactly the World of `counts_check.reliability_world`, its first act is `ask` at 1/4, one right grade moves the reliability to (3/5, 2/5), and its census is data 12, elicited 24. `laws/packs/ok/appendix_a_shipped.py` is that pack with two lines added — `counts` holding that one right grade, digest `c0cd11a6…53dba` (the first vector of §3), and its Score, 3/8 — and nothing else changed: its census is data 14, elicited 24, and its plate starts at (3/5, 2/5), first act `ask` at 17/50.
