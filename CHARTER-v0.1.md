# CHARTER v0.1 — amendment: the think act

Name: **wald**. Status: **draft 6, unsigned.** In force from the author-signed tag `charter-v0.1`, together with `charter-v0`. Where the two pages speak of the same thing, this page decides; everything it does not mention stands as signed. Nothing in v0 is edited (§8 of v0). `SURFACE.md` (signed, tag `surface-v0`) is the syntax of packs; this page uses two of its words: a **Parameter** is a table cell written once and read by name (its K11), and a table is **fenced** when its source is `fitted` (its §3).

Marks **[J11]–[J18]** are author judgements: they do not follow mechanically from anything. They are ruled in §9. Everything unmarked follows from §2 of v0 and §2 below.

Throughout, at a step with n observations left, **V_d, decide_d, V_{d⁺} and decide_{d⁺}** are shorthand for V_min(d,n), decide_min(d,n), V_min(d⁺,n) and decide_min(d⁺,n) (E3). Every V and decide of v0 §2 is evaluated over the menu **without θ**: θ is an entry of decide⁺'s menu (§2 below) and of nothing else.

## 0. What forced this

E3 of v0 said the fixed depth d is the one declared approximation and that v1 would replace it with priced, decided deliberation. The measurement: on 200 common words the regret of the floor is zero — depth 2 costs about twenty times the operations of depth 1 and changes no outcome; on 126 near-twin words depth 2 removes two of four wrong claims. There is a World where deeper thought is waste and a World where it pays, and no fixed d is right in both. This page lets the World price the thought and the one `decide` buy it. Metacomputation here means what it means in Good and in Russell & Wefald: deciding when an approximation is justified, for expected utility, with the regress ended by a floor.

## 1. Nouns added

| noun | what it is |
| --- | --- |
| Think act θ | an entry of decide⁺'s menu, listed after O. Executing it evaluates v0 §2 at depth d⁺ instead of d for the current step, over M without θ. It mints no Obs, reads no source, changes no belief, removes nothing from M and consumes no horizon. The door never sees it. |
| Depth⁺ d⁺ | the depth a think act buys, a housed numeral. **[J11]** In v0.1 a World that declares θ declares d = 1, d⁺ = 2 and N ≥ 2: one look ahead at the floor, then at most one think act per step buying a second. Any other d, d⁺ or N alongside θ is refused by the name DEPTH_PLUS; a World without θ keeps v0's d. |
| Meta-belief | a housed number read as the mean of a belief about the agent's own computation. Not a Belief of v0 §1: it comes from a table, is conditioned on nothing, and is changed by no verb within an episode. There are two, Fraction and Cost. |
| Cap | best(ω) = max( max_{t ∈ T} u(ω,t), max u_end(ω,k,o) over k ∈ M∩O and ending o with K_k(o\|ω) > 0 ); cap(b, M) = max( V_0(b,M), Σ_ω b(ω)·best(ω) − min_{k ∈ M∩O} price(k) ), and V_0(b,M) when M∩O = ∅. For each ω the inner max is omitted when no act in M∩O has an ending outcome its kernel can emit in ω. The value of an agent that stops now, or pays the cheapest price, is told ω and handed the outcome it wants among those a kernel can emit in ω. **[J12]** |
| Gain bound | ĝ(b,M,n) = 0 if n ≤ d or M∩O = ∅; otherwise cap(b,M) − V_d(b,M). |
| Fraction | f ∈ ℚ with 0 ≤ f ≤ 1: the meta-belief about V_{d⁺} − V_d, the rise in the lookahead value the thought returns, as a share of the room ĝ. That rise lies in [0, ĝ] and utility is linear, so only the mean is read. The act then played is decide_{d⁺} whatever the rise (C17): a rise of 0 can still change the act, by J3. One number per World, housed; its source is `elicited` or `fitted`, any other is refused by the name FRACTION. A `fitted` f is learned across episodes (J7); no f changes within one. **[J17]** |
| Operation | one arithmetic operation on ℚ performed by `push`, `condition` or expectation in the evaluator that runs. The unit of computation. Never a clock. |
| Cost | ops : {1, …, \|Ω\|} → ℚ≥0, one cell for each s from 1 to \|Ω\|, where s(b) is the number of states of positive belief mass — states as the World names them, so two states with identical rows are two states (a state written twice is not a pack: SURFACE refuses it, DUPLICATE). The meta-belief about the operations one think act takes at s live states. The keys are indices, not numerals of the census; the cells are table cells, not Parameters. A missing cell is refused by the name COST. Housed; source `elicited` or `fitted`, any other refused by the name COST. A `fitted` Cost is learned across episodes; none changes within one. **[J13]** |
| Rate | r ∈ ℚ≥0, utility per operation: the owner's exchange rate. Housed; its source is `elicited`, any other is refused by the name RATE. |
| Predicted cost | c(b) = r · ops(s(b)). |
| Score | the held-out score a `fitted` Fraction or Cost carries (S10): a housed numeral read by the scoreboard, not by a verb. |

decide⁺'s menu is **T then O, in declared order, then θ**. A World that declares no θ is a v0 World and plays as v0. **[J14]**

## 2. Verbs — the added semantics

```
think      ĝ(b,M,n) = 0                    if n ≤ d or M∩O = ∅
           ĝ(b,M,n) = cap(b,M) − V_d(b,M)  otherwise
           c(b)     = r · ops(s(b))
           θ is struck at this step         if ĝ ≤ c          (bounds settle it; f is not read)
           Q(b,M,θ) = V_d(b,M) + f·ĝ − c   otherwise
           decide⁺(b,M,n) = decide_d(b,M)                if θ is struck
           decide⁺(b,M,n) = the first entry of (M then θ) attaining max( V_d(b,M), Q(b,M,θ) )   otherwise
```

Executing θ: the episode pays c, the kernel then evaluates a⁺ = decide_{d⁺}(b,M) over M without θ, and a⁺ is played as if `decide` had minted it: fired by the door if terminal, executed if observational. θ is executed at most once per step.

An episode is as in v0 with a ← decide⁺(b,M,n) in place of decide_d(b,M); if a = θ the kernel executes it and a ← a⁺; the rest is unchanged, and n is not decremented by θ. When the World declares no θ, decide⁺ is decide_d.

The **value of a policy** is the expected utility its episodes earn, net of the prices they pay and of the predicted costs c of the think acts they execute, under the declared model. Realised operations are a scoreboard measurement (E6) and enter no value. **[J15] [J16]**

Proof that the bounds are bounds. V_m ≤ V_n for m ≤ n, at every (b, M′) including the menus `once` leaves behind: V_n = max(V_0, max_k Q_n(k)) and Q_n ≥ Q_{n−1} by induction on n over all (b, M′), the base being V_1 ≥ V_0 everywhere. V_n ≤ cap: an episode either stops at once, earning at most V_0, or plays an observational act, paying at least the cheapest price in M, and ends by earning some u(ω,t) or some u_end(ω,k,o) with K_k(o\|ω) > 0 under the state ω that obtains, for a k in the root M, which contains every later menu; best(ω) is the largest such earning in that state and the cap averages it under b. The per-state form is what makes this a bound: valuing ending branches at the root posterior instead is below V_N on a World in `laws/meta_check.py` (FIXED_CAP), where an ending outcome pays in the state it is evidence against and a cheap act can reveal ω first. When n ≤ d the deeper evaluation is the same evaluation, and when M∩O = ∅ there is nothing to look ahead through, so V_{d⁺} = V_d in both and ĝ = 0 is exact; otherwise ĝ = cap − V_d. Hence V_{d⁺} − V_d ≤ ĝ always, and ĝ = 0 also whenever cap = V_d. Q(b,M,θ) therefore lies in [V_d − c, V_d + ĝ − c].

What the cap is for. It assumes ω revealed and the outcome chosen, so it is loose: on a World like Wordle, whose utility is minus the guesses, the room ĝ is about the mean number of guesses still to come, and bounds alone will rarely settle the don't-think direction. Its job in v0.1 is to make the scale of f proven and cheap to compute, not to prune; the tighter per-state bound is deferred (§7).

## 3. Structural rules — amended and added

S6–S10 are rules about the computation behind an act, like S1 and E5 of v0. An agent that breaks one of them while firing the reference's act at every node with the reference's value exists (attack session 1, category 3: an evaluator that computes depth d⁺ eagerly and charges c anyway; a rescaled f outside [0,1] against an unproven bound; a decider outside `decide`; a fitted table labelled `elicited`). No consequence and no act-by-act comparison can see such an agent. They are judged as S1 and E5 are: by the structural kit, by the import lint, and by the author's reading of the kernel before merge. Not by the numbers: the realised operation count (E6) is the kernel's own report, and an evaluator that computes depth d⁺ eagerly can book that count against the step where θ is bought (attack session 2).

- **S3 Housed numerals** (amended; folds ERRATA 1). Every numeral lives in a declared table (Prior, Kernel, Utility, Price, Horizon, Depth, Depth⁺, Fraction, Cost, Rate, Score) or is a declared Parameter, and every table and Parameter names its source: `data`, `elicited` or `fitted`. Nothing else in a pack contains a numeral other than 0 and 1. Every declared Parameter is read (a Parameter is a named cell; this reading of v0's sentence supersedes the lower-case one, so an unreachable Cost cell is not unread). Scoreboards print the count of numerals by source and the count of judgements in force.
- **S6 Meta-beliefs inside proven bounds.** The agent holds two meta-beliefs, Fraction and Cost, and no other. 0 ≤ f ≤ 1 and every ops cell is ≥ 0; a pack outside this is refused by the name FRACTION or COST. Every value the kernel forms about a thought lies inside a bound this page proves (§2). No meta-belief is formed about anything the page has not bounded, and none is changed within an episode.
- **S7 Bounds first.** When ĝ ≤ c the think act is struck and f is not read. The kernel counts, per episode, every step of the loop including one at n = 0, each in the first bucket that applies: struck because n ≤ d or M∩O = ∅; struck because cap − V_d ≤ c; Q(θ) formed and θ not bought; θ executed. The scoreboard prints the four counts.
- **S8 One menu.** θ is an entry of decide⁺'s menu chosen by the one `decide` (E5) and by nothing else: there is no second World and no separate meta-decider. Its five negatives are in the Think act noun.
- **S9 At the floor.** The decision to execute θ reads V_d(b,M), cap(b,M), M, s(b), n and the declared tables, and nothing else; it plays decide_d(b,M) when θ is not bought. Nothing evaluated at depth d⁺ is consulted before θ has been executed and paid for.
- **S10 Learned tables.** A Fraction or Cost with source `fitted` is fenced and its pack carries its Score; a fitted meta-table without a Score is refused by the name UNSCORED. **[J18]**

## 4. Consequences — theorems of §2, tests in `laws/meta_check.py`

Necessary, not sufficient, as in v0 §4. Several poisons are seen only by the act-by-act comparison (E2), which is why E5 exists; the agents of §3's first paragraph are seen by nothing here.

**Standing of v0's consequences under θ.** C1, C2, C6, C7 concern beliefs and are untouched. C3 and C4 become C13 and C14. C9(a): a terminal act better in every state than every other utility has best(ω) = u(ω,t) in every state, so cap = V_0 = V_d, ĝ = 0, θ is struck and t is played at once. C9(b) holds at any depth. C10: if some Q_1(k) > V_0 then V_min(d,n) ≥ V_1 > V_0 for n ≥ 1, so neither decide_d nor decide_{d⁺} is terminal. C11's one look left is n = 1 ≤ d, where θ is struck and decide_d is v0's. **C5 and C8 do not hold for the adaptive policy** and are exempted for a World that declares θ: they are theorems of the exact policy, and the adaptive agent is a floor policy whose thought is priced on a belief. Making an act free can raise the cap and buy a thought that returns nothing (World S1-2B of `laws/meta_check.py`: with the act free, the policy is worth 1/4, and V_0 is 1/2); a longer horizon is more steps at which the same can happen (World S1-2A there: Appendix A at N = 3 is worth −161/125 against −61/50 at N = 2, fixed d unchanged). Both are C18 at work and both are measured by E3, as the regret of the floor already was in v0.

- **C12 Bounds.** At every reachable (b, M, n): V_d(b,M) ≤ V_m(b,M) ≤ cap(b,M) for every d ≤ m ≤ n (vacuous at n = 0), and θ is never executed when n ≤ d or M∩O = ∅.
- **C13 Gauge.** No act and no think decision changes under u ↦ a·u + e (terminal and ending alike), price ↦ a·price and r ↦ a·r, for a > 0 and any constant e. f is dimensionless.
- **C14 Sure-thing.** Adding any h(ω) to every terminal and ending utility changes no act and no think decision; ĝ is unchanged.
- **C15 Cost dominance.** If f = 0, θ is never executed: where bounds settle it, it is struck; where Q(θ) is formed, Q(θ) = V_d − c is a strict refusal for c > 0 and a tie at c = 0, and a tie goes to menu order (J3, J14). If r · min_s ops(s) ≥ max − min over every u and u_end the World declares, θ is never executed: the cheapest thought costs more than the widest gap.
- **C16 Free thought.** If r = 0 and f = 1, θ is executed at exactly the steps with ĝ > 0.
- **C17 Bought is played.** Whenever θ is executed the act played is decide_{d⁺}(b,M): the act played at that (b, M, n) by the v0 World obtained by deleting θ, Fraction, Cost, Rate and Score and setting d = d⁺.
- **C18 Not a theorem.** V_{d⁺} ≥ V_d at a node does not make the d⁺ policy worth more than the d policy over an episode; the regret of the floor is measured (E3), not proven. This is why f is a belief and not a bound, why C5 and C8 are exempted above, and why the omniscient meta-policy is an oracle and not a law.
- **C19 The cap is not deliberation.** cap(b,M) reads no lookahead value at all — only V_0, best(ω) and the prices — and no d⁺: a kernel handed a different d⁺ forms the same cap and, at a node, the same decision — struck, refused, or bought; only the act bought could differ. (The kit probes this on Worlds it constructs; a pack with d⁺ ≠ 2 is refused, J11.)
- **C20 Monotone price at a node.** At a node, raising r never turns a refused or struck θ into a bought one. Over an episode the number of thoughts can rise with r, because the dearer agent may play a different act and reach nodes the cheaper one did not (World S1-2C of `laws/meta_check.py`: r 1/25 → 11/25 raises the expected number of thoughts from 1 to 19/15).

## 5. Evaluators — amended and added

- **E3 The floor** (amended). This supersedes v0's E3 "With n observations left the agent plays decide_min(d,n)", J6's "play is decide_min(d,n)", and E3's last sentence, for a World that declares θ: v0.1 prices the deeper depth and lets `decide` buy it. The scoreboard prints, at the declared r and along a grid of r that lives in the kit, not in any pack: the policy value at fixed d; at fixed d⁺, paying c at every step with n > d and M∩O ≠ ∅; at the best fixed depth in hindsight; adaptive (this page); and under the omniscient meta-policy — the exact solution of the meta-decision problem, which at every node buys θ or not to maximise the value of its own continuation net of c, computed by dynamic programming over the episode tree in `laws/meta_check.py`. r is the x-axis, never a ruling.
- **E2** (amended). Under θ the comparison is at the same d, d⁺, f, ops and r, and the kernel plays the reference's act and makes the reference's think decision — struck, refused, or bought — at every reachable (b, M, n).
- **E6 The operation counter.** The kernel counts the operations performed while θ executes, in whatever evaluator runs (E1 or an E2 fast path). The count is a scoreboard measurement: printed beside the predicted ops for every think act, read by no verb, and a self-report (§3). Two evaluators may count differently; each prints its own count beside the same prediction.

## 6. Residues, named

To v0 §6 add: the meta-beliefs (f and ops, inside the bounds, unchanged within an episode). The unit (an operation, as the evaluator that runs counts it; it counts states as named, so two states with identical rows are two rows of arithmetic — the same beliefs, the same acts, a dearer thought).

## 7. Deferred to v0.2, each its own amendment

A Fraction or Cost that reads features beyond s(b) (live continuations, n, the stop-versus-look gap) — stage 2 of the plan, exchangeable counts clipped inside §2's bounds and held-out scored. A Cost that updates within an episode from the realised count of an earlier thought: the kernel would then mint an observation about itself, a source behind the door, which touches S1 and S2. The tighter cap: ω known, outcomes still random, no belief branching. d⁺ > 2 or a second think act in one step. Until then v0.1 takes the simplest form that is defensible, and says so.

## 8. Amendment

Unchanged. This page is the first measurement-forced amendment; §0 carries the measurement.

## 9. Rulings

| mark | question | ruling (accept / amend / reject) | date |
| --- | --- | --- | --- |
| J11 | a World with θ declares d = 1 and d⁺ = 2, else refused DEPTH_PLUS; one think act per step; other depths are an amendment | accept | 2026-09-21 |
| J12 | the cap: perfect information, chosen outcome, less the cheapest price, restricted to M; its job is a proven scale for f, not pruning; the tighter cap is an amendment | accept | 2026-09-21 |
| J13 | the cost is a belief; in v0.1 a point belief keyed on live states alone, learned across episodes by fitting, never within one; `decide` reads its mean, never a measured count | accept | 2026-09-21 |
| J14 | θ is last in decide⁺'s menu, so a tie between V_d and Q(θ) does not think | accept | 2026-09-21 |
| J15 | the policy value charges the predicted cost c; realised operations are printed, never charged | accept | 2026-09-21 |
| J16 | θ consumes no horizon: computation is priced in utility (r), not in the clock (N) | accept | 2026-09-21 |
| J17 | f is the mean of a belief about the thought's result; in v0.1 one point belief per World, learned across episodes by fitting; feature-keyed tables are stage 2 and an amendment | accept | 2026-09-21 |
| J18 | a `fitted` Fraction or Cost must carry a Score or the pack is refused | accept | 2026-09-21 |

Ruled by the owner's direction of 2026-09-21: v0.1 takes the simplest defensible form and defers the rest (§7). J19 of draft 2 (free thought at f = 0) is struck: it is a tie and J3 already rules ties (C15).

Numbers awaiting the owner's ruling, to be housed in packs, not on this page: f for the common-word pack and for the near-twin pack; r for the scoreboards. The grid of r for the sweep lives in the kit.

Attack sessions:

- Session 1, on draft 3 (2026-09-21): 7 findings claimed in categories 1–5 (1a, 2a, 2b, 2c, 3a–d, 4a, 5a, 5b) and 19 in category 6; 7 reproduced in `laws/meta_check.py` as Worlds (1a, 2a, 2b, 2c, 4a, 5a by construction, 6.5). Resolved in draft 4: 1a and 4a by the Throughout line; 2a and 2b by concession — C5 and C8 are exempted for the adaptive policy (§4); 2c by restating C20 at a node; 3a–d by concession — S6–S10 are structural rules judged as S1 and E5 are (§3); 5a by adding Score to S3; 5b by moving the sweep grid to the kit. All 19 wording items taken. No act of §2 changed.
- Session 2, on draft 4 (2026-09-21): categories 2 and 4 clean on 5,000 random Worlds and on paper. 3 findings claimed in categories 1, 3, 5 (1.1, 3, 5) and 28 in category 6; 1.1 and 5 reproduced as Worlds in `laws/meta_check.py` (COIN, A′); 3 is indistinguishable by construction and is not a World. Resolved in draft 5: 1.1 by attaching the name DEPTH_PLUS to J11's (d, d⁺) = (1, 2) — under the other reading a pack with d⁺ = 3 would run and buy `test` for −1/90; 3 by withdrawing the claim that E6 witnesses an eager evaluator (§3); 5 as a residue (§6). Vector B's provenance moved here: it is the frozen vector of the other author-side draft of 2026-09-21. All 28 wording items taken. No act of any admitted World changed.
- Session 3, on draft 5 (2026-09-21): categories 2, 4, 5 clean on 3,000 random Worlds and on paper; 1 marginal reading (1.a, s(b) counts states or rows), 1 agent in the class §3 concedes (3.a, forms Q(θ) where bounds settle it: same act, same value, everywhere), 19 wording items. 1.a resolved in draft 6 by a clause, not a change: a state written twice is refused by SURFACE (DUPLICATE), so two states with identical rows are two states, which is what s(b) already counted. All 19 wording items taken. No act of any admitted World changed. The session reported nothing further reproducible in categories 1–5 and stopped.

## Appendix — two frozen vectors (work them by hand before signing)

**A. The thought that changes nothing.** Ω = {sick, well}, P₀ = (1/5, 4/5), closed, N = 2, d = 1, d⁺ = 2. T = {treat, leave}: u(sick,treat) = 0, u(well,treat) = −2, u(sick,leave) = −10, u(well,leave) = 0. One `fresh` test, price 1/2: K(+\|sick) = 9/10, K(+\|well) = 1/5. f = 1/2 (`elicited`), ops(1) = 100, ops(2) = 200, r = 1/1000 (`elicited`).

- At the root, n = 2, s = 2. V_1 = −51/50, decide_1 = test (as in the v0 appendix). best(ω) = 0 in either state; cap = max(V_0 = −8/5, 0 − 1/2) = −1/2. ĝ = 13/25. c = (1/1000)·200 = 1/5. ĝ > c, so Q(θ) is formed: Q(θ) = −51/50 + (1/2)(13/25) − 1/5 = −24/25 > −51/50. **θ is executed.**
- Depth 2 by hand: after +, b = (9/17, 8/17), V_0 = −16/17 (treat); Q_1(test) = (97/170)(−32/97) + (73/170)(−90/73) − 1/2 = −207/170 < −16/17, so V_1(b\|+) = −16/17. After −, b = (1/33, 32/33), V_0 = −10/33 (leave); Q_1(test) = (73/330)(−90/73) + (257/330)(−10/257) − 1/2 = −53/66 < −10/33, so V_1(b\|−) = −10/33. Hence Q_2(test) = Q_1(test) and V_2 = V_1 = −51/50: a⁺ = **test**. The thought changed nothing and cost 1/5.
- Second step, n = 1 ≤ d: ĝ = 0, θ struck, f not read. Fixed-d policy value −51/50; adaptive −61/50; the omniscient meta-policy does not think here. With r = 1/100, c = 2 > ĝ and bounds settle it at the root. With f = 0 the agent never thinks; with r = 0 and f = 1 it thinks at the root.

**B. The thought that changes the act.** Vector A with two changes before any number: `test` becomes `once`, and a second `once` act `scan` is added after it, price 1/5: K(y\|sick) = 9/10, K(y\|well) = 2/5. Same f, ops, r.

- V_1 = −51/50 (test). V_2 = −479/500 (**scan**). cap = max(−8/5, 0 − 1/5) = −1/5; ĝ = 41/50; c = 1/5. Q(θ) = −51/50 + 41/100 − 1/5 = −81/100 > −51/50: **θ is executed and scan is played.** At r = 1/400, c = 1/2 > 41/100: Q(θ) is formed and θ is not bought. At r = 1/200, c = 1 > ĝ: bounds settle it.
- The thought is worth V_2 − V_1 = 31/500 of policy value and cost 1/5: the adaptive agent, predicting f·ĝ = 41/100, buys it at a loss of 69/500; the omniscient meta-policy does not buy it. This is C18 in one World, and the reason f is elicited per World and swept on the scoreboard.
