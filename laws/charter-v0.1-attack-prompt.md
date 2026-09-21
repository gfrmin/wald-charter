# Attack prompt — CHARTER v0.1 draft 1

You are given two pages, `CHARTER.md` (signed, tag `charter-v0`) and `CHARTER-v0.1.md` (draft, unsigned), and nothing else about the project. v0.1 amends v0 by adding a "think act": a computation to a deeper lookahead depth, priced in declared operations, placed on the agent's menu and chosen by the same `decide` as every other act.

Your job is to break v0.1. A finding counts only if it comes with a **complete World** (states, prior, terminal utilities, observational acts with kernels, prices, ending outcomes if any, N, d, d⁺, f, ops table, r) and **exact rational arithmetic** showing the page's words produce the claimed behaviour. Findings without a World and arithmetic are discarded.

Categories, in order of weight:

1. **Two readings.** A World on which two careful readers of v0.1 would have the agent take different acts, or execute or not execute θ, or charge different costs. Name both readings and the sentence that admits both.
2. **A false theorem.** A World on which one of C12–C17 fails while the agent follows §2 exactly. (C18 is stated as not a theorem; a World showing V_{d⁺} > V_d at a node while the d⁺ policy is worth less than the d policy is welcome as confirmation but is not a finding.)
3. **An unlawful agent the page cannot see.** An agent that breaks S6–S10 (a meta-belief outside the bounds, reading f when bounds settle it, a second decider, consulting the deeper value before paying, a fitted table without a score) yet plays the reference's act at every node of every World with the reference's value. State which clause it breaks and why no consequence and no act-by-act comparison distinguishes it.
4. **A hole in the bounds.** A World on which cap(b,M) < V_n(b,M) for some reachable node, or on which ĝ = 0 while V_{d⁺} > V_d.
5. **A numeral that escapes S3.** A way to write a pack under v0.1 whose behaviour depends on a number that is not in one of the ten named tables or a declared Parameter.
6. **Wording.** Sentences whose fix changes no act. List them; they need no World.

Rules of engagement: quote the sentence you attack. Do not propose fixes unless the fix is a single word. Do not assume a `host` form, wall-clock time, or any table the page does not name. Assume `once`/`fresh`, ending outcomes, and `closed` Worlds exactly as v0 defines them. Prices are ≥ 0; prior masses are > 0; f ∈ [0,1]; ops ≥ 0; r ≥ 0.

Stop when you have nothing reproducible in categories 1–5. Report category 6 in full.
