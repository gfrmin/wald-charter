# Attack prompt — CHARTER v0.2 draft 5

You are given three pages: `CHARTER.md` (signed, tag `charter-v0`), `CHARTER-v0.1.md` (signed, tag `charter-v0.1`) and `CHARTER-v0.2.md` (draft, unsigned), and nothing else about the project. v0.2 lets a World learn across episodes: some dimensions of Ω are Globals, shared across a plate of episodes; an after-act reports on the state once the terminal act has fired; Counts of whole-episode records persist, and the next episode's prior over Globals is the declared prior conditioned on them.

Your job is to break v0.2. A finding counts only if it comes with a **complete World** (dimensions, which are Globals, P(Global), P(local | Global), acts with kernels and prices, the after-act's kernel for every terminal, terminals with utilities, N, d, and the Counts if any) and **exact rational arithmetic**. Findings without a World and arithmetic are discarded.

Categories, in order of weight:

1. **Two readings.** A World on which two careful readers of v0.2 would give a different prior for the next episode, or a different act, or a different refusal. Name both readings and the sentence that admits both.
2. **A false theorem.** A World on which C21–C25 or C27 fails while the kernel follows §4 exactly. (C26 is stated as not a theorem.)
3. **S15 wrong in either direction.** A World refused UNIDENTIFIED whose Globals some plate could in fact learn; or a World accepted whose Globals no plate can learn.
4. **An unlawful implementation the page cannot see.** One that breaks S11–S15 (carries a local, keeps a log, reads the after-act when deciding, persists something other than Counts) yet gives the reference's prior and act at every episode of every World. Say which clause it breaks and why no consequence distinguishes it.
5. **A hole in sufficiency.** A World and a plate where the prior from Counts differs from conditioning episode by episode on the full product Ω — or where Counts are not bounded by the number of distinct records.
6. **A numeral that escapes S3.** Behaviour that depends on a number in no declared table.
7. **Wording.** Sentences whose fix changes nothing. List them; they need no World.

Rules of engagement: quote the sentence you attack. Assume v0 and v0.1 exactly as signed. Prices ≥ 0; priors strictly positive; kernels rows sum to 1. Stop when you have nothing reproducible in categories 1–6, and report category 7 in full.
