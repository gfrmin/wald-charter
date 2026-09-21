# ERRATA — queued for CHARTER v0.1

Signed pages are not edited (CHARTER §8). Wording found wanting is queued here with the evidence, and folded in at the next signed version.

1. **S3 does not name parameters in its list of tables**, though its last sentence ("Every declared parameter is read") presupposes them. Found by surface attack session 4 (2026-09-20). Reading in force meanwhile: SURFACE K11 — a parameter is a table cell written once and read by name. No act changes.

## Queued for CHARTER v0.2

1. **§1 of v0.1 names no clause for a Rate below zero**, though it writes r ∈ ℚ≥0. Found by the builder in brief 005a (`QUESTIONS.md` Q4, with the World). Reading in force meanwhile: a negative Rate is refused by the name RATE, the name the row already gives the Rate's source; SURFACE v0.1 says so, `meta_check.refuse_meta` moves to it at kit v0.8, and the kernel's one string follows in brief 005b. No act changes.

## Queued for SURFACE v0.2

1. **§3's "A parameter keeps its own source wherever it is read" admits two census readings** (attack on SURFACE v0.1, session 2, finding 4.2): the cell that reads a parameter counts under the table's source (what `laws/surface_check.py` has done since `surface-v0`) or under the parameter's. SURFACE v0.1 K17 fixes the former as the reading in force. No act changes; only a printed census.
