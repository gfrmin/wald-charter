# Violators — one per rule, so that every rule is known to forbid something

These are intent-level. The surface syntax does not exist yet; build step 3 turns each into a poison file the checker must reject. A rule for which no violator can be written says nothing and should be deleted. Semantic bug classes (gates, double counting, tempering, max-for-sum, ignored prices) are in `spec_check.py` as poison agents.

## S1 Single exit
```python
out = resolve(text)
if out.confidence < 0.8:        # a display value reaching control
    return gated(out)
```
Expected: refused. `confidence` is a display value and has no comparison. "Never wrong" is said by raising the loss.
Source: hkaddresses `resolve/bayes.py`, found by the audit of 2026-09-20, retired by ruling 26.

## S2 Independent, linear evidence
```python
b = condition(condition(b, K, o), K, o)            # one token, used twice

k1 = observe("reading", source="the_draw")         # two acts read one draw,
k2 = observe("re-reading", source="the_draw")      # and "the_draw" is not a component of Omega

for copy in forwarded_copies(email):               # five copies of one attestation,
    b = condition(b, extraction_kernel, observe(copy))   # and the attestation is not in Omega
```
Expected: refused three times. A token is consumed at most once. A source read twice must be a declared component of Ω; then the second read is nearly worthless and the agent will not pay for it.
Source: attack session 1, World P (the draft-2 agent believed 13/160 and earned −1/5). life-agent's `β_ancestry = 0.3` is the hand-set patch for the third case.

## S3 Housed numerals
```python
score = 0.7 * name_score + 0.3 * number_score      # numerals with no table and no source
```
and a table entry that no kernel reads.
Expected: refused twice.
Source: audit — ~95 hand-set weights, six parameters read by nothing.

## S4 Normalised kernels
```yaml
abbreviate:
  Street: {St: 0.5, Str: 0.2}                      # row sums to 0.7; where is the rest?
```
Expected: refused. Say the remainder (here: written in full, 0.3).
Source: audit — the channel is not a proper distribution (A34).

## S5 Zero evidence
```python
if z == 0:
    return prior                                   # or: z = max(z, 1e-12)
```
Expected: refused. Either ⊥ has full support and z > 0 always, or the World is closed and the episode ends as WORLD_FALSIFIED.
Source: life-agent `prob_eps = 1e-12`.

## E3 The floor
```yaml
depth: 0                                           # never looks; every one-sided consequence passes
```
Expected: refused; 1 ≤ d ≤ N. C10 catches the behaviour where the declaration is missing.
Source: attack session 1, finding 5 (regret 29/50 on the appendix vector).

## E5 One decide
```python
def choose_candidate(posterior):                   # a pack ranks and picks
    return max(posterior, key=posterior.get) if max(posterior.values()) > 0.5 else None
```
Expected: refused. Packs and fast paths supply beliefs and values; only the kernel's `decide` chooses.
Source: attack session 2, finding 5.1 — an agent that plays the first improving look, or ignores the declared depth, passes every consequence; only the differential on toy worlds sees it, so the choosing code must exist once.

## E2 Fast paths
```python
cands = [c for c in index.lookup(x) if c.score > 0.2]   # the dropped mass goes nowhere
p_x_given_e = max(score(x, e, z) for z in alignments)    # best path where the model says sum
```
Expected: both fail E2. Unevaluated mass is a bound, and the act must be the Bayes act for every belief consistent with it (attack session 2, 1.2: dropping 3/200 flips t2 to t1); a mass is a sum.
Source: audit — ~15 build-time gates; the shipped likelihood kept the best alignment.
