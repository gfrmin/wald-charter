# CHARTER v0 — draft 2, for the author's ruling

Working name: **wald**. Status: unsigned. Nothing here is in force until the author's signed tag `charter-v0`.

Marks **[J1]–[J8]** are author judgements: they do not follow mechanically from anything. They are ruled in §9. Everything unmarked follows from §2.

## 0. Scope

One agent. A finite world whose latent state does not change during an episode: acts change what the agent knows, never what is true. All semantics in exact rationals.

**[J1]** Accept this cut. It admits address resolution, cryptic clues, cited question answering, diagnosis and Wordle. It excludes NetHack and interactive fiction until v2.

## 1. Nouns

| noun | what it is |
|---|---|
| World | the whole declaration below. A pack contains declarations only: no control flow. |
| Space Ω | finite, non-empty; given by a generator and a membership test |
| Prior | P₀ : Ω → ℚ≥0, summing to 1 |
| Kernel | K_k : Ω → Dist(B_k), B_k finite; every row sums to 1 by construction |
| Obs | a token (value in B_k, provenance set), minted only by the door when an observational act is executed |
| Belief | sealed; introduced only from the Prior, changed only by `condition` |
| Utility | u : Ω × T → ℚ over terminal acts T, and u_end over ending outcomes; the owner's; read only by `decide` and `report` |
| Price | price : O → ℚ≥0 over observational acts O, in utility units |
| Horizon | N: the most observational acts one episode may contain (the clock, in its v0 form) |
| Menu M | T then O, in declared order. Executing a `once` act removes it from M. |

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

An episode: n ← N. Repeat: a ← decide_n(b,M). If a is terminal the door fires it and the episode ends. Otherwise the door executes a and mints o; if o is an ending outcome the episode ends; else b ← b|a,o, M ← M', n ← n−1.

- **[J2]** Prices are additive to utility (the agent is risk-neutral in cost).
- **[J3]** Ties go to menu order, terminal acts first, so a tie prefers stopping.
- **[J4]** Ending outcomes are admitted in v0. They are what makes Wordle exact, and they cover "the probe happened to be the answer".

## 3. Structural rules — what cannot be said

- **S1 Single exit.** Only `decide` turns a belief into an act, and the door fires only acts minted by `decide`. `report` renders beliefs and values for display; a display value has no operations and flows nowhere.
- **S2 Linear evidence.** Every Obs is consumed by exactly one `condition`. Tokens whose provenance intersects can be consumed only together, by a kernel declared jointly over them. An observational act is declared `fresh` (each execution an independent draw) or `once`.
- **S3 Housed numerals.** Every numeral lives in a declared table (Prior, Kernel, Utility, Price, Horizon), and every table names its source: `data`, `elicited` or `fitted`. Nothing else in a pack contains a numeral other than 0 and 1. Every declared parameter is read. Scoreboards print the count of numerals by source.
- **S4 Normalised kernels.** Kernels are built only from combinators that preserve row sums: point, table, mixture, product, composition. A table whose row does not sum to 1 is refused.
- **S5 Zero evidence.** **[J5]** A World declares either a catch-all state ⊥ with P₀(⊥) > 0 and K_k(o|⊥) > 0 for every k and o, or itself `closed`. In a closed world an observation with P_b(o|k) = 0 ends the episode as WORLD_FALSIFIED. It is never silently handled.

## 4. Consequences — theorems of §2, tests in the kit, targets in Lean

If one of these fails on paper, §2 is wrong. `laws/spec_check.py` checks C1–C9 and S5 on random worlds, and checks that each poison agent is caught by at least one of them without consulting the reference.

- **C1 Coherence.** b ≥ 0 and Σ b = 1; P_b(·|k) ≥ 0 and sums to 1. Always.
- **C2 Order.** Conditioning on tokens with disjoint provenance commutes.
- **C3 Gauge.** Acts are unchanged by u ↦ a·u + c (terminal and ending utilities alike) together with price ↦ a·price, for a > 0.
- **C4 Sure-thing.** Adding any h(ω) to every terminal and ending utility changes no act.
- **C5 Free information.** Making observational acts that have no ending outcome free never lowers the policy's expected utility below that of acting at once.
- **C6 No book.** The price of a called-off bet before an observation equals its price after it. No finite set of accepted bets loses in every state.
- **C7 Self-calibration.** Under the declared model, among the outcomes after which the agent states probability p for an event, the event has frequency exactly p.
- **C8 Horizon.** A longer horizon never lowers the policy's expected utility.
- **C9 Dominance.** (a) A terminal act better than every other utility in every state is played at once. (b) An observational act priced above the whole utility range is never chosen.

## 5. Evaluators — anything that is not the reference

- **E1** The reference is the exact enumeration of §2 over ℚ. It is the definition.
- **E2** An exact fast path (dynamic programming, lazy partitions with bounds, pruning by act-invariance) attains the reference's value on every toy world. Any number it reports comes with an interval that contains the reference value. A fast path that drops hypotheses reports the dropped mass as a bound.
- **E3 The floor.** **[J6]** An evaluator may run rolling depth d < N: at each step it plays decide_d. This is the one declared approximation in v0. Its regret against decide_N is measured on toy worlds and printed on every scoreboard. v1 replaces the fixed d with priced, decided deliberation.
- **E4** No other approximation exists in v0. Learned parameters enter only as latent components of Ω. **[J7]** Point-estimate fitting is outside v0's semantics: a fitted pack is a different World (its tables say `fitted`), compared with its rivals on held-out log score.

## 6. Residues, named

The alphabet (§1–2). The clock (Price, Horizon). The pointer (whose Utility). The floor (E3). The small world (Ω, with ⊥ carrying the rest).

## 7. Out of scope for v0

Priced refinement and priced inference (v1; `refine` is the candidate fourth verb, admitted only under an executed failed composition). World dynamics (v2). Other agents. Continuous spaces.

## 8. Amendment

Only by a new signed version, carrying the measurement that forced it. **[J8]** The name.

## 9. Rulings

| mark | question | ruling | date |
|---|---|---|---|
| J1 | static latent, finite, one agent, exact rationals | accept | 2026-09-20 |
| J2 | prices additive to utility | accept | 2026-09-20 |
| J3 | ties to menu order, terminal first | accept | 2026-09-20 |
| J4 | ending outcomes in v0 | accept | 2026-09-20 |
| J5 | each World: catch-all ⊥, or `closed` with WORLD_FALSIFIED | accept | 2026-09-20 |
| J6 | the floor is rolling depth d, regret printed | accept | 2026-09-20 |
| J7 | fitting is outside the semantics; fitted packs compete on held-out log score | accept | 2026-09-20 |
| J8 | the name | wald | 2026-09-20 |

Attack session(s): ___ findings claimed, ___ reproduced in `spec_check.py`, all reproduced findings resolved: yes / no.

## Appendix — the first frozen vector (work it by hand before signing)

Ω = {sick, well}, P₀ = (1/5, 4/5), closed. T = {treat, leave}: u(sick,treat) = 0, u(well,treat) = −2, u(sick,leave) = −10, u(well,leave) = 0. One `once` test, price 1/2: K(+|sick) = 9/10, K(+|well) = 1/5. N = 1.

- E[treat] = −8/5, E[leave] = −2, so V_0 = −8/5 (treat).
- P(+) = 17/50. Posterior given +: sick 9/17, act treat, value −16/17. Given −: sick 1/33, act leave, value −10/33.
- Q_1(test) = (17/50)(−16/17) + (33/50)(−10/33) − 1/2 = −51/50.
- V_1 = −51/50 > −8/5, so decide_1 = **test**.
