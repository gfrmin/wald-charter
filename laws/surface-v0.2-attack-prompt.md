# Attack prompt — SURFACE v0.2 draft 6

You are given six pages and nothing else about the project: `CHARTER.md`, `CHARTER-v0.1.md` and `CHARTER-v0.2.md` (signed semantics), `SURFACE.md` and `SURFACE-v0.1.md` (signed syntax), and `SURFACE-v0.2.md` (draft), with the two lawful packs `appendix_a.py` and `appendix_a_shipped.py` as examples. SURFACE v0.2 gives a syntax to what CHARTER v0.2 adds: Global components, P(local | Global), the After-act, and shipped Counts with their digest, Score and falsifier.

Your job is to break SURFACE v0.2. You rule nothing and suggest no style changes. A finding counts only with a **complete pack**, and, where it claims a behaviour, the World it elaborates to and exact rational arithmetic.

Find, in order of value:

1. **Smuggling.** A pack the draft accepts that says what a signed page forbids: a utility or ending utility that reads a Global (CHARTER v0.2 S11) by any route; a second After-act, or one whose kernel reads more than the state and the end; Counts that are not facts — a record no episode of the World could write, multiplicities that are not whole, Counts whose digest does not pin them; a numeral in no table (S3); a prior or kernel number that escapes its source's fence.
2. **Unsayable.** A World lawful under CHARTER v0.2 — Globals, After-act, shipped Counts, falsifier and all — that no pack can express under the draft. Show the World in full.
3. **Ambiguity.** A pack with two reasonable readings that elaborate to different Worlds: a different prior, a different set of states, a different After-act kernel, a different digest. Show both Worlds and where the next act differs, exactly.
4. **Contradiction.** Two sentences — of the draft, or one of it and one of a signed page — that demand different verdicts on one pack. Watch: K20 (`prior` changing meaning), `by(...)` over a component that is Global, `reads` against the joint prior's support, the canonical encoding against a record holding non-ASCII names or `None`.
5. **A wrong census or a wrong digest.** A pack whose count of numerals by source, or whose digest under §3, is not what the draft's rules give.

Format of every finding: the pack in full; the sentences at issue, quoted; the verdicts, Worlds or digests, exact. A finding without a complete pack will be discarded unread.

Do every calculation in code with exact rationals. If you find nothing in a category, say "none found" and stop. Do not pad.
