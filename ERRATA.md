# ERRATA — queued for CHARTER v0.1

Signed pages are not edited (CHARTER §8). Wording found wanting is queued here with the evidence, and folded in at the next signed version.

1. **S3 does not name parameters in its list of tables**, though its last sentence ("Every declared parameter is read") presupposes them. Found by surface attack session 4 (2026-09-20). Reading in force meanwhile: SURFACE K11 — a parameter is a table cell written once and read by name. No act changes.

## Queued for CHARTER v0.3 (items 1 and 2 were queued for v0.2 and missed its signing; item 3 is on v0.2 itself)

1. **§1 of v0.1 names no clause for a Rate below zero**, though it writes r ∈ ℚ≥0. Found by the builder in brief 005a (`QUESTIONS.md` Q4, with the World). Reading in force meanwhile: a negative Rate is refused by the name RATE, the name the row already gives the Rate's source; SURFACE v0.1 says so, `meta_check.refuse_meta` moves to it at kit v0.8, and the kernel's one string follows in brief 005b. No act changes.

2. **v0.1 §1 names no source for Depth⁺ and no source for Score**, so under S3 either could be `data`, `elicited` or `fitted`. SURFACE v0.1 K18 fixes Depth⁺ as `elicited` (it is the owner's, fixed by J11) and Score as `data` (it is a measurement). Found by attack session 3 on SURFACE v0.1. No act changes.

3. **S14's Score gave the falsifying records no term**, though S13 has the prior condition on them (attack session 3 on SURFACE v0.2, finding 1.1). A pack could therefore ship a plate's data as "falsifying records" and move its learned prior while its Score stayed at the empty product, 1, the best any pack can have. **Corrected reading:** the leave-one-out product has a term for each copy of each record of the Counts and for each falsifying record, each under the prior conditioned on all the others. And a falsifying record is either a prefix — the draws up to and including a report that falsified the World inside an episode, with no end and no after-report — or a full record whose after-report falsified it; a full record with no after-report falsified nothing, and shipped as a falsifier it is refused PLATE. `laws/counts_check.py` implements both. No act changes; only the Score and what PLATE accepts. Adopted by SURFACE v0.2 K28, ruled by the owner on 2026-09-24, and in force from `surface-v0.2`, whose V2.7 and V2.8 state it in full and decide over C2.S13 and C2.S14 as the later page; CHARTER v0.3 is to restate it.

## Amendment queued for CHARTER v0.3 — acts with a precondition

Not an erratum: no signed page says this wrong, it cannot say it at all. Queued here so v0.3 carries it, with the measurement that forces it (§8 of v0) as the page's §0.

**§0, the measurement.** `gfrmin/wald-arena`, the AA-Omniscience showcase. `answer_second` submits the second opinion's answer; it is a terminal, so the World cannot make it wait for `second_opinion`. Two runs measured it.

*The dry run* (`12d9d23`, `showcases/omniscience/SCOREBOARD.md`; Haiku as primary, second opinion and grader; 150 test questions, p = 1; `answer_second` priced 0 in the World, so a blind switch was undercharged by c):

| c | wald consults / agreement | blind switches | total undercharge | per question | wald realised, with Counts | without Counts |
|---|---|---|---|---|---|---|
| 1/10 | 67% / 45% | 96 of 150 | 48/5 | 0.064 | −0.104 | −0.100 |
| 1 | 64% / 39% | 96 of 150 | 96 | **0.64** | −0.677 | −1.006 |

*Stage 2* (`100e250`, `runs/run/SCOREBOARD-stage2.md`; gpt-5.5 primary, Opus 5.5 second opinion, gemini-3.8-flash grader; 300 test questions, p = 1; the arena's workaround in force since 2026-09-27 — `answer_second` costs c in every state, so a blind switch is priced exactly and a switch after consulting is overcharged by c):

| c | wald consults / agreement | blind switches | switches after consulting / overcharge | wald realised, with Counts | without Counts |
|---|---|---|---|---|---|
| 0 | 100% / 14% | 98 of 300 | 6 / 0 | +0.497 | +0.472 |
| 1/20 | 50% / 66% | 105 of 300 | 0 / 0 | +0.459 | +0.422 |
| 1/10 | 38% / 80% | 60 of 300 | 0 / 0 | +0.408 | +0.360 |
| 1/4 and above | 0% / 36% | 0 | 0 / 0 | +0.347 | +0.370 |

None at p = 3 or p = 10 in either run. So the blind switch is common on real instruments too, at a cheap second opinion; and **the workaround's overcharge measured zero**: at every c > 0 the policy never consulted and then switched. What remains against it is not a number but that no constant in a utility prices both paths in general — it prices this policy on these instruments. **As of stage 2, no measurement forces this amendment.** It stays queued for the consumer whose policy does switch after consulting.

**What v0.3 is to say.** An act may declare a precondition: another act that must have been executed earlier in the episode. It enters M only once that act has been. This extends v0's menu rule, under which executing a `once` act already removes it from M (v0 §1's Menu, and M′ in §2): a precondition is the other direction, executing an act adds one. §2's M′ becomes "M without k if k is `once`, with every act whose precondition is k". M stays a function of the acts executed, never of what they reported. Places v0.3 must carry it: v0's T non-empty (T must be non-empty with no act executed); C5, C9 and v0.1's cap (whose proof relies on the root M containing every later menu — it no longer does); C2.S13's "any act of M at each step" and C2.S15's realisable designs (a record that fires `answer_second` before `second_opinion` is then refused PLATE); and SURFACE v0.3's syntax for declaring it. Open for the owner: whether a precondition may name only an observational act, and whether one act may have several.

## Queued for SURFACE v0.2 — folded into its §2 (draft 7)

1. **§3's "A parameter keeps its own source wherever it is read" admits two census readings** (attack on SURFACE v0.1, session 2, finding 4.2): the cell that reads a parameter counts under the table's source (what `laws/surface_check.py` has done since `surface-v0`) or under the parameter's. SURFACE v0.1 K17 fixes the former as the reading in force. No act changes; only a printed census.

## Cosmetic — for each page's next amendment

Signed pages are never edited: editing one breaks its tag, and `gfrmin/wald`'s `cage/fetch_charter.sh` refuses a page that differs from it. Nothing below changes a rule, a verdict or a number. Each is to be restated by the next amendment of that page.

1. **CHARTER v0.1's status line says "draft 6, unsigned."**, as signed at `charter-v0.1`. It is signed, and in force from that tag. To be restated in CHARTER v0.3. Found on reading, 2026-09-25.
2. **SURFACE v0.1's status line says "draft 4, unsigned."**, as signed at `surface-v0.1`. It is signed, and in force from that tag. To be restated in SURFACE v0.3. Found on reading, 2026-09-25.
3. **SURFACE v0.1's rulings table (K12–K18) has empty ruling and date cells.** The owner ruled the marks before signing, but the page never recorded them. SURFACE v0.3 is to record each ruling and its date from the owner's record, not from this file. Found on reading, 2026-09-25.
4. **SURFACE v0's attack log ends with a blank template**, "Signed as `surface-v0`: ___ claimed, ___ reproduced, resolved or carried to v0.1: ___." The four sessions above it are the record. To be filled or struck in SURFACE v0.3. Found on reading, 2026-09-25.

## Queued for SURFACE v0.3 (from kit v0.13, 2026-09-25)

1. **SURFACE v0.2's generated sections are as of signing.** Kit v0.13 grew the corpus (ten poisons and five lawful packs) and added four refusal sites: KERNEL_ROW under V2.5 (a row of the After-act's kernel that is not a distribution), PRICE under V2.5 (a negative After-act price), TABLE_SHAPE under V2.4 (an After-act row keyed by no state), DUPLICATE under V2.5 (one end written twice). Each of these is a refusal the signed rules already make. The page cannot be regenerated, so `laws/page_check.py` now checks that nothing the page lists has gone, and keeps the current rendering in `laws/generated/SURFACE-v0.2.md`, which SURFACE v0.3 carries in.
2. **An ending end's spelling `"end:act=outcome"` (V2.6) is not injective when a name holds `=`.** Act `a` with ending outcome `b=c` and act `a=b` with ending outcome `c` are two ends. V2.5 writes their After-act rows as `("a", "b=c")` and `("a=b", "c")`, which are distinct, but both spell `"end:a=b=c"`. The World's After-act kernel (`model.py`'s `End`) is keyed by the spelling, so kit v0.13's reference refuses such a pack DUPLICATE; before kit v0.13, one row silently replaced the other. Records are unaffected, because a record's last draw names the pair. Candidates: key ends by the pair, or forbid `=` in the name of an act with an ending outcome. Found by kit v0.13's work on QUESTIONS.md Q10e, 2026-09-25.
3. **V2.5 writes an ending end's After-act row as `(act, outcome)`.** The reference and the kernel also accept the string `"end:act=outcome"` there, and the page says nothing either way. Allowing one spelling would retire QUESTIONS.md Q10e's class, a key written twice under two spellings, from the After-act's table.
4. **QUESTIONS.md Q10f: After-act outcomes written as tuples.** No record can hold one (V2.6, K27), so they are probably unsayable, like a product kernel's outcomes. The reference accepts them, and `model.py` says an after-outcome is a name.
5. **QUESTIONS.md Q16: what a coding declaration is, and a byte-order mark.** The reference refuses a BOM as NOT_A_DECLARATION on every pack; the kernel refuses it as SYNTAX; Python's parser accepts one when it reads bytes. Kit v0.13's gate asks only that a BOM change every pack's verdict to one name, and the kit does not pin which.

## Measurements for SURFACE v0.3 — what a real host could not say compactly (gfrmin/wald#14, 2026-10-01)

These are not errata. SURFACE v0.2 says each of them as signed. They are recorded because a real host paid a measured price for each, and §8 of v0 asks for that price before any amendment. The host: the Renavon World (`renavon-monorepo`, branch `world/turn-one`, `world/make_pack.py`), with 81 Global values, 20,736 states, four `once` windows, 8 terminals and 70 monthly records. No amendment is drafted. Each item waits for a second consumer, or for this one to need the dropped part.

1. **An After-act's kernel is a full table only (V2.5).** "Reveal component X" is `point(X)` for an act, but an After-act has to spell it out as a row for every end and every state. Measured: 16 ends × 20,736 states = 331,776 cells, 21,787,173 bytes of pack text. The host dropped its After-act. Candidate: `point`, and the other kernel forms an act may use, for an After-act's rows.
2. **A utility that reads more than one component is a full state table.** `by` takes one component. A utility over four binary components would be 8 terminals × 20,736 states, about 12 MB, so the host fused the four into one 16-valued component to fit `by`. Candidate: `by` over a tuple of components.
3. **Counts cannot hold a product kernel's outcome (V2.14, K27).** A multi-component observation enters a record only as one `point` over a fused component, or as separate acts. This is the same class as item 4 of the kit v0.13 queue (Q10f, After-act outcomes as tuples). The two should be decided together.
4. **A `data` cell that nothing reads is refused (`UNREAD_PARAMETER`, S3).** The host wanted to keep a recorded measurement (the ECB rate, with its date) in the pack as provenance, and keeps it in a comment instead. Here S3 is working as intended: a number that no table reads cannot reach a choice, and the pack's census would count it anyway. Recorded as a cost the rule imposes. It is not, by itself, a reason to change the rule.
