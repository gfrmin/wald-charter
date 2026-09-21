# SURFACE v0.1 — amendment: declaring the think act

Status: **draft 3, unsigned.** In force from the author-signed tag `surface-v0.1`, together with `surface-v0`. Where the two pages speak of the same thing, this page decides; everything it does not mention stands as signed. This page gives syntax to the five tables CHARTER v0.1 adds (Depth⁺, Fraction, Cost, Rate, Score) and nothing else. `laws/surface_check.py` is amended to be its reference checker; `laws/packs/{ok,poison}` gain its corpus.

Marks **[K12]–[K17]** are author judgements, ruled in §7.

## 1. Five more declarations

| declaration | says |
| --- | --- |
| `depth_plus(d⁺, source="elicited")` | Depth⁺, a whole number, declared as `depth(d, source=…)` is (K6: depths are sourced separately) but with one admissible source: it is the owner's, fixed by CHARTER v0.1 J11, so `elicited`; any other is `TABLE_SOURCE`. Written out although J11 fixes it at 2: no defaults. |
| `think(fraction=number, source=…)` | the think act θ and its Fraction f: a cell (a number, a `param`, or arithmetic over them, §3 of v0). The source is f's: `elicited` or `fitted`, anything else `FRACTION`. **[K13]** |
| `cost([number, …], source=…)` | the Cost table: the s-th entry is ops(s), the predicted operations of one think act at s live states, for s = 1 … \|Ω\|. **A list, positional, exactly \|Ω\| long**: the keys are positions, and no numeral stands for a key **[K12]**. Comes after `prior` (\|Ω\| is what the prior names, K10). A list of the wrong length, or a negative cell, or a source other than `elicited` or `fitted`, is `COST`. |
| `rate(number, source="elicited")` | the Rate r, utility per operation, the owner's. Its source is `elicited`; any other is `RATE`. |
| `score(number, of="fraction"\|"cost", source="data")` | the Score of one `fitted` meta-table, named by `of`: the held-out score of that fit, as measured. Its source is `data`; any other is `TABLE_SOURCE`. One per fitted table, no more (`DUPLICATE`) and no fewer: a fitted Fraction or Cost without its Score is `UNSCORED`; a Score of a table that is not `fitted` is `MISSING`. **[K14]** |

`depth_plus`, `think`, `cost` and `rate` come together or not at all: any of them without the others is `MISSING`. A pack without them is a v0 pack and elaborates exactly as before. Each appears at most once (`DUPLICATE`); `score` at most once per table.

**What a meta-table's cell may read [K16].** Every cell of these five tables is a cell in v0 §3's sense, and v0's fence stands unchanged: a `fitted` `param` read by any table whose source is not `fitted` is `TABLE_SOURCE` — so a `fitted` number has no lawful spelling in `rate`, `depth_plus` or `score`. Beyond the fence, a meta-table admits a parameter only if the parameter's **provenance** — its own source together with the sources of every parameter its own cell reads, transitively — lies within the sources the table could itself declare: `think` and `cost` admit `elicited` and `fitted`, `rate` and `depth_plus` admit `elicited`, `score` admits `data`. A parameter of other provenance behind a lawful label is refused by the table's own name (`FRACTION`, `COST`, `RATE`; `TABLE_SOURCE` for `score` and `depth_plus`). Routing a number through a second `param` does not change its provenance, as v0's corpus already holds for the fence (`a1_1.2_laundered_parameter.py`). A meta-belief is the owner's number or a fit, and a Score is a measurement; neither arrives from elsewhere under a lawful label.

The World the checker builds gains `dplus`, `fraction`, `rate`, `ops`, `table_sources.dplus`, `.fraction`, `.cost`, `.rate`, and `score` as `{"fraction": number, "cost": number}` for the fitted tables (INTERFACE.md, kit v0.8). `declare` then applies CHARTER v0.1's own refusals: `FRACTION` (f outside [0, 1]), `COST` (a cell below 0), `RATE` (r below 0, per ERRATA on CHARTER v0.1), `DEPTH_PLUS` (d ≠ 1, or Depth⁺ ≠ 2, or N < 2, alongside a `think`).

## 2. Numbers (CHARTER v0.1 S3)

To v0 §3's six tables add five places a number may appear: `depth_plus`'s number, `think`'s `fraction`, each `cost` entry, `rate`'s number, each `score`'s number. Each is a cell in the sense of v0 §3 — an integer, a ratio, a `param`, or arithmetic over these; no decimals. The census counts as v0's checker does **[K17]**: a `param` counts once where it is declared, under its own source, and a cell counts once under its table's source whether written in place or read from a `param`. This is one reading of v0 §3's "a parameter keeps its own source wherever it is read"; it is the reading `laws/surface_check.py` has implemented since `surface-v0`, and this page makes it the reading in force. Under it a `fitted` table whose one cell reads an `elicited` `param` contributes one `fitted` quantity and the `param` one `elicited` quantity. The positions of a `cost` list are not numbers and are not counted **[K12]**.

## 3. What a pack still cannot say

Nothing here lets a pack choose when to think: the rule is CHARTER v0.1 §2's, in the kernel, and the pack supplies f, ops and r and no comparison of them. There is no form for a Fraction or Cost keyed on anything but s (CHARTER v0.1 §7 defers that), no form for updating either within an episode, and no form for a second think act. A `depth_plus` other than 2, or one in a pack whose `depth(d)` is not 1, elaborates to a World that `declare` refuses (`DEPTH_PLUS`); the surface does not pre-empt the kernel's name **[K15]**.

## 4. Refusals, by name

Added to v0 §5. Of the surface: `FRACTION` (fraction source, or a parameter of a source it does not admit), `COST` (cost length, sign, source, or such a parameter), `RATE` (rate source or such a parameter), `UNSCORED`, `MISSING` (as above); `TABLE_SOURCE` and `DUPLICATE` extend to the new tables. Of the World, from `declare`: `FRACTION` (range), `COST` (range), `RATE` (range), `DEPTH_PLUS`. K7 stands: one broken rule, that rule's name; several, any one of theirs.

## 5. Consequences added — what the kit will check

- **R5 Round trip, with a thought.** Every v0.1 World of `INTERFACE.md` prints as a pack that elaborates back to the same World, `dplus`, `fraction`, `rate`, `ops` and their sources included.
- **R6 Frozen thoughts.** For every lawful pack that declares `think`, `decide⁺` at the root (bucket and act, CHARTER v0.1 §2) is the frozen one.
- R2 and R3 extend to the new corpus; R4 is unchanged.

## 6. Residues

The positional `cost` list is the first table whose key is a count rather than a name; the count is of states as the prior names them (CHARTER v0.1 §6).

## 7. Rulings

| mark | question | ruling | date |
| --- | --- | --- | --- |
| K12 | Cost is a positional list of exactly \|Ω\| cells: positions are not numerals, so K3 is untouched and the census counts cells only | | |
| K13 | five declarations — `depth_plus`, `think`, `cost`, `rate`, `score` — one per table of CHARTER v0.1 S3, each with its own source as K6 requires; Depth⁺ written out although J11 fixes it (no defaults) | | |
| K14 | `score` is a `data`-sourced quantity naming the table it scores by `of`; exactly one per fitted table | | |
| K15 | the surface does not repeat `declare`'s range and depth checks under its own names; the kernel's refusal names stand for both | | |
| K16 | a meta-table admits only parameters whose provenance (own source and, transitively, the sources of every parameter their cells read) lies within the sources it could declare, refused by the table's own name; v0's fence is unchanged and covers every cell; `depth_plus` is `elicited` only | | |
| K17 | the census reading in force: a parameter counts once under its own source at declaration, a cell once under its table's source; an erratum on v0 §3's wording is queued | | |

Attack sessions:

- Session 1, on draft 1 (2026-09-21): 7 findings claimed (1a, 1b, 2a, 2b, 3, 4, 5); 5 reproduced against the draft checker or the pages (1a accepted by the checker; 1b and 3 refused by the checker but admitted by the page's words; 2a/4 a contradiction with CHARTER v0.1 S3; 2b unsayable), 5 the census rule left unstated. Resolved in draft 2: Depth⁺ is its own declaration with its own source (K13 amended); `score` names its table and repeats per fitted table (K14 amended); K16 added, with `owned` in the checker and eleven new poison packs; §2 states v0's census rule. No act of any pack accepted by both drafts changed.
- Session 2, on draft 2 (2026-09-21): 3 findings claimed (1.1, 4.1, 4.2), categories 2, 3, 5 clean; all 3 reproduced against the draft checker (1.1 accepted both ways — a `data` number into `rate` and an `elicited` one into `score`, each through a second `param`; 4.1 a `fitted` `depth_plus` accepted against K16's words; 4.2 lawful, its census the draft's reading). Resolved in draft 3: K16 restated on provenance, with five new poison packs; `depth_plus` is `elicited` only; K17 states the census reading in force and queues an erratum on v0 §3. One lawful pack added for 4.2. No act of any pack accepted by both drafts changed.

## Appendix — CHARTER v0.1's vector A, as a pack

```python
world("p", closed=True)
horizon(2, source="elicited")
depth(1, source="elicited")
space({"health": ["sick", "well"]})
prior({"sick": 1/5, "well": 4/5}, source="data")
utility({"treat": {"sick": 0, "well": -2}, "leave": {"sick": -10, "well": 0}}, source="elicited")
price({"test": 1/2}, source="elicited")
act("test", once=False, kernel=table({"sick": {"+": 9/10, "-": 1/10}, "well": {"+": 1/5, "-": 4/5}}, source="data"), reads=["health"])
depth_plus(2, source="elicited")
think(fraction=1/2, source="elicited")
cost([100, 200], source="elicited")
rate(1/1000, source="elicited")
```

Census: data 6, elicited 12 (horizon, depth, 4 utilities, 1 price, depth⁺, fraction, 2 cost cells, rate), fitted 0. With `param("r0", 1/1000, source="data")` and `rate(r0, …)` instead, the pack is refused RATE; were it admitted its census would be data 7, elicited 12 (the parameter once as `data`, the cell once as `elicited`). At the root: struck by nothing, Q(θ) = −24/25 > −51/50, θ bought, `test` played, 1/5 paid.
