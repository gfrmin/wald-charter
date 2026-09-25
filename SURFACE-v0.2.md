# SURFACE v0.2 — amendment: declaring what is learned between episodes

Status: **draft 9, unsigned.** In force from the author-signed tag `surface-v0.2`, together with `surface-v0` and `surface-v0.1`. Where the pages speak of the same thing, the later decides; everything this page does not mention stands as signed. This page gives syntax to what CHARTER v0.2 (signed, tag `charter-v0.2`) adds — Globals, P(local \| Global), the After-act, shipped Counts with their falsifying records, digest and Score — and nothing else.

**How this page is written.** Every rule is stated once, as V2.0–V2.14 in §1. Every other section cites rules by ID, and §2 and §3 are generated from the rules and the references by `laws/page_check.py`. Rules of other signed pages are cited by ID: `C2.S12` is CHARTER v0.2's S12, `V0.reads` is SURFACE v0's rule that a kernel names what it reads. `laws/surface_check.py` is the reference, and every refusal it makes names its rule; `laws/counts_check.py` supplies CHARTER v0.2's. `laws/gate.py` runs every mechanical check — this page's traceability, invariance under re-spelling, a second encoder for V2.13, the references and the kit's stand-ins — and an attack runs only once it passes. Marks [K19]–[K28] are the owner's rulings (§4).

## 1. Rules

- **V2.0** Each of `globals`, `local_prior`, `after`, `counts` and `falsifiers` is declared at most once. Refused DUPLICATE.
- **V2.1** `globals(["component", ...])` names which components of the space are Global; the rest are local. It comes after `space` and before `prior`; each name is a component of the space, named once. Every component may be Global: a monitor, whose one local value is `()` [K19]. Refused MISSING (out of order), NOT_A_DECLARATION (not a list of names), UNKNOWN_NAME, DUPLICATE.
- **V2.2** With Globals declared, `prior({g: p, ...}, source=…)` is P(Global), keyed by Global value — a name when one component is Global, a tuple in the space's order when several are — with cells strictly positive and summing to 1. Without Globals it is SURFACE v0's prior over states [K20]. Refused NOT_A_DECLARATION (not a dict), TABLE_SHAPE (a value outside the space), PRIOR — which C2.J20 also refuses of a World given as data.
- **V2.3** `local_prior({g: {l: p, ...}, ...}, source=…)` is P(local \| Global). It comes after `prior`, and is required with Globals when some component is local, and allowed only then. It has one row for exactly the Global values the prior names, each keyed by local values of the space, its cells never negative and each row summing to 1 [K20]. Refused MISSING, NOT_A_DECLARATION (in a World whose every component is Global), TABLE_SHAPE, PRIOR.
- **V2.4** The states are the pairs (local, Global) to which V2.2 and V2.3 together give positive probability. Every other table over states — utilities, kernels, `by(...)` — is keyed by those states as in SURFACE v0, a state being the tuple of its components in the space's order; and wherever an earlier page counts states — "\|Ω\|", "what the prior names", the length of SURFACE v0.1's `cost` — it means these [K20].
- **V2.5** `after(name, kernel=table({end: {state: {outcome: p}}}, source=…), reads=[...])` declares the After-act of C2.S12: a name; a kernel with rows for exactly the ends — each terminal, and `(act, outcome)` for each ending outcome — each with a row for every state, or C2.S12 refuses it AFTER; `reads` naming every component the kernel depends on, as V0.reads asks of an act; and a price, the cell of `price` under its name. It needs no Global [K21]. Refused NOT_A_DECLARATION, UNDECLARED_READ, UNKNOWN_NAME (a read component outside the space), MISSING (no price).
- **V2.6** `counts([[draws, end, after, n], ...], sha256="…", source="data")` ships the Counts of C2.S13 inline. A row is a record — `draws` a list of `[act, outcome]` in the order taken, every outcome a name [K27]; `end` a terminal or `"end:act=outcome"`; `after` the after-report or `None` — and `n`, a whole-number literal, at least 1. Each record at most once; the list may be empty; the source is `data` [K22]. Refused NOT_A_DECLARATION, FLOAT, DUPLICATE, TABLE_SOURCE.
- **V2.7** `falsifiers([[draws, end, after], ...])`, only with `counts`, ships the falsifying records of C2.J26: one for each plate the Counts passed through that ended falsified, so a chain of refits ships several. Each is a prefix `[draws, None, None]` ending at the report that falsified, or a full record whose after-report falsified; each at most once. Which records may be falsifiers, and whether the whole is possible, is C2.S13's, as corrected by `ERRATA.md` (CHARTER v0.3, item 3). Refused MISSING, NOT_A_DECLARATION, DUPLICATE.
- **V2.8** `score(value, of="counts", source="data")`, only with `counts`, declares the Score of C2.S14 as corrected by `ERRATA.md` item 3: for every copy of every record and every falsifying record, its likelihood under the prior conditioned on all the others, multiplied together; the kernel recomputes it [K28]. Refused MISSING, DUPLICATE.
- **V2.9** A World that declares `after`, `counts` or `falsifiers` without Globals has one Global value, `()`: it learns nothing across episodes, its Counts still travel, and its grades still check the model.
- **V2.10** No utility or ending utility is written `by(...)` over a Global component, for C2.S11's rule is one of form; refused GLOBAL. Utilities that differ between two states sharing their local part are C2.S11's to refuse; a utility written over a local that copies a Global is lawful.
- **V2.11** A pack is UTF-8 text with LF line endings. A coding declaration naming another encoding, a CR byte anywhere, or a surrogate code point in any string, paired or not, is refused NOT_A_DECLARATION. A checker reads a pack's bytes as written [K26].
- **V2.12** Every cell of `local_prior`, every cell of the After-act's kernel, each multiplicity of `counts`, and a counts score counts once in the census, under its table's source — a cell that reads a parameter too, as SURFACE v0.1 K17 fixed; a multiplicity under `data`. Names and the digest are not numerals.
- **V2.13** The digest `sha256` is the SHA-256, lowercase hex, of the bytes of the compact JSON array `[counts, falsifiers]`: `counts` the records `[draws,end,after,n]`, `falsifiers` the falsifying records `[draws,end,after]`, each array's elements in ascending order of their bytes; no whitespace; strings with the escapes `\"`, `\\`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\u` with four lowercase hex digits for every other character outside U+0020–U+007E — DEL included — with a surrogate pair beyond U+FFFF; every character from U+0020 to U+007E, `/` included, as itself; `null` for an absent end or after-report; a multiplicity as decimal digits with no sign, exponent or leading zero [K23]. A digest that is not this, C2.S13 refuses PLATE. Five vectors, each reproducible with `printf '%s'` and `sha256sum` alone:

| case | the bytes | the digest |
| --- | --- | --- |
| one record | `[[[[["ask","a1"]],"say a1","a1",1]],[]]` | `c0cd11a6dbce579fb5a0ccc1e157fd2316358b4d31bcb47889e8072c50b53dba` |
| no after-report | `[[[[["ask","a1"]],"abstain",null,2]],[]]` | `0b23b8d5964a7ca207fc9c3c2a19a2126e60368254c493b1896cf4538bee6bf9` |
| a non-ASCII name | `[[[[["ask","\u00e9"]],"say \u00e9","\u00e9",1]],[]]` | `d9fa0f5f5548a1aa1e95c10b51a5cfdc9f6b02ab0bf8e0a6725565f956f7ffeb` |
| a falsifier inside an episode | `[[[[["ask","a1"]],"say a1","a1",1]],[[[["ask","a3"]],null,null]]]` | `dd1eaa3a4086b8bdf45c0c114f9b3505a15d69daa233c9940fa5984d5af519d0` |
| a slash and a tab | `[[[[["ask","a/b\t"]],"say a1","a1",1]],[]]` | `710e0cda6e91f6f52f4b8a6ef6898adb2948075a12fd29b4889908abfb55e8e9` |

- **V2.14** Not sayable in v0.2: a drift of the Globals between episodes; Counts shared between Worlds; Counts read from a file [K24]; Counts from a World with product outcomes, by V2.6's record [K27]; and a catch-all state ⊥ beside Globals [K25], refused NOT_A_DECLARATION.

*A note, not a rule:* V0.reads shows what a kernel reads directly, not everything a World can learn. A local spelt per Global value carries the Global into a kernel that reads only the local. What can be learned is C2.S15's disclosure.

## 2. Refusals, by name

Generated: each name, with the rules under which the references refuse by it.

<!-- generated:refusals -->
- **AFTER**: C2.S12
- **DUPLICATE**: V2.0, V2.1, V2.6, V2.7, V2.8
- **FLOAT**: V2.6
- **GLOBAL**: V2.10, C2.S11
- **MISSING**: V2.1, V2.3, V2.5, V2.7, V2.8
- **NOT_A_DECLARATION**: V2.1, V2.2, V2.3, V2.5, V2.6, V2.7, V2.11, V2.14
- **PLATE**: C2.S13
- **PRIOR**: V2.2, V2.3
- **TABLE_SHAPE**: V2.2, V2.3
- **TABLE_SOURCE**: V2.6
- **UNDECLARED_READ**: V2.5, V0.reads
- **UNKNOWN_NAME**: V2.1, V2.5
- **UNSCORED**: C2.S14
<!-- /generated -->

## 3. Traceability

Generated: each rule, the names it refuses by, how many poisons test it, and the lawful packs or gate checks that exercise it.

<!-- generated:trace -->
| rule | refused by | poisons | exercised by |
| --- | --- | --- | --- |
| V2.0 | DUPLICATE | 1 | — |
| V2.1 | DUPLICATE, MISSING, NOT_A_DECLARATION, UNKNOWN_NAME | 4 | appendix_a, monitor_all_global |
| V2.2 | NOT_A_DECLARATION, PRIOR, TABLE_SHAPE | 3 | appendix_a, router_credence_prior |
| V2.3 | MISSING, NOT_A_DECLARATION, PRIOR, TABLE_SHAPE | 5 | appendix_a |
| V2.4 | — | 0 | appendix_a, monitor_all_global, router_credence_prior, two_instruments |
| V2.5 | MISSING, NOT_A_DECLARATION, UNDECLARED_READ, UNKNOWN_NAME | 4 | appendix_a |
| V2.6 | DUPLICATE, FLOAT, NOT_A_DECLARATION, TABLE_SOURCE | 5 | appendix_a_shipped, monitor_shipping |
| V2.7 | DUPLICATE, MISSING, NOT_A_DECLARATION | 3 | falsified_refit, prefix_falsifier |
| V2.8 | DUPLICATE, MISSING | 2 | appendix_a_shipped, monitor_shipping |
| V2.9 | — | 0 | after_without_globals |
| V2.10 | GLOBAL | 1 | — |
| V2.11 | NOT_A_DECLARATION | 4 | — |
| V2.12 | — | 0 | appendix_a, appendix_a_shipped |
| V2.13 | — | 0 | appendix_a_shipped, encoding_check.py |
| V2.14 | NOT_A_DECLARATION | 1 | — |
| C2.S11 | GLOBAL | 2 | — |
| C2.S12 | AFTER | 2 | — |
| C2.S13 | PLATE | 7 | — |
| C2.S14 | UNSCORED | 2 | — |
| V0.reads | UNDECLARED_READ | 1 | — |
<!-- /generated -->

## 4. Rulings

| mark | question | ruling | date |
| --- | --- | --- | --- |
| K19 | `globals([...])` names components of the one space, rather than a second space; every component may be Global | accept (re-ruled; draft 4 required a local, which a one-valued dummy local defeated, attack session 2) | 2026-09-24 |
| K20 | with Globals declared, `prior` is P(Global) and `local_prior` is P(local \| Global), two tables with two sources; the states are the joint's support, every other table keeps v0's keys, and every earlier count of states means that support | accept (draft 3 adds the last clause) | 2026-09-23 |
| K21 | the After-act is a declaration with its own kernel table over exactly the ends, its own `reads`, and its price a cell of `price`; it needs no Global | accept (re-ruled; draft 2 had no `reads`, and required Globals) | 2026-09-24 |
| K22 | Counts are written inline as records with whole-number literal multiplicities, source `data`, each record once | accept (draft 3 says "literal") | 2026-09-23 |
| K23 | the digest's canonical encoding is defined by its bytes — compact JSON of `[counts, falsifiers]`, every escape pinned, arrays in byte order | accept (re-ruled; draft 2 left out the falsifiers and left ASCII escapes open) | 2026-09-24 |
| K24 | no Counts from files in v0.2: a pack that learns carries its data | accept | 2026-09-23 |
| K25 | ⊥ beside Globals is deferred: refused until a syntax joins SURFACE v0's `bottom` to CHARTER v0.2's local ⊥ | accept | 2026-09-24 |
| K26 | a pack is UTF-8 text with LF line endings: no CR byte, no surrogate code point, paired or not | accept (re-ruled; draft 6 allowed CR, which two readers read two ways, attack session 3) | 2026-09-24 |
| K27 | Counts from a World with product outcomes are deferred: record outcomes are names | accept | 2026-09-24 |
| K28 | adopt the erratum on CHARTER v0.2 S14: the Score scores the falsifying records too, and a full record with no after-report is no falsifier | accept | 2026-09-24 |

Ruled by the owner, 2026-09-23 and 2026-09-24, on the author's recommendations; K26 re-ruled and K28 ruled, 2026-09-24, after attack session 3.

## 5. Consequences the kit checks

- **R6 extended.** Every lawful v0.2 pack elaborates to the reference's World, and its first act, at the prior its Counts and falsifying records give, is the frozen one.
- **R7 Round trip, with Globals.** Every v0.2 World of `counts_check.py` prints as a pack that elaborates back to the same World. Measured: 100 of 100, half shipping Counts.
- **R8 The digest.** V2.13's five vectors, from their bytes, and a second encoder written from V2.13 alone against the reference on fuzzed names.

## 6. Residues

None beyond those of the signed pages: the canonical encoding is defined by its bytes (V2.13).

## 7. The attack log

Attack sessions:

- Session 1, on draft 2 (2026-09-24) — attacking an intermediate text of draft 2 whose §3 defined the same encoding without its vector table; every claim that text makes was reproduced, by two independent encoders for the digest. Category 5: nothing. Findings: 1.1 (a lone-surrogate name and an astral name share a digest); 1.2 (the falsifying record lay outside the digest); 1.3 (a multiplicity as a cell reading an elicited param); 1.4 (After-act rows under a key that is no end); 2.1 (an After-act in a World with no Global was unsayable); 2.2 (a chain of refits ships two falsifying records); 3.1 (a coding cookie gives one pack's bytes two sets of names); 3.2 (ASCII escapes not pinned); 3.3 (whether the Score scores the falsifier); 4.1 (\|Ω\| for `cost` under Globals); 4.2 (the After-act's kernel reading a Global, with no `reads`); 4.3 (⊥ beside Globals); 4.4 (`reads` against the joint support). Reproduced against the reference, which also showed it demanding After-act rows for states outside the joint support. With the builder's Q8 and Q9 from brief 007 — After-act rows at ending outcomes, and a falsifier from inside an episode — resolved in draft 3: 1.2 and 2.2 by `falsifiers` inside the digest; 1.1 and 3.1 by K26; 3.2 by pinning every escape; 3.3 by scoring every shipped fact (reverted in draft 5, which follows the signed S14); 1.3 by a literal multiplicity; 1.4 and Q8 by rows for exactly the ends; 2.1 and 4.2 by K21; 4.1 by K20's last clause; 4.3 by K25; 4.4 by restating what `reads` shows; Q9 by prefix falsifiers.

- Session 2, on draft 4 (2026-09-24), with its own parser: every claim of the page reproduced — the five vectors from their bytes, both appendix packs, their censuses, digest and Score. Category 5: nothing. Findings: 1.1 (a utility paid on two Global dimensions that copy each other — refused GLOBAL by the reference, silent in the text); 1.2 (Counts and a falsifying record no Global value can hold together — refused PLATE by the reference, silent in the text); 1.3 (a surrogate pair spelt by escapes and the character itself, one digest); 2.1 (Counts through a product kernel, whose outcomes are tuples); 2.2 (a monitor whose every component is Global, refused by K19 though a one-valued dummy local made it lawful); 3.1 (how a large multiplicity is written in the bytes); 4.1 (a utility written `by` over a Global that a local copies — the charter's S11 is one of form); 4.2 (which prior cells may be zero or negative); 4.3 (draft 3's Score gave the falsifying records a term, which the signed S14 does not). Resolved in draft 5: 1.1, 1.2, 4.1, 4.2 by saying what the reference does — S11's form and support rules, falsifiers in PLATE's positivity, prior cells; 1.3 by K26's "paired or not"; 2.1 by K27; 2.2 by K19 re-ruled; 3.1 by decimal digits; 4.3 by following S14 as signed.

- Session 3, on draft 6 (2026-09-24): every claim reproduced — the five vectors, both appendix packs, their censuses, digest and Score — with the charter's appendices A, F, I and J cross-checked. Categories 2 and 5: nothing. Findings: 1.1 (a "falsifying record" no plate could leave — a full record with no after-report, in a World with no After-act — moved the prior while the Score, which as signed gives falsifiers no term, stayed at 1: a gap in CHARTER v0.2 S14 itself); 3.1 (a CR LF inside a triple-quoted name: a text reader keeps five characters, Python's parser four, and the two readings give two digests); 4.1 (§5 still listed draft 4's refusal of a World with no local, which K19 had withdrawn — the author's miss). The reference had a bug of its own: it could not read `None` inside a record, so no prefix falsifier had ever parsed, and its harness read packs with newline translation, hiding every CR. Resolved in draft 7: 1.1 by the erratum (K28) and PLATE's rule on full records; 3.1 by K26 re-ruled (no CR; bytes read as written); 4.1 by correcting §5. The census wording queued for this page since SURFACE v0.1 is folded into §2.

- Between sessions 3 and 4, the page was rewritten as rules stated once (draft 8), with the gate. The gate's first run found that V2.13's text wrote DEL as itself while the reference escapes it — which no vector contains, and three sessions had not seen. V2.13 now says what the reference does: every character outside U+0020–U+007E is escaped. The invariance check found that the reference's printer could not write a World with no Global.

## Appendix — CHARTER v0.2's appendix A, as a pack

`laws/packs/ok/appendix_a.py`: the space `{"answer": [a1, a2], "rel": [9/10, 3/5]}`, `globals(["rel"])`, P(rel) uniform, P(answer \| rel) uniform, `ask` reading `answer` and `rel`, the After-act `grade` reading `answer` and revealing it at every end. It elaborates to exactly the World of `counts_check.reliability_world`, its first act is `ask` at 1/4, one right grade moves the reliability to (3/5, 2/5), and its census is data 12, elicited 24. `laws/packs/ok/appendix_a_shipped.py` is that pack with two lines added — `counts` holding that one right grade, digest `c0cd11a6…53dba` (the first vector of §3), and its Score, 3/8 — and nothing else changed: its census is data 14, elicited 24, and its plate starts at (3/5, 2/5), first act `ask` at 17/50.
