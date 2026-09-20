# CHARTER v0

Name: **wald**. Status: in force from the author-signed tag `charter-v0`.

Marks **[J1]–[J10]** are author judgements: they do not follow mechanically from anything. They are ruled in §9. Everything unmarked follows from §2.

## 0. Scope

One agent. A finite world whose latent state does not change during an episode: acts change what the agent knows, never what is true. All semantics in exact rationals.

**[J1]** Accept this cut. It admits address resolution, cryptic clues, cited question answering, diagnosis and Wordle. It excludes NetHack and interactive fiction until v2.

## 1. Nouns

| noun | what it is |
|---|---|
| World | the whole declaration below. A pack contains declarations only: no control flow. |
| Space Ω | finite, non-empty; given by a generator and a membership test |
| Prior | P₀ : Ω → ℚ>0, summing to 1. A state of prior zero is not in Ω. |
| Kernel | K_k : Ω → Dist(B_k), B_k finite; every row sums to 1 by construction |
| Obs | a token (act, value in B_k), minted only by the door when an observational act is executed |
| Source | what an observational act reads beyond ω. A `once` act reads one private source, once. A `fresh` act reads a new private source at each execution. Any other source is a declared component of Ω (S2). |
| Belief | sealed; introduced only from the Prior, changed only by `condition` |
| Utility | u : Ω × T → ℚ over terminal acts T, and u_end over ending outcomes; the owner's; read only by `decide` and `report` |
| Price | price : O → ℚ≥0 over observational acts O, in utility units |
| Horizon | N: the most observational acts one episode may contain (the clock, in its v0 form) |
| Depth | d with 1 ≤ d ≤ N: the lookahead the clock affords. d = N is exact (E3). |
| Menu M | T then O, in declared order. T is non-empty. Executing a `once` act removes it from M. |

## 2. Verbs — this section is the semantics

```
push       P_b(o|k) = Σ_ω b(ω)·K_k(o|ω)          E_b[f] = Σ_ω b(ω)·f(ω)
condition  (b|k,o)(ω) = b(ω)·K_k(o|ω) / P_b(o|k)
decide     V_0(b,M)   = max_t E_b[u(·,t)]
           Q_n(b,M,k) = Σ_o P_b(o|k)·W − price(k)
             W = E_{b|k,o}[u_end(·,k,o)]   if o ends the episode
             W = V_{n-1}(b|k,o, M')        otherwise;  M' = M without k if k is `once`
           V_n(b,M)   = max( V_0(b,M), max_{k in M} Q_n(b,M,k) )
           decide_n(b,M) = the first entry of M attaining V_n(b,M)
```

Every Σ_o runs over the outcomes with P_b(o|k) > 0.

An episode: n ← N. Repeat: a ← decide_min(d,n)(b,M). If a is terminal the door fires it and the episode ends. Otherwise the door executes a, the episode pays price(a), the door mints o, and then, in this order: if P_b(o|a) = 0 the episode ends as WORLD_FALSIFIED (S5); else b ← b|a,o; then if o is an ending outcome the episode ends, earning u_end; else M ← M', n ← n−1.

The **value of a policy** is the expected utility its episodes earn, net of the prices they pay, under the declared model.

- **[J2]** Prices are additive to utility (the agent is risk-neutral in cost).
- **[J3]** Ties go to menu order, terminal acts first, so a tie prefers stopping.
- **[J4]** Ending outcomes are admitted in v0. They are what makes Wordle exact, and they cover "the probe happened to be the answer".

## 3. Structural rules — what cannot be said

- **S1 Single exit.** Only `decide` turns a belief into an act, and the door fires only acts minted by `decide`. `report` renders beliefs and values for display; a display value has no operations and flows nowhere.
- **S2 Independent, linear evidence.** **[J9]** Given ω, the outcomes of distinct executions are independent: whatever two observations share beyond ω is part of Ω. Each observational act is declared `once` or `fresh` and names the sources it reads. A source read by two acts, or by two executions of a `fresh` act, must be a declared component of Ω; otherwise the pack is refused. Every Obs that does not falsify the World is consumed by exactly one `condition`, ending outcomes included.
- **S3 Housed numerals.** Every numeral lives in a declared table (Prior, Kernel, Utility, Price, Horizon, Depth), and every table names its source: `data`, `elicited` or `fitted`. Nothing else in a pack contains a numeral other than 0 and 1. Every declared parameter is read. Scoreboards print the count of numerals by source.
- **S4 Normalised kernels.** Kernels are built only from combinators that preserve row sums: point, table, mixture, product, composition. A table whose row does not sum to 1 is refused.
- **S5 Zero evidence.** **[J5]** A World declares either a catch-all state ⊥ with K_k(o|⊥) > 0 for every k and o, or itself `closed`. ⊥ is a state like any other: its kernel rows are the pack's declared account of whatever it did not name, and S2 applies to it. In a closed world an observation with P_b(o|k) = 0 ends the episode as WORLD_FALSIFIED before anything else is done with it, whether or not it is an ending outcome. It is never silently handled.

## 4. Consequences — theorems of §2, tests in the kit, targets in Lean

If one of these fails on paper, §2 is wrong. They are necessary, not sufficient: no list of them characterises §2, and on toy worlds the sufficient check is E2. `laws/spec_check.py` checks C1–C11 and S5 on random worlds and prints, for each poison agent, which checks kill it. A poison that only E2 kills is a bug class that large worlds cannot see, which is why E5 exists.

- **C1 Coherence.** b ≥ 0 and Σ b = 1; P_b(·|k) ≥ 0 and sums to 1. Always.
- **C2 Order.** Conditioning on two tokens commutes.
- **C3 Gauge.** Acts are unchanged by u ↦ a·u + c (terminal and ending utilities alike) together with price ↦ a·price, for a > 0.
- **C4 Sure-thing.** Adding any h(ω) to every terminal and ending utility changes no act.
- **C5 Free information.** Making observational acts that have no ending outcome free never lowers the policy's expected utility below that of acting at once.
- **C6 No book.** The price of a called-off bet before an observation equals its price after it. No finite set of accepted bets loses in every state.
- **C7 Self-calibration.** Under the declared model, among the outcomes after which the agent states probability p for an event, the event has frequency exactly p.
- **C8 Horizon.** A longer horizon never lowers the policy's expected utility.
- **C9 Dominance.** Utilities here are terminal and ending alike. (a) A terminal act better in every state than every other utility is played at once. (b) An observational act whose price exceeds the largest utility minus the smallest is never chosen.
- **C10 Valuable information.** If n ≥ 1 and some observational act k in M has Q_1(b,M,k) > V_0(b,M), the act played is not terminal.
- **C11 Garbling.** With one look left, an observational act without ending outcomes that is a garbling of another such act in M listed before it, at no lower price, is not played.

## 5. Evaluators — anything that is not the reference

- **E1** The reference is the exact enumeration of §2 over ℚ. It is the definition.
- **E2** An exact fast path (dynamic programming, lazy partitions with bounds) may replace `push`, `condition` and expectation, nothing else. On every toy world, at the same d, the kernel running on it plays the reference's act at every reachable (b, M, n). Any number it reports comes with an interval that contains the reference value. It may leave hypotheses unevaluated only by carrying their mass as a bound, and only while the act returned is the Bayes act for every belief consistent with that bound; otherwise it evaluates more. This is exact, not an approximation.
- **E3 The floor.** **[J6]** The Depth d is declared by the World, a housed numeral like any other, with 1 ≤ d ≤ N. With n observations left the agent plays decide_min(d,n). d < N is the one declared approximation in v0. An evaluator is compared with the reference at the same d. The regret of d is the policy value at d = N minus the policy value at d; it is measured on toy worlds and printed on every scoreboard. v1 replaces the fixed d with priced, decided deliberation.
- **E4** No other approximation exists in v0. Learned parameters enter only as latent components of Ω. **[J7]** Point-estimate fitting is outside v0's semantics: a fitted pack is a different World (its tables say `fitted`), compared with its rivals on held-out log score.

- **E5 One `decide`.** **[J10]** The argmax, the lookahead and the episode loop exist once, in the kernel, and are checked there by E2. Packs and fast paths supply beliefs and values, never choices.

## 6. Residues, named

The alphabet (§1–2). The clock (Price, Horizon). The pointer (whose Utility). The floor (Depth, E3). The small world (Ω is all the agent can conceive; ⊥, where declared, is one of its states and not a window onto the rest).

## 7. Out of scope for v0

Priced refinement and priced inference (v1; `refine` is the candidate fourth verb, admitted only under an executed failed composition). World dynamics (v2). Other agents. Continuous spaces.

## 8. Amendment

Only by a new signed version, carrying the measurement that forced it. **[J8]** The name.

## 9. Rulings

| mark | question | ruling (accept / amend / reject) | date |
|---|---|---|---|
| J1 | static latent, finite, one agent, exact rationals | accept | 2026-09-20 |
| J2 | prices additive to utility | accept | 2026-09-20 |
| J3 | ties to menu order, terminal first | accept | 2026-09-20 |
| J4 | ending outcomes in v0 | accept | 2026-09-20 |
| J5 | each World: `closed` with WORLD_FALSIFIED, or a catch-all ⊥ that is an ordinary state (S2 applies to it; the page does not model "the rest") | accept | 2026-09-20 |
| J6 | the floor is a declared depth d, 1 ≤ d ≤ N; play is decide_min(d,n); regret against d = N printed | accept | 2026-09-20 |
| J7 | fitting is outside the semantics; fitted packs compete on held-out log score | accept | 2026-09-20 |
| J8 | the name | wald | 2026-09-20 |
| J9 | evidence is independent given ω; any shared source is a component of Ω; no joint kernels in v0 | accept | 2026-09-20 |
| J10 | one `decide`, in the kernel; packs and fast paths never choose | accept | 2026-09-20 |

Attack sessions:
- Session 1, on draft 2 (2026-09-20): 7 findings claimed (1a, 1b, 1c, 4a, 4b, 4c, 5), 7 reproduced in `spec_check.py`, all resolved in draft 3.
- Session 2, on draft 3 (2026-09-20): 8 findings claimed (1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 4.1, 5.1), 8 reproduced, all resolved in draft 4. Finding 5.1 is resolved by concession: the consequences are necessary only (§4), and E5 confines the bug class to the kernel, where E2 sees it.
- Session 3, on draft 4 (2026-09-20): 4 findings claimed (4.1–4.4), all ambiguities, none in categories 1, 2, 3 or 5 under every reading; 4 reproduced; each resolved in draft 5 by fixing the reading `spec_check.py` already implemented. No act of §2 changed. Nothing is carried to v0.1.

## Appendix — the first frozen vector (work it by hand before signing)

Ω = {sick, well}, P₀ = (1/5, 4/5), closed, d = 1. T = {treat, leave}: u(sick,treat) = 0, u(well,treat) = −2, u(sick,leave) = −10, u(well,leave) = 0. One `once` test, price 1/2: K(+|sick) = 9/10, K(+|well) = 1/5. N = 1.

- E[treat] = −8/5, E[leave] = −2, so V_0 = −8/5 (treat).
- P(+) = 17/50. Posterior given +: sick 9/17, act treat, value −16/17. Given −: sick 1/33, act leave, value −10/33.
- Q_1(test) = (17/50)(−16/17) + (33/50)(−10/33) − 1/2 = −51/50.
- V_1 = −51/50 > −8/5, so decide_1 = **test**.
