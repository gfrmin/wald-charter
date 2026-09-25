# ERRATA — queued for CHARTER v0.1

Signed pages are not edited (CHARTER §8). Wording found wanting is queued here with the evidence, and folded in at the next signed version.

1. **S3 does not name parameters in its list of tables**, though its last sentence ("Every declared parameter is read") presupposes them. Found by surface attack session 4 (2026-09-20). Reading in force meanwhile: SURFACE K11 — a parameter is a table cell written once and read by name. No act changes.

## Queued for CHARTER v0.3 (items 1 and 2 were queued for v0.2 and missed its signing; item 3 is on v0.2 itself)

1. **§1 of v0.1 names no clause for a Rate below zero**, though it writes r ∈ ℚ≥0. Found by the builder in brief 005a (`QUESTIONS.md` Q4, with the World). Reading in force meanwhile: a negative Rate is refused by the name RATE, the name the row already gives the Rate's source; SURFACE v0.1 says so, `meta_check.refuse_meta` moves to it at kit v0.8, and the kernel's one string follows in brief 005b. No act changes.

2. **v0.1 §1 names no source for Depth⁺ and no source for Score**, so under S3 either could be `data`, `elicited` or `fitted`. SURFACE v0.1 K18 fixes Depth⁺ as `elicited` (it is the owner's, fixed by J11) and Score as `data` (it is a measurement). Found by attack session 3 on SURFACE v0.1. No act changes.

3. **S14's Score gave the falsifying records no term**, though S13 has the prior condition on them (attack session 3 on SURFACE v0.2, finding 1.1). A pack could therefore ship a plate's data as "falsifying records" and move its learned prior while its Score stayed at the empty product, 1, the best any pack can have. **Corrected reading:** the leave-one-out product has a term for each copy of each record of the Counts and for each falsifying record, each under the prior conditioned on all the others. And a falsifying record is either a prefix — the draws up to and including a report that falsified the World inside an episode, with no end and no after-report — or a full record whose after-report falsified it; a full record with no after-report falsified nothing, and shipped as a falsifier it is refused PLATE. `laws/counts_check.py` implements both. No act changes; only the Score and what PLATE accepts. Adopted by SURFACE v0.2 K28, ruled by the owner on 2026-09-24.

## Queued for SURFACE v0.2 — folded into its §2 (draft 7)

1. **§3's "A parameter keeps its own source wherever it is read" admits two census readings** (attack on SURFACE v0.1, session 2, finding 4.2): the cell that reads a parameter counts under the table's source (what `laws/surface_check.py` has done since `surface-v0`) or under the parameter's. SURFACE v0.1 K17 fixes the former as the reading in force. No act changes; only a printed census.
