# SURFACE v0.1 — amendment: declaring the think act

Status: **draft 1, unsigned.** In force from the author-signed tag `surface-v0.1`, together with `surface-v0`. Where the two pages speak of the same thing, this page decides; everything it does not mention stands as signed. This page gives syntax to the four tables CHARTER v0.1 adds (Depth⁺, Fraction, Cost, Rate) and to Score, and nothing else. `laws/surface_check.py` is amended to be its reference checker; `laws/packs/{ok,poison}` gain its corpus.

Marks **[K12]–[K15]** are author judgements, ruled in §7.

## 1. Four more declarations

| declaration | says |
| --- | --- |
| `think(depth=2, fraction=number, source=…)` | the think act θ. `depth` is Depth⁺, written out although CHARTER v0.1 J11 fixes it: no defaults. `fraction` is f, a cell (a number, a `param`, or arithmetic over them, §3 of v0). The source is f's: `elicited` or `fitted`, anything else `FRACTION`. Appears at most once. **[K13]** |
| `cost([number, …], source=…)` | the Cost table: the s-th entry is ops(s), the predicted operations of one think act at s live states, for s = 1 … \|Ω\|. **A list, positional, exactly \|Ω\| long**: the keys are positions, and no numeral stands for a key **[K12]**. Comes after `prior` (\|Ω\| is what the prior names, K10). A list of the wrong length, or a negative cell, or a source other than `elicited` or `fitted`, is `COST`. |
| `rate(number, source="elicited")` | the Rate r, utility per operation, the owner's. Its source is `elicited`; any other is `RATE`. |
| `score(number, source="data")` | the Score of a `fitted` Fraction or Cost: the held-out score of the fit, as measured. Its source is `data`; any other is `TABLE_SOURCE`. Present exactly when a Fraction or a Cost is `fitted`: a fitted meta-table without it is `UNSCORED`; a `score` with nothing fitted is `MISSING`. **[K14]** |

`think`, `cost` and `rate` come together or not at all: `think` without `cost` or `rate`, or either without `think`, is `MISSING`. A pack without `think` is a v0 pack and elaborates exactly as before. Each of the four appears at most once (`DUPLICATE`).

The World the checker builds gains `dplus`, `fraction`, `rate`, `ops` and, for the sources, `table_sources.fraction`, `.cost`, `.rate`, and `score` where declared (INTERFACE.md, kit v0.7). `declare` then applies CHARTER v0.1's own refusals: `FRACTION` (f outside [0, 1]), `COST` (a cell below 0), `DEPTH_PLUS` (d ≠ 1, or Depth⁺ ≠ 2, or N < 2, beside a `think`).

## 2. Numbers (CHARTER v0.1 S3)

To v0 §3's six tables add five places a number may appear: `think`'s `depth` and `fraction`, each `cost` entry, `rate`'s number, `score`'s number. Each is a cell in the sense of v0 §3 — an integer, a ratio, a `param`, or arithmetic over these; no decimals — and each counts once in the census under its table's source. `fitted` stays fenced: a `param` with source `fitted` read by a `cost` or `fraction` cell forces that table's source to say `fitted` (`TABLE_SOURCE`), and then a `score` is due. The positions of a `cost` list are not numbers and are not counted **[K12]**.

## 3. What a pack still cannot say

Nothing here lets a pack choose when to think: the rule is CHARTER v0.1 §2's, in the kernel, and the pack supplies f, ops and r and no comparison of them. There is no form for a Fraction or Cost keyed on anything but s (CHARTER v0.1 §7 defers that), no form for updating either within an episode, and no form for a second think act. A `think` with `depth` other than 2, or in a pack whose `depth(d)` is not 1, elaborates to a World that `declare` refuses (`DEPTH_PLUS`); the surface does not pre-empt the kernel's name **[K15]**.

## 4. Refusals, by name

Added to v0 §5. Of the surface: `FRACTION` (fraction source), `COST` (cost length, sign or source), `RATE` (rate source), `UNSCORED`, `MISSING` (as above). Of the World, from `declare`: `FRACTION` (range), `COST` (range), `DEPTH_PLUS`. K7 stands: one broken rule, that rule's name; several, any one of theirs.

## 5. Consequences added — what the kit will check

- **R5 Round trip, with a thought.** Every v0.1 World of `INTERFACE.md` prints as a pack that elaborates back to the same World, `dplus`, `fraction`, `rate` and `ops` included.
- **R6 Frozen thoughts.** For every lawful pack that declares `think`, `decide⁺` at the root (bucket and act, CHARTER v0.1 §2) is the frozen one.
- R2 and R3 extend to the new corpus; R4 is unchanged.

## 6. Residues

The positional `cost` list is the first table whose key is a count rather than a name; the count is of states as the prior names them (CHARTER v0.1 §6).

## 7. Rulings

| mark | question | ruling | date |
| --- | --- | --- | --- |
| K12 | Cost is a positional list of exactly \|Ω\| cells: positions are not numerals, so K3 is untouched and the census counts cells only | | |
| K13 | four declarations — `think`, `cost`, `rate`, `score` — rather than one `think(...)` carrying all; each table keeps its own source as K6 requires; `depth=2` is written out (no defaults) | | |
| K14 | `score` is a `data`-sourced quantity, present exactly when a meta-table is `fitted` | | |
| K15 | the surface does not repeat `declare`'s range and depth checks under its own names; the kernel's refusal names stand for both | | |

Attack sessions: none yet on this page.

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
think(depth=2, fraction=1/2, source="elicited")
cost([100, 200], source="elicited")
rate(1/1000, source="elicited")
```

Census: data 6, elicited 12 (horizon, depth, 4 utilities, 1 price, think's depth and fraction, 2 cost cells, rate), fitted 0. At the root: struck by nothing, Q(θ) = −24/25 > −51/50, θ bought, `test` played, 1/5 paid.
