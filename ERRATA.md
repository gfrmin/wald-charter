# ERRATA — queued for CHARTER v0.1

Signed pages are not edited (CHARTER §8). Wording found wanting is queued here with the evidence, and folded in at the next signed version.

1. **S3 does not name parameters in its list of tables**, though its last sentence ("Every declared parameter is read") presupposes them. Found by surface attack session 4 (2026-09-20). Reading in force meanwhile: SURFACE K11 — a parameter is a table cell written once and read by name. No act changes.

## Queued for CHARTER v0.3 (items 1 and 2 were queued for v0.2 and missed its signing; item 3 is on v0.2 itself)

1. **§1 of v0.1 names no clause for a Rate below zero**, though it writes r ∈ ℚ≥0. Found by the builder in brief 005a (`QUESTIONS.md` Q4, with the World). Reading in force meanwhile: a negative Rate is refused by the name RATE, the name the row already gives the Rate's source; SURFACE v0.1 says so, `meta_check.refuse_meta` moves to it at kit v0.8, and the kernel's one string follows in brief 005b. No act changes.

2. **v0.1 §1 names no source for Depth⁺ and no source for Score**, so under S3 either could be `data`, `elicited` or `fitted`. SURFACE v0.1 K18 fixes Depth⁺ as `elicited` (it is the owner's, fixed by J11) and Score as `data` (it is a measurement). Found by attack session 3 on SURFACE v0.1. No act changes.

3. **S14's Score gave the falsifying records no term**, though S13 has the prior condition on them (attack session 3 on SURFACE v0.2, finding 1.1). A pack could therefore ship a plate's data as "falsifying records" and move its learned prior while its Score stayed at the empty product, 1, the best any pack can have. **Corrected reading:** the leave-one-out product has a term for each copy of each record of the Counts and for each falsifying record, each under the prior conditioned on all the others. And a falsifying record is either a prefix — the draws up to and including a report that falsified the World inside an episode, with no end and no after-report — or a full record whose after-report falsified it; a full record with no after-report falsified nothing, and shipped as a falsifier it is refused PLATE. `laws/counts_check.py` implements both. No act changes; only the Score and what PLATE accepts. Adopted by SURFACE v0.2 K28, ruled by the owner on 2026-09-24, and in force from `surface-v0.2`, whose V2.7 and V2.8 state it in full and decide over C2.S13 and C2.S14 as the later page; CHARTER v0.3 is to restate it.

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
