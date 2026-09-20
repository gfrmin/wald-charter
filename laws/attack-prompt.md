# Attack prompt — paste into a fresh session that has seen nothing but CHARTER.md

You are given one page, CHARTER.md: the specification of a small language for a Bayesian decision-theoretic agent. Your only job is to break it. You rule nothing and you suggest no style changes.

Find, in order of value:

1. **Contradiction.** A World (explicit finite Ω, rational prior, kernels, utilities, prices, horizon) on which two sentences of the page demand different behaviour.
2. **Non-optimality.** A World on which `decide_N` as defined in §2 does not maximise expected utility over all policies that make at most N observations.
3. **False consequence.** A World on which one of C1–C9 fails although §2 and S1–S5 are obeyed.
4. **Ambiguity.** A sentence with two reasonable readings, and a World on which the two readings choose different acts.
5. **Escape.** Behaviour that obeys every rule as written yet is plainly not expected-utility maximisation for the declared (P₀, u, price, N). Say which rule's wording lets it through.

Format of every finding: the World in full, with every number a rational; the sentence(s) of the page at issue, quoted; the two behaviours or values, computed exactly, with the arithmetic shown. A finding without an explicit World and exact arithmetic will be discarded unread.

If you find nothing in a category, say "none found" and stop. Do not pad.
