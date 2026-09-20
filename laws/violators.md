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

## S2 Linear evidence
```python
b = condition(condition(b, K, o), K, o)            # one token, used twice

for copy in forwarded_copies(email):               # five copies of one attestation
    b = condition(b, extraction_kernel, observe(copy))
```
Expected: refused twice. A token is consumed once. Tokens sharing provenance need a kernel declared jointly over them.
Source: life-agent's `β_ancestry = 0.3` is the hand-set patch for the second case.

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

## E2 Fast paths
```python
cands = [c for c in index.lookup(x) if c.score > 0.2]   # the dropped mass goes nowhere
p_x_given_e = max(score(x, e, z) for z in alignments)    # best path where the model says sum
```
Expected: both fail E2. A dropped hypothesis is a bound the act must be invariant to; a mass is a sum.
Source: audit — ~15 build-time gates; the shipped likelihood kept the best alignment.
