"""
counts_check.py - tests CHARTER v0.2 (what is learned between episodes) against the trusted reference in spec_check.py.

Part 1  the amendment's semantics: a World whose Omega is locals x Globals, with P(local | Global) declared and a prior over
        Globals conditioned on Counts; the after-act; identifiability (S15); the E7 diagnostic.
Part 2  the consequences as black-box checks on any implementation (prior, persist, decide, declare).
Part 3  poisons - most of them bugs credence actually shipped (github.com/gfrmin/credence, read 2026-09-22):
        the router learning a reliability with no verdict, the governor's degenerate label and railed grid, the
        winner's-curse collapse, forgetting, a log kept instead of counts, a score/transition split.
Part 4  frozen vectors (the page's appendices, the credence cases) and the kill matrix.

A record is one episode's observable history: (((act, outcome), ...), terminal act fired, after-outcome or None).
Counts are a multiset of records. Reports within an episode share the episode's local state, so the record - not the
(act, outcome) pair - is the unit of sufficiency.

Run:  python3 laws/counts_check.py [--seed S] [--worlds K]        (exit 0 = the page passes)
"""
from fractions import Fraction as F
from collections import Counter
import argparse, hashlib, itertools, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec_check import REF, Refused

def refused(name, rule):
    "a refusal carrying the rule of CHARTER v0.2 that makes it, for the traceability lint (laws/page_check.py)"
    e = Refused(name); e.rule = rule; return e

# ---------------------------------------------------------------- Part 1: the amendment
def vals(dims): return [tuple(x) for x in itertools.product(*[v for _, v in dims])] if dims else [()]
def skey(l, g): return ",".join(l) + "|" + ",".join(g)
def unkey(s):
    l, g = s.split("|"); return (tuple(l.split(",")) if l else ()), (tuple(g.split(",")) if g else ())
def strK(K): return {skey(l, g): row for (l, g), row in K.items()}

def counts_sha(counts, falsifiers=()):
    """SURFACE v0.2 section 3 (draft 3): SHA-256, lowercase hex, of the compact JSON array [counts, falsifiers] -
    counts the array of the distinct records [draws, end, after, n], falsifiers the array of the falsifying records
    [draws, end, after] (end and after null for a report inside an episode), each array sorted by its elements' own
    compact JSON; no whitespace, the short escapes \\" \\\\ \\b \\f \\n \\r \\t, other control characters and every
    non-ASCII character as \\u and four lowercase hex digits, DEL and / written raw. Names hold no lone surrogate."""
    enc = lambda x: json.dumps(x, separators=(",", ":"), ensure_ascii=True)
    rows = sorted(enc([[list(x) for x in obs], t, oa, n]) for (obs, t, oa), n in counts.items())
    fal = sorted(enc([[list(x) for x in obs], t, oa]) for (obs, t, oa) in falsifiers)
    return hashlib.sha256(("[[" + ",".join(rows) + "],[" + ",".join(fal) + "]]").encode("utf-8")).hexdigest()

def evidence(W):
    "everything a plate's prior conditions on: the shipped Counts and their falsifying records (S13, J26)"
    return W.get("counts", Counter()) + Counter(W.get("falsifiers", ()))

def record_lik(W, rec, g):
    "P(this episode's reports and after-report | Global g): the local state is summed out under P(local | g)"
    obs, t, oa = rec; tot = F(0)
    for l, pl in W["prior_local"][g].items():
        p = pl
        for k, o in obs: p *= W["O"][k]["K"][(l, g)].get(o, F(0))
        if oa is not None and t is not None: p *= W["after"]["K"][t][(l, g)].get(oa, F(0))
        tot += p
    return tot

def post_global(W, counts):
    "the declared prior over Globals conditioned on Counts - v0 `condition`, applied to a multiset of records"
    w = {g: W["prior_global"][g] for g in vals(W["globals"])}
    for rec, n in counts.items():
        for g in w: w[g] *= record_lik(W, rec, g) ** n
    s = sum(w.values())
    if s == 0: raise refused("FALSIFIED", "C2.J26")
    return {g: v / s for g, v in w.items()}

def episode_world(W, counts, prior=None):
    "an INTERFACE (v0) World for one episode: prior = P(Global | Counts) x P(local | Global); locals start fresh"
    pg = post_global(W, counts) if prior is None else prior
    p = {skey(l, g): pg[g] * pl for g in pg for l, pl in W["prior_local"][g].items() if pg[g] * pl > 0}
    return {"prior": p, "T": {t: strK(u) for t, u in W["T"].items()},
            "O": {k: {"K": strK(s["K"]), "price": s["price"], "once": s["once"], "ends": {}} for k, s in W["O"].items()},
            "N": W["N"], "d": W["d"], "declared_prior": {g: W["prior_global"][g] for g in pg}}

AFTER = "<after>"

def designs(W):
    "every realisable fixed design: a sequence of draws within the horizon N, each `once` act at most once"
    acts, out = sorted(W["O"]), []
    def grow(seq, used, n):
        out.append(tuple(seq))
        if n == 0: return
        for k in acts:
            if W["O"][k]["once"] and k in used: continue
            grow(seq + [k], used | {k}, n - 1)
    grow([], frozenset(), W["N"])
    return out

def _walk(W, l, g, seq):
    "the draws of a fixed design from state (l, g), stopping at an ending outcome (Q8): yields (outcomes, end or None, p)"
    def go(i, p, outs):
        if i == len(seq): yield outs, None, p; return
        k = seq[i]
        for o, q in W["O"][k]["K"][(l, g)].items():
            if q == 0: continue
            if o in W["O"][k].get("ends", ()): yield outs + (o,), f"end:{k}={o}", p * q
            else: yield from go(i + 1, p * q, outs + (o,))
    yield from go(0, F(1), ())

def design_dist(W, g, seq, t):
    "the law of a design's outcomes, its end and the after-report under end t, the local summed out under P(local | g)"
    dist, after = {}, W.get("after")
    for l, pl in W["prior_local"][g].items():
        if pl == 0: continue
        for outs, e, p in _walk(W, l, g, seq):
            end = e or t
            arow = after["K"][end][(l, g)] if (after and end is not None) else {None: F(1)}
            for oa, qa in arow.items():
                key = (outs, e, oa); dist[key] = dist.get(key, F(0)) + pl * p * qa
    return frozenset((k, v) for k, v in dist.items() if v)

def classes(W):
    """Global values that no realisable design separates, grouped. A distinguishing adaptive policy implies a
    distinguishing fixed design, so two values in one class are ones no policy and no plate can ever tell apart
    (attack session 2 on draft 6, 3.1: draft 6's design could exceed N and accepted Worlds no policy learns)."""
    ts = list(W["T"]) if W.get("after") else [None]
    ds = designs(W); sig = {}
    for g in vals(W["globals"]):
        sig.setdefault(tuple(design_dist(W, g, d, t) for d in ds for t in ts), []).append(g)
    return list(sig.values())

def learns_nothing(W):
    "every Global value in one class: no plate, from any records this declaration can write, can move the Globals"
    return len(vals(W["globals"])) > 1 and len(classes(W)) == 1

def paid_part(W, l, g):
    """what an act can feel of a state (session 6): the utility differences between terminals - a per-state constant
    changes no act (v0 C4, 3.3) - and, when the World declares the think act, best(state), which the cap reads (3.1)"""
    ts = sorted(W["T"]); base = W["T"][ts[0]][(l, g)]
    part = tuple(W["T"][t][(l, g)] - base for t in ts)
    if "dplus" in W:
        best = max(W["T"][t][(l, g)] for t in ts)
        for k, sp in W["O"].items():
            for o, ue in sp.get("u_end", {}).items():
                if sp["K"][(l, g)].get(o, F(0)) > 0: best = max(best, ue[(l, g)] if isinstance(ue, dict) else ue)
        part += (best,)
    return part

def joint_dist(W, g, seq, t):
    """the joint law of what an act can feel of the state with a design's draws, under g; the after-report left out
    (session 6, 3.2); a design stops at an ending outcome (Q8)"""
    dist = {}
    for l, pl in W["prior_local"][g].items():
        if pl == 0: continue
        lk = paid_part(W, l, g)
        for outs, e, p in _walk(W, l, g, seq):
            key = (lk, outs, e); dist[key] = dist.get(key, F(0)) + pl * p
    return frozenset((k, v) for k, v in dist.items() if v)

def unwashable(W):
    """S15 as of draft 11: nothing is refused; the part of the prior no plate will move is disclosed (attack session 4,
    1.3: every refusal rule proposed so far was beaten by a spelling - of names in session 3, of dimensions in session 4).
    The part of the prior no plate will move: each class holding two values that no
    design separates yet which disagree about the local jointly with the records - so the declared prior within that
    class settles, forever, something a utility reads. Twins (the same joint law) are a spelling and are not listed."""
    ts = list(W["T"]) if W.get("after") else [None]; ds = designs(W); out = []
    for c in classes(W):
        kinds = {tuple(joint_dist(W, g, d, t) for d in ds for t in ts) for g in c}
        if len(kinds) > 1: out.append({g: W["prior_global"][g] for g in c})
    return out

def after_taken(W):
    """S12 as of draft 11: the After-act is taken at the end of every episode not ended in WORLD_FALSIFIED, whenever it
    is declared. Draft 9 struck it when the declared model said it could not teach; that blinded E7 exactly where the
    model is wrong (attack session 4, 2.1-2.3): grading is a check on the model, which the model cannot value."""
    return bool(W.get("after"))

def plate_value(W, T, counts=None, one_run=False):
    """E7's policy value: the expected utility of a plate of T episodes under the declared model, net of every price,
    the After-act's included; the kernel's policy at the floor (J21), or with one_run the exact one-run maximiser"""
    counts = Counter() if counts is None else counts
    if T == 0: return F(0)
    w = episode_world(W, counts); pg = post_global(W, counts)
    def go(b, n, used, obs):
        if one_run:
            best = None
            for a in list(w["T"]) + [k for k in w["O"] if not (w["O"][k]["once"] and k in used)] if n > 0 else list(w["T"]):
                v = act_value(a, b, n, used, obs)
                if best is None or v > best: best = v
            return best
        a = REF.solve(b, w, min(w["d"], n), used)[1]
        return act_value(a, b, n, used, obs)
    def act_value(a, b, n, used, obs):
        if a in w["T"]:
            v = REF.expect(b, w["T"][a])
            if W.get("after"):
                K = strK(W["after"]["K"][a]); v -= W["after"]["price"]
                for o, po in REF.push(b, K).items():
                    if po > 0: v += po * plate_value(W, T - 1, counts + Counter([(tuple(obs), a, o)]), one_run)
            else:
                v += plate_value(W, T - 1, counts + Counter([(tuple(obs), a, None)]), one_run)
            return v
        K = w["O"][a]["K"]; v = -w["O"][a]["price"]
        for o, po in REF.push(b, K).items():
            if po > 0:
                v += po * go(REF.condition(b, K, o), n - 1, used | ({a} if w["O"][a]["once"] else set()), obs + [(a, o)])
        return v
    return go(w["prior"], w["N"], frozenset(), [])

def loo_score(W, counts, falsifiers=()):
    """S14 as corrected by ERRATA (CHARTER v0.2, entry 1): for each copy of each record of the Counts and for each
    falsifying record, its likelihood under the Prior conditioned on all the others, multiplied together; a rational.
    As signed, S14 gave the falsifying records no term, so data shipped as a falsifier moved the prior unscored
    (SURFACE v0.2 session 3, 1.1)."""
    allrec = counts + Counter(falsifiers); total = F(1)
    for r, n in allrec.items():
        rest = Counter(allrec); rest[r] -= 1
        if rest[r] == 0: del rest[r]
        pg = post_global(W, rest)
        total *= sum(pg[g] * record_lik(W, r, g) for g in pg) ** n
    return total

def ends_of(W):
    "every end: each terminal, and each ending outcome as end:act=outcome (CHARTER v0.2 section 3; Q8 of brief 007)"
    return set(W["T"]) | {f"end:{k}={o}" for k, sp in W["O"].items() for o in sp.get("ends", ())}

def realisable(W, rec_, falsifier=False):
    """a record an episode of this declaration can produce under v0's loop, whatever its policy (the kernel's policy
    is not consulted): its acts declared, at most N draws, each `once` act at most once, an ending outcome only as
    the last draw and then as the end, an after-report exactly when an After-act is declared. A falsifier may also be
    a prefix - draws up to the report that falsified the World inside the episode, with no end (Q9 of brief 007)."""
    obs, t, oa = rec_
    acts = [k for k, _ in obs]
    if len(acts) > W["N"] or any(k not in W["O"] for k in acts): return False
    if any(W["O"][k]["once"] and acts.count(k) > 1 for k in set(acts)): return False
    for i, (k, o) in enumerate(obs):
        if o in W["O"][k].get("ends", ()) and (i != len(obs) - 1 or t != f"end:{k}={o}"): return False
    if falsifier and t is None: return oa is None and len(obs) >= 1
    if falsifier and oa is None: return False          # an episode that ended with no report after it falsified nothing (SURFACE v0.2 session 3, 1.1)
    if t not in ends_of(W): return False
    return (oa is not None) == bool(W.get("after")) or (falsifier and oa is not None and bool(W.get("after")))

def expressible(W, counts, falsifiers=()):
    "session 4, 1.1 and 5.1; draft 3: every shipped record and falsifier realisable here, all of them jointly possible"
    if not all(realisable(W, r) for r in counts) or not all(realisable(W, f, True) for f in falsifiers): return False
    allrec = counts + Counter(falsifiers)
    return any(W["prior_global"][g] * _prod(record_lik(W, r, g) ** n for r, n in allrec.items()) > 0 for g in vals(W["globals"]))

def _prod(xs):
    out = F(1)
    for x in xs: out *= x
    return out

def refuse(W):
    "v0.2's refusals, by name (draft 11: S15 refuses nothing and discloses; shipped Counts must be expressible)"
    gs, ls = vals(W["globals"]), vals(W["locals"])
    for t, u in W["T"].items():                                        # S11: a Global is unpaid
        for l in ls:
            if len({u[(l, g)] for g in gs if (l, g) in u}) > 1: raise refused("GLOBAL", "C2.S11")
    for k, sp in W["O"].items():                                       # S11: nor is an ending utility
        for o, ue in sp.get("u_end", {}).items():
            if isinstance(ue, dict):
                for l in ls:
                    if len({ue[(l, g)] for g in gs if (l, g) in ue}) > 1: raise refused("GLOBAL", "C2.S11")
    if W.get("after"):                                                 # S12: one After-act, a kernel for exactly the ends
        supp = {(l, g) for g in gs for l, p in W["prior_local"][g].items() if p > 0 and W["prior_global"].get(g, 0) > 0}
        if set(W["after"]["K"]) != ends_of(W) or any(not supp <= set(W["after"]["K"][e]) for e in ends_of(W)):
            raise refused("AFTER", "C2.S12")
    if sum(W["prior_global"].values()) != 1 or min(W["prior_global"].values()) <= 0: raise refused("PRIOR", "C2.J20")
    for g in gs:
        if sum(W["prior_local"][g].values()) != 1: raise refused("PRIOR", "C2.J20")
    if W.get("counts") is not None or W.get("falsifiers"):             # S13, S14
        c, fs = W.get("counts", Counter()), tuple(W.get("falsifiers", ()))
        if W.get("counts_sha") != counts_sha(c, fs) or not expressible(W, c, fs): raise refused("PLATE", "C2.S13")
        if W.get("score") != loo_score(W, c, fs): raise refused("UNSCORED", "C2.S14")
    return W

def seq_prob(W, g, draws, t):
    "P(these draws | g), the local summed out; an after-draw is read under end t"
    tot = F(0)
    for l, pl in W["prior_local"][g].items():
        p = pl
        for k, o in draws:
            p *= (W["after"]["K"][t] if k == AFTER else W["O"][k]["K"])[(l, g)].get(o, F(0))
        tot += p
    return tot

def diagnostic(W, counts):
    """E7, as of draft 7: for every draw in Counts - each report, and the after-report - grouped by the history
    within its episode that led to it, the total variation distance between the empirical distribution of its
    outcome and its posterior predictive given that history. The choice to take a draw depends only on what came
    before it, so no selection enters (attack session 2, 1.3: a per-design predictive printed 1/2 on a correct World).
    The Global is weighted by P(Global | all Counts), which already holds this history; the history conditions the
    local only (session 6, wording 6: conditioning the Global on it again counts it twice)."""
    pg = post_global(W, counts); groups = {}
    for (obs, t, oa), n in counts.items():
        draws = list(obs) + ([(AFTER, oa)] if oa is not None else [])
        for j, (k, o) in enumerate(draws):
            groups.setdefault((tuple(draws[:j]), k, t if k == AFTER else None), Counter())[o] += n
    tv = {}
    for (hist, k, t), c in groups.items():
        tot = sum(c.values())
        table = W["after"]["K"][t] if k == AFTER else W["O"][k]["K"]
        outs = sorted({o for row in table.values() for o in row}, key=str)
        live = [g for g in pg if pg[g] > 0 and seq_prob(W, g, list(hist), t) > 0]
        pred = lambda o: sum(pg[g] * seq_prob(W, g, list(hist) + [(k, o)], t) / seq_prob(W, g, list(hist), t) for g in live) / sum(pg[g] for g in live)
        tv[(hist, k, t)] = sum(abs(F(c.get(o, 0), tot) - pred(o)) for o in outs) / 2
    return tv

def e7(W, counts): return max(diagnostic(W, counts).values())

def full_posterior_global(W, recs):
    "C23's independent route: episode by episode through v0 `condition` on the full product Omega, locals re-drawn"
    pg = dict(W["prior_global"])
    for obs, t, oa in recs:
        b = {skey(l, g): pg[g] * pl for g in pg for l, pl in W["prior_local"][g].items() if pg[g] * pl > 0}
        for k, o in obs: b = REF.condition(b, strK(W["O"][k]["K"]), o)
        if oa is not None: b = REF.condition(b, strK(W["after"]["K"][t]), oa)
        pg = {g: F(0) for g in pg}
        for s, p in b.items(): pg[unkey(s)[1]] += p
    return pg

# ---------------------------------------------------------------- implementations (the reference, then poisons)
class Reference:
    name = "reference (CHARTER v0.2 draft 15)"
    def declare(self, W): return refuse(W)
    def disclose(self, W): return unwashable(W)
    def persist(self, recs): return Counter(recs)
    def prior(self, W, recs): return episode_world(W, Counter(recs))["prior"]
    def decide(self, b, w, n, used): return REF.solve(b, w, min(w["d"], n), used)[1]
REFI = Reference()

def global_marginal(prior):
    m = {}
    for s, p in prior.items(): g = unkey(s)[1]; m[g] = m.get(g, F(0)) + p
    return m

def play(impl, W, recs, script):
    "one episode: the impl's prior, its decisions at the floor, outcomes from the script; returns (acts, terminal)"
    w = episode_world(W, Counter(recs)); w["prior"] = impl.prior(W, recs)
    b, used, n, acts = w["prior"], frozenset(), w["N"], []
    while True:
        a = impl.decide(b, w, n, used); acts.append(a)
        if a in w["T"]: return tuple(acts)
        b = REF.condition(b, w["O"][a]["K"], script[a]); used |= {a} if w["O"][a]["once"] else set(); n -= 1

# ---------------------------------------------------------------- Part 2: checks (True = holds)
def FRESH(impl, W, recs, rng):
    "locals never persist: under the impl's prior, P(local | Global) is the declared one"
    pr = impl.prior(W, recs); m = global_marginal(pr)
    return all(pr.get(skey(l, g), F(0)) == m[g] * pl for g in m if m[g] > 0 for l, pl in W["prior_local"][g].items())
def C22(impl, W, recs, rng):
    "order invariance: the next prior depends on the plate only through Counts"
    shuffled = list(recs); rng.shuffle(shuffled)
    return impl.prior(W, recs) == impl.prior(W, list(reversed(recs))) == impl.prior(W, shuffled)
def C23(impl, W, recs, rng):
    "sufficiency: the impl's Global marginal equals episode-by-episode v0 conditioning on the full product Omega"
    m = global_marginal(impl.prior(W, recs)); ref = full_posterior_global(W, recs)
    return all(m.get(g, F(0)) == ref[g] for g in ref)
def C24(impl, W, recs, rng):
    "no leakage: what is learned does not read utilities or prices"
    W2 = {**W, "T": {t: {s: 3 * u - 7 for s, u in r.items()} for t, r in W["T"].items()},
          "O": {k: {**s, "price": 3 * s["price"] + 1} for k, s in W["O"].items()}}
    return impl.prior(W, recs) == impl.prior(W2, recs)
def E2(impl, W, recs, rng):
    "the differential: the impl plays the reference's acts, episode by episode, on a scripted door"
    script = {k: rng.choice(sorted({o for row in s["K"].values() for o in row})) for k, s in W["O"].items()}
    try: return play(impl, W, recs, script) == play(REFI, W, recs, script)
    except Exception: return False
def BOUND(impl, W, recs, rng):
    "S13: what persists is bounded by the number of distinct records, however long the plate"
    return len(impl.persist(recs * 5)) <= len(set(recs))
CHECKS = [("FRESH", FRESH), ("C22", C22), ("C23", C23), ("C24", C24), ("E2", E2), ("BOUND", BOUND)]

# ---------------------------------------------------------------- Part 3: poisons
class CarryAnswer(Reference):
    name = "carries the answer: the last episode's joint posterior becomes the next prior (locals persist)"
    def prior(self, W, recs):
        if not recs: return super().prior(W, recs)
        b = super().prior(W, recs[:-1]); obs, t, oa = recs[-1]
        for k, o in obs: b = REF.condition(b, strK(W["O"][k]["K"]), o)
        if oa is not None: b = REF.condition(b, strK(W["after"]["K"][t]), oa)
        return b
class SlidingWindow(Reference):
    name = "forgets: conditions only on the last two records (a window - credence's own constitution forbids it, 1.41)"
    def prior(self, W, recs): return super().prior(W, recs[-2:])
    def persist(self, recs): return Counter(recs[-2:])
class Collapse(Reference):
    name = "collapses: all Global mass on the posterior's argmax (credence's winner's curse / average-not-collapse)"
    def prior(self, W, recs):
        pg = post_global(W, Counter(recs)); top = max(pg, key=lambda g: (pg[g], g))
        return episode_world(W, Counter(), {g: F(1 if g == top else 0) for g in pg})["prior"]
class KeepsLog(Reference):
    name = "keeps a log instead of Counts: persisted state grows with the plate (proplang #25's growth)"
    def persist(self, recs): return list(recs)
class ScoreTransitionSplit(Reference):
    name = "reports the learned prior, decides with the declared one (credence's score/transition split)"
    def decide(self, b, w, n, used):
        b0 = episode_world_like_declared(w)
        return REF.solve(b0, w, min(w["d"], n), used)[1]
class ReadsAfter(Reference):
    name = "decide weighs the after-act: bends the terminal toward the gradeable act (breaks S12/J21)"
    def decide(self, b, w, n, used):
        best, arg = None, None
        for t, u in w["T"].items():
            v = REF.expect(b, u) + (F(1, 2) if w.get("after_informative", {}).get(t) else 0)
            if best is None or v > best: best, arg = v, t
        return arg
class ProbabilityOfBest(Reference):
    name = "ranks terminals by the chance each is best, not by expected utility (utility levels inert: proplang #24)"
    def decide(self, b, w, n, used):
        score = {t: sum(p for s, p in b.items() if all(w["T"][t][s] >= w["T"][t2][s] for t2 in w["T"])) for t in w["T"]}
        return max(w["T"], key=lambda t: (score[t], -list(w["T"]).index(t)))
class HidesTheUnwashable(Reference):
    name = "discloses nothing: the part of the prior no plate will move goes unshown (S15; credence's router)"
    def disclose(self, W): return []

class AcceptsPaidGlobal(Reference):
    name = "accepts a utility that reads a Global (S11)"
    def declare(self, W):
        try: return refuse(W)
        except Refused as e:
            if str(e) == "GLOBAL": return W
            raise

def episode_world_like_declared(w):
    "the declared prior rebuilt from an episode World: P(g) declared, P(local | g) read off the episode prior"
    pg, m = w["declared_prior"], global_marginal(w["prior"])
    return {s: pg[unkey(s)[1]] * (p / m[unkey(s)[1]]) for s, p in w["prior"].items() if m[unkey(s)[1]] > 0}

class HardAssign(Reference):
    name = "classify, then condition as if certain: each record's local set to its most probable value (credence's categories)"
    def prior(self, W, recs):
        pg = dict(W["prior_global"])
        for obs, t, oa in recs:
            # the most probable local under the current belief, then condition as if that local had been observed
            score = {}
            for l in vals(W["locals"]):
                s_ = F(0)
                for g in pg:
                    p = pg[g] * W["prior_local"][g].get(l, F(0))
                    for k, o in obs: p *= W["O"][k]["K"][(l, g)].get(o, F(0))
                    if oa is not None: p *= W["after"]["K"][t][(l, g)].get(oa, F(0))
                    s_ += p
                score[l] = s_
            lhat = max(score, key=lambda l: (score[l], l))
            new = {}
            for g in pg:
                p = pg[g] * W["prior_local"][g].get(lhat, F(0))
                for k, o in obs: p *= W["O"][k]["K"][(lhat, g)].get(o, F(0))
                if oa is not None: p *= W["after"]["K"][t][(lhat, g)].get(oa, F(0))
                new[g] = p
            z = sum(new.values()); pg = {g: q / z for g, q in new.items()} if z else pg
        return episode_world(W, Counter(), pg)["prior"]

POISONS = [HardAssign(), CarryAnswer(), SlidingWindow(), Collapse(), KeepsLog(), ScoreTransitionSplit(), ReadsAfter(),
           ProbabilityOfBest(), HidesTheUnwashable(), AcceptsPaidGlobal()]

# ---------------------------------------------------------------- Part 4: Worlds
def reliability_world(grid, prior_g, u_wrong, verdict=True):
    """appendix A's shape: the answer (local, uniform) x the instrument's reliability (Global, on a grid).
    `ask` reports the answer with the reliability; the after-act, if declared, reveals the answer."""
    L = [("answer", ["a1", "a2"])]; G = [("rel", [str(r) for r in grid])]
    gs, ls = vals(G), vals(L)
    other = {"a1": "a2", "a2": "a1"}
    K = {(l, g): {l[0]: F(g[0]), other[l[0]]: 1 - F(g[0])} for l in ls for g in gs}
    T = {"say a1": {(l, g): (F(1) if l == ("a1",) else u_wrong) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l == ("a2",) else u_wrong) for l in ls for g in gs},
         "abstain": {(l, g): F(0) for l in ls for g in gs}}
    W = {"locals": L, "globals": G, "prior_global": {g: prior_g[i] for i, g in enumerate(gs)},
         "prior_local": {g: {l: F(1, 2) for l in ls} for g in gs}, "T": T,
         "O": {"ask": {"K": K, "price": F(0), "once": True}}, "N": 1, "d": 1}
    if verdict: W["after"] = {"K": {t: {(l, g): {l[0]: F(1)} for l in ls for g in gs} for t in T}, "price": F(0)}
    return W

def rec(report, truth, t="abstain"): return ((("ask", report),), t, truth)

def router_world(verdict, credence_prior=False):
    """credence's router in miniature (src/routing.jl): a turn is correct (C, local) with probability theta (the model's
    quality, Global); the exec signal e fires with rho if correct and sigma if not (Globals). No ground truth unless a
    verdict reveals C."""
    grid = ["1/4", "3/4"]
    L = [("C", ["1", "0"])]; G = [("theta", grid), ("rho", grid), ("sigma", grid)]
    gs, ls = vals(G), vals(L)
    Kx = {(l, g): {"1": F(g[1] if l == ("1",) else g[2]), "0": 1 - F(g[1] if l == ("1",) else g[2])} for l in ls for g in gs}
    T = {"use": {(l, g): (F(1) if l == ("1",) else F(-1)) for l in ls for g in gs}, "skip": {(l, g): F(0) for l in ls for g in gs}}
    if credence_prior:   # E[rho] = 2/3, E[sigma] = 1/3 on {1/4, 3/4}: P(rho = 3/4) = 5/6, P(sigma = 3/4) = 1/6
        pr = {g: F(1, 2) * (F(5, 6) if g[1] == "3/4" else F(1, 6)) * (F(1, 6) if g[2] == "3/4" else F(5, 6)) for g in gs}
    else:
        pr = {g: F(1, len(gs)) for g in gs}
    W = {"locals": L, "globals": G, "prior_global": pr,
         "prior_local": {g: {("1",): F(g[0]), ("0",): 1 - F(g[0])} for g in gs}, "T": T,
         "O": {"exec": {"K": Kx, "price": F(0), "once": True}}, "N": 1, "d": 1}
    if verdict: W["after"] = {"K": {t: {(l, g): {l[0]: F(1)} for l in ls for g in gs} for t in T}, "price": F(0)}
    return W

def levels_world():
    "C25: expected utility and 'chance of being best' disagree; safe is listed first"
    L = [("s", ["x", "y"])]; ls = vals(L); g = ()
    T = {"safe": {(l, g): F(1) for l in ls}, "bet": {(("x",), g): F(17, 5), (("y",), g): F(-1)}}
    return {"locals": L, "globals": [], "prior_global": {(): F(1)}, "prior_local": {(): {l: F(1, 2) for l in ls}},
            "T": T, "O": {}, "N": 0, "d": 1}

def after_world():
    "J21: the verdict is informative only if `say a1` fires; the episode's act must not bend toward it"
    L = [("answer", ["a1", "a2"])]; ls = vals(L); g = ()
    T = {"say a1": {(("a1",), g): F(1), (("a2",), g): F(-2)}, "say a2": {(("a2",), g): F(1), (("a1",), g): F(-2)},
         "abstain": {(l, g): F(0) for l in ls}}
    after = {"say a1": {(l, g): {l[0]: F(1)} for l in ls}, "say a2": {(l, g): {"none": F(1)} for l in ls},
             "abstain": {(l, g): {"none": F(1)} for l in ls}}
    return {"locals": L, "globals": [], "prior_global": {(): F(1)},
            "prior_local": {(): {("a1",): F(11, 20), ("a2",): F(9, 20)}}, "T": T, "O": {}, "after": {"K": after, "price": F(0)},
            "N": 0, "d": 1}

def rand_world(rng):
    "two locals, two or three Global values, P(local | Global) varying, one or two acts, an after-act"
    L = [("l", ["x", "y"])]; nG = rng.choice([2, 3]); G = [("g", [f"g{i}" for i in range(nG)])]
    gs, ls = vals(G), vals(L)
    def row(outs): ws = [rng.randint(1, 6) for _ in outs]; s = sum(ws); return {o: F(w, s) for o, w in zip(outs, ws)}
    pg = row(gs); pl = {g: row(ls) for g in gs}
    O = {f"k{i}": {"K": {(l, g): row(["p", "q"]) for l in ls for g in gs}, "price": F(rng.randint(0, 3), 4), "once": True}
         for i in range(rng.choice([1, 2]))}
    T = {f"t{i}": {(l, g): u for l in ls for u in [F(rng.randint(-4, 4))] for g in gs} for i in range(2)}
    after = {"K": {t: {(l, g): row(["r", "s"]) for l in ls for g in gs} for t in T}, "price": F(0)}
    return {"locals": L, "globals": G, "prior_global": pg, "prior_local": pl, "T": T, "O": O, "after": after,
            "N": len(O), "d": 1}

def rand_records(W, rng, n):
    out = []
    for _ in range(n):
        obs = tuple((k, rng.choice(["p", "q"])) for k in sorted(W["O"]) if rng.random() < 0.8)
        out.append((obs, rng.choice(list(W["T"])), rng.choice(["r", "s"])))
    return out

# ---------------------------------------------------------------- frozen vectors
def frozen():
    L = []
    # Appendix A: what one graded episode is worth
    W = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); refuse(W)
    good, poor = ("9/10",), ("3/5",)
    assert post_global(W, Counter([rec("a1", "a1")])) == {good: F(3, 5), poor: F(2, 5)}
    assert post_global(W, Counter([rec("a1", "a2")])) == {good: F(1, 5), poor: F(4, 5)}
    w2 = episode_world(W, Counter([rec("a1", "a1")])); b = REF.condition(w2["prior"], w2["O"]["ask"]["K"], "a1")
    assert sum(p for s, p in b.items() if s.startswith("a1")) == F(39, 50) and REF.solve(b, w2, 0) == (F(17, 50), "say a1")
    assert post_global(W, Counter([rec("a1", "a1"), rec("a1", "a2")])) == {good: F(3, 11), poor: F(8, 11)}
    L.append("  A  one graded episode: reliability (3/5, 2/5); next P(a1|report) 39/50, value 17/50; order-free (3/11, 8/11)")
    # S15 on the same World without a verdict: reports alone are uninformative about a symmetric reliability
    Ap = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False); refuse(Ap)
    assert learns_nothing(Ap) and len(unwashable(Ap)) == 1
    L.append("  A' the same World with no after-act: accepted, and disclosed as learning nothing - P(report) = 1/2 whatever")
    L.append("     the reliability, so no plate moves it and it rests on its prior forever")
    # credence's router: accepted, and the kernel discloses the part of its prior no plate will ever move
    Rc = router_world(verdict=False, credence_prior=True); refuse(Rc); refuse(router_world(verdict=False))
    uw = unwashable(Rc)
    assert len(uw) == 4 and all(len(c) == 2 for c in uw) and any(len(set(c.values())) > 1 for c in uw)
    assert unwashable(router_world(verdict=True, credence_prior=True)) == []
    L.append("  R  credence's router with its prior: accepted, and 4 classes disclosed as unwashable - (theta, rho, sigma) against")
    L.append("     (1 - theta, sigma, rho), where 'is this model good?' rests on the declared prior forever. With a verdict: none.")
    # credence's governor, both halves, as Worlds whose own kernel asks
    Wg = reliability_world([F(1, 2), F(9, 10)], [F(1, 2), F(1, 2)], F(-2))           # break-even 2/3 < E[rel] = 7/10
    gaps = []
    for n in (200, 2000):
        c = Counter({rec("a1", "a1", "say a1"): 99 * n // 200, rec("a2", "a2", "say a2"): 99 * n // 200,
                     rec("a1", "a2", "say a1"): n // 200, rec("a2", "a1", "say a2"): n // 200})
        assert play(REFI, Wg, [], {"ask": "a1"}) == ("ask", "say a1") and play(REFI, Wg, list(c.elements())[:3], {"ask": "a2"}) == ("ask", "say a2")
        pg = post_global(Wg, c); gap = e7(Wg, c); gaps.append(gap)
        assert pg[("9/10",)] > F(999, 1000) and F(8, 100) < gap < F(1, 10), (float(pg[("9/10",)]), float(gap))
    L.append(f"  G1 credence's degenerate label: the kernel asks and answers the report; 99% graded right on a grid capped at")
    L.append(f"     9/10 -> certain of 9/10; E7 {float(gaps[0]):.4f} at n = 200 and {float(gaps[1]):.4f} at n = 2000 (the after-report's calibration)")
    Wr = reliability_world([F(1, 2), F(97, 100)], [F(1, 25), F(24, 25)], F(-19))    # a prior that already trusts it
    assert play(REFI, Wr, [], {"ask": "a1"}) == ("ask", "say a1")
    last = None
    for n in (100, 1000):
        c = Counter({rec("a1", "a1", "say a1"): 93 * n // 200, rec("a2", "a2", "say a2"): 93 * n // 200,
                     rec("a1", "a2", "say a1"): 7 * n // 200, rec("a2", "a1", "say a2"): 7 * n // 200})
        w = episode_world(Wr, c); b = REF.condition(w["prior"], w["O"]["ask"]["K"], "a1")
        v, act = REF.solve(b, w, 0); m = post_global(Wr, c)[("97/100",)]
        assert act == "say a1" and v > 0 and (last is None or m > last) and e7(Wr, c) > F(3, 100); last = m
    L.append("  G2 the railed rung: prior (1/25, 24/25) on {1/2, 97/100}, true rate 93/100, break-even 19/20 -> the kernel")
    L.append("     asks and answers, wrong for 93/100, more certain from n = 100 to 1000; E7 prints about 0.04, not shrinking")
    # PLATE: Counts are content-addressed
    Wp = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); Wp["counts"] = Counter([rec("a1", "a1")])
    Wp["counts_sha"] = counts_sha(Wp["counts"]); Wp["score"] = loo_score(Wp, Wp["counts"]); refuse(Wp)
    Wp["counts"] = Counter([rec("a1", "a1"), rec("a1", "a2")])
    try: refuse(Wp); assert False
    except Refused as e: assert str(e) == "PLATE"
    L.append("  P  Counts that do not hash to their declared sha: refused PLATE (a live log cannot move under a fixed seed)")
    # GLOBAL
    Wu = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    Wu["T"]["say a1"][(("a1",), ("9/10",))] = F(2)
    try: refuse(Wu); assert False
    except Refused as e: assert str(e) == "GLOBAL"
    L.append("  U  a utility that reads the reliability: refused GLOBAL")
    # ---- attack session 1 on draft 5 (2026-09-22)
    W0 = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False)
    ls, gs = vals(W0["locals"]), vals(W0["globals"]); other = {"a1": "a2", "a2": "a1"}
    W0["O"]["check"] = {"K": {(l, g): {l[0]: F(4, 5), other[l[0]]: F(1, 5)} for l in ls for g in gs}, "price": F(0), "once": True}
    W0["N"] = 2; W0["d"] = 2; refuse(W0)
    r = ((("ask", "a1"), ("check", "a1")), "say a1", None)
    assert post_global(W0, Counter([r])) == full_posterior_global(W0, [r]) == {("9/10",): F(37, 65), ("3/5",): F(28, 65)}
    L.append("  s1-F1 no after-act, two instruments: the record still enters; Counts give (37/65, 28/65), as full conditioning does")
    Wf = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); Wf["O"]["ask"]["once"] = False; Wf["N"] = 2; Wf["d"] = 2
    ls, gs = vals(Wf["locals"]), vals(Wf["globals"])
    Wf["after"] = {"K": {t: {(l, g): {"-": F(1)} for l in ls for g in gs} for t in Wf["T"]}, "price": F(0)}
    refuse(Wf)
    assert post_global(Wf, Counter([((("ask", "a1"), ("ask", "a1")), "say a1", "-")])) == {("9/10",): F(41, 67), ("3/5",): F(26, 67)}
    L.append("  s1-F8 a `fresh` act, a blank verdict: accepted (two draws separate the Globals); one agreeing episode -> (41/67, 26/67)")
    Wo = oscillating_world(); refuse(Wo)
    ca = Counter({((), "useA", "A1"): 16, ((), "useA", "A0"): 24, ((), "useB", "B1"): 16, ((), "useB", "B0"): 24})
    cf = Counter({((), "useA", "A1"): 40, ((), "useA", "A0"): 60})
    assert post_global(Wo, ca) == {("x",): F(1, 2), ("y",): F(1, 2)}
    assert all(v == F(3, 10) for v in diagnostic(Wo, ca).values()) and F(9, 100) < e7(Wo, cf) < F(11, 100)
    L.append("  s1-F11 an adaptive design on a misdeclared grid need not converge: held at (1/2, 1/2); E7 prints 3/10 per draw")
    L.append("         (a fixed design concentrates on the KL-nearest point and E7 prints 1/10: C27's fixed-design case)")
    # ---- attack session 2 on draft 6 (2026-09-22)
    F1 = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False)
    ls, gs = vals(F1["locals"]), vals(F1["globals"]); other = {"a1": "a2", "a2": "a1"}
    F1["O"]["check"] = {"K": {(l, g): {l[0]: F(4, 5), other[l[0]]: F(1, 5)} for l in ls for g in gs}, "price": F(0), "once": True}
    refuse(F1); assert learns_nothing(F1)
    L.append("  s2-3.1 appendix F with N = 1: accepted, disclosed as learning nothing - one report is uninformative, and no")
    L.append("         realisable design takes two")
    TW = two_world(); refuse(TW); assert len(unwashable(TW)) == 1
    assert classes(TW) and any(len(c) == 2 for c in classes(TW))
    recs = [((("ask", "a1"), ("check", "a1")), "say a1", None)] * 4
    w0 = episode_world(TW, Counter()); b0 = REF.condition(w0["prior"], w0["O"]["ask"]["K"], "a1")
    w4 = episode_world(TW, Counter(recs)); b4 = REF.condition(w4["prior"], w4["O"]["ask"]["K"], "a1")
    assert REF.solve(b0, w0, 1, frozenset({"ask"}))[1] == "check" and REF.solve(b4, w4, 1, frozenset({"ask"}))[1] == "say a1"
    L.append("  s2-3.2 two reliabilities, one swapped pair inseparable under an equal prior: accepted; four agreeing episodes")
    L.append("         turn `check` into `say a1` - the plate learns what can be learned")
    RR = railed_world(); refuse(RR)
    c = Counter({((), "useA", "1"): 70, ((), "useA", "0"): 30})
    assert post_global(RR, c)[("x",)] > F(1) - F(1, 10**12) and e7(RR, c) < F(1, 10**12)
    L.append("  s2-2.1 conceded: a misdeclaration in an act the policy has stopped taking is invisible to every record-based")
    L.append("         check - on the railed branch E7 prints 0 (the price of J21: acting to learn is what would see it)")
    Wn = reliability_world([F(1, 2), F(9, 10)], [F(1, 2), F(1, 2)], F(-19))
    cn = Counter({((), "abstain", "a1"): 50, ((), "abstain", "a2"): 50})
    assert play(REFI, Wn, [], {"ask": "a1"}) == ("abstain",) and post_global(Wn, cn) == {("1/2",): F(1, 2), ("9/10",): F(1, 2)}
    L.append("  s2-2.2 draft 6's G1 as its kernel plays it: it never asks, every record is equally likely under both rungs, and")
    L.append("         the posterior stays (1/2, 1/2) - two KL minimisers, no concentration")
    # ---- attack session 3 on draft 8 (2026-09-23)
    Y = twin_world(F(1, 3), F(1, 6)); refuse(Y); assert unwashable(Y) == []
    assert post_global(Y, Counter([rec("a1", "a1", "say a1")]))[("x",)] == F(3, 5)
    L.append("  s3-3.1 appendix A with the poor rung spelt twice at (1/3, 1/6): accepted, nothing disclosed (the twins are a")
    L.append("         spelling), and one right grade gives P(x) = 3/5 exactly as appendix A does")
    Wg = reliability_world([F(1, 2), F(9, 10)], [F(1, 2), F(1, 2)], F(-19)); Wg["after"]["price"] = F(1, 100)
    assert after_taken(Wg)
    L.append("  s3-4.1 draft 6's G1 with an After-act at 1/100: taken, and paid, every episode - it cannot teach the Globals,")
    L.append("         but it checks the model, which the model cannot value; the owner decides by declaring it (draft 11)")
    W0 = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False)
    ls, gs = vals(W0["locals"]), vals(W0["globals"]); other = {"a1": "a2", "a2": "a1"}
    W0["N"] = 2; W0["d"] = 2
    W0["O"]["check"] = {"K": {(l, g): {l[0]: F(7, 10), other[l[0]]: F(3, 10)} for l in ls for g in gs}, "price": F(0), "once": True}
    six = Counter({((("ask", "a1"), ("check", "a1")), "say a1", None): 6})
    assert post_global(W0, six)[("9/10",)] == F(1771561, 2303002)
    L.append("  s3-1.1 Counts written under check = 4/5, shipped into the refit check = 7/10: the refit conditions on the same")
    L.append("         facts under its own kernel, P(good) = 11^6/(11^6 + 9^6) = 1771561/2303002")
    A3 = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    c3 = Counter({rec("a1", "a1", "say a1"): 2, rec("a1", "a2", "say a1"): 1})
    assert post_global(A3, c3)[("9/10",)] == F(9, 25) and loo_score(A3, c3) == F(1125, 100672)
    L.append("  s3-6.1 appendix A shipping {right: 2, wrong: 1}: P(good) = 9/25; the leave-one-out Score is the rational")
    L.append("         1125/100672, which the kernel recomputes and the pack must match")
    # ---- attack session 4 on draft 10 (2026-09-23)
    W1 = railed_world(); ls1 = vals(W1["locals"]); gs1 = [("x",), ("y",)]
    pA = {("x",): F(7, 10), ("y",): F(3, 10)}
    W1["prior_local"] = {g: {l: (pA[g] if l[0] == "1" else 1 - pA[g]) * (F(99, 100) if l[1] == "1" else F(1, 100)) for l in ls1} for g in gs1}
    w = episode_world(W1, Counter()); assert REF.solve(w["prior"], w, 1)[1] == "useB" and after_taken(W1)
    assert e7(W1, Counter({((), "useB", "1"): 25, ((), "useB", "0"): 25})) == F(49, 100)
    L.append("  s4-2.1 appendix G with B declared 99/100 and true 1/2: the policy plays useB forever; graded every episode, E7")
    L.append("         prints 49/100 (draft 9 struck every B grade, and E7 printed nothing)")
    Ws = reliability_world([F(1), F(9, 10)], [F(1, 2), F(1, 2)], F(-2))
    cs = Counter({rec("a1", "a1", "say a1"): 9 + 30, rec("a2", "a2", "say a2"): 30, rec("a1", "a2", "say a1"): 1 + 20, rec("a2", "a1", "say a2"): 20})
    assert post_global(Ws, cs)[("1",)] == 0 and e7(Ws, cs) > F(1, 5)
    L.append("  s4-2.1'' a rung at 1 killed by the first wrong grade: grading continues, and E7 prints about 3/10 against the")
    L.append("         true 3/5 (draft 9 stopped grading at the point mass, and E7 printed 0)")
    Wf = railed_world(); Wf["prior_local"] = {g: {l: (pA[g] if l[0] == "1" else 1 - pA[g]) * (F(1) if l[1] == "1" else F(0)) for l in ls1} for g in gs1}
    try: post_global(Wf, Counter({((), "useB", "0"): 1})); assert False
    except Refused as e: assert str(e) == "FALSIFIED"
    L.append("  s4-2.2 s_B declared 1 everywhere, true 1/2: the first graded 0 falsifies the World and ends the plate (J26)")
    F2 = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False)
    ls2, gs2 = vals(F2["locals"]), vals(F2["globals"]); oth = {"a1": "a2", "a2": "a1"}
    F2["O"]["check"] = {"K": {(l, g): {l[0]: F(7, 10), oth[l[0]]: F(3, 10)} for l in ls2 for g in gs2}, "price": F(0), "once": True}
    F2["N"] = 2; F2["d"] = 2
    long_ = Counter({((("ask", "a1"), ("check", "a2"), ("check", "a2")), "abstain", None): 1})
    F2["counts"] = long_; F2["counts_sha"] = counts_sha(long_); F2["score"] = F(1)
    try: refuse(F2); assert False
    except Refused as e: assert str(e) == "PLATE"
    L.append("  s4-1.1a shipped records with three draws, `check` twice, into a declaration with N = 2 and `check` once: PLATE")
    Fb = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); lsb, gsb = vals(Fb["locals"]), vals(Fb["globals"])
    Fb["O"]["ask"]["K"] = {(l, g): {l[0]: F(1)} for l in lsb for g in gsb}
    imp = Counter({rec("a1", "a2", "say a1"): 1})
    assert not expressible(Fb, imp)
    L.append("  s4-1.1b a shipped wrong grade into a declaration whose instrument is perfect: impossible under every Global, PLATE")
    F3 = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False)
    F3["O"]["check"] = {"K": {(l, g): {l[0]: F(4, 5), oth[l[0]]: F(1, 5)} for l in ls2 for g in gs2}, "price": F(0), "once": True}
    assert not realisable(F3, ((("ask", "a1"), ("check", "a1")), "say a1", None))
    L.append("  s4-3.1 appendix F's two-draw records into its N = 1 refit: not realisable there, so not shippable (PLATE)")
    SK = stakes_world(); refuse(SK)
    assert not learns_nothing(SK) and len(unwashable(SK)) == 2
    L.append("  s4-1.3 a stakes Global nothing can inform beside a reliability that can be learned: accepted, and the stakes")
    L.append("         disclosed in both reliability classes - the same verdict as with the stakes alone, which learns nothing")
    SK1 = stakes_world(rel_fixed=True); refuse(SK1); assert learns_nothing(SK1)
    # ---- attack session 5 on draft 12 (2026-09-23)
    Wa = reliability_world([F(9, 10), F(3, 5)], [F(1, 5), F(4, 5)], F(-2)); lsa, gsa = vals(Wa["locals"]), vals(Wa["globals"])
    Wa["O"]["peek"] = {"K": {(l, g): {"drop": F(1, 2), "go": F(1, 2)} for l in lsa for g in gsa}, "price": F(0), "once": True, "ends": {"drop"}}
    Wa["N"] = 2; Wa["d"] = 2
    assert not realisable(Wa, ((("peek", "drop"), ("ask", "a1")), "say a1", "a1"))
    L.append("  s5-1.1a a shipped record with `ask` after an ending `drop`: no episode can write it (an ending outcome is the last")
    L.append("         draw, and then the end), so PLATE; the kernel's policy is never consulted")
    Wb = base_rate_world(F(3)); c3 = Counter({((("ask", "a2"),), "say a2", None): 3})
    Wb["counts"] = c3; Wb["counts_sha"] = counts_sha(c3); Wb["score"] = loo_score(Wb, c3); refuse(Wb)
    w = episode_world(Wb, c3)
    assert post_global(Wb, c3)[("g2",)] == F(64, 65) and REF.solve(w["prior"], w, 1) == (F(189, 325), "say a2")
    L.append("  s5-1.1b a refit that raised `ask` to 3 accepts Counts its kernel would no longer write: P(g2) = 64/65, `say a2`")
    L.append("         at 189/325 without asking - the records are facts, and could be written under v0's loop")
    Wc = confounded_world(); refuse(Wc); assert unwashable(Wc) == []
    c = Counter({((("ask", "a1"),), "say a1", "a1"): 370, ((("ask", "a1"),), "say a1", "a2"): 130,
                 ((("ask", "a2"),), "say a2", "a2"): 370, ((("ask", "a2"),), "say a2", "a1"): 130})
    assert post_global(Wc, c)[("r9",)] > F(9999, 10000) and e7(Wc, c) < F(1, 10**5)
    L.append("  s5-2.1 conceded: a grader declared at 4/5 and truly perfect, `ask` truly at 37/50 - the truth's record law is")
    L.append("         r9's exactly, so P(r9) -> 1 and E7 -> 0 while the agent loses 3/10 an episode; no record can show it")
    A = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    one_wrong = Counter([rec("a1", "a2", "say a1")])
    assert plate_value(A, 2, one_wrong, one_run=True) == F(3, 100) and plate_value(A, 2, one_wrong) == 0
    L.append("  s5-2.2 appendix A after one wrong grade: the kernel stops asking, but the one-run maximiser of the same model")
    L.append("         asks while two episodes remain (value 3/100 against 0) - acting to learn looks when the model says it teaches")
    Wd = colour_world(); refuse(Wd); assert learns_nothing(Wd) and unwashable(Wd) == []
    L.append("  s5-3.1 a Global that governs only a colour no utility reads: one class, 'nothing can be learned', and no class")
    L.append("         disclosed as settling something a utility reads")
    W7 = w7a_world(1); W72 = w7a_world(2)
    assert plate_value(W7, 2) == F(291, 250) and plate_value(W72, 2) == F(28, 25)
    # ---- attack session 6 on draft 13 (2026-09-23)
    import meta_check as M
    acts = []
    for pi in (F(9, 10), F(1, 10)):
        Wt = cap_world(pi); assert len(classes(Wt)) == 1 and len(unwashable(Wt)) == 1
        w = episode_world(Wt, Counter()); w["O"]["k"]["ends"] = {"e": {s_: F(1, 5) for s_ in w["prior"]}}
        w.update({k_: Wt[k_] for k_ in ("dplus", "fraction", "rate", "ops")})
        a_, how, _ = M.DPLUS.step(w["prior"], w, 2); acts.append((how, a_))
    assert acts == [("think", "scan"), ("refused", "test")]
    L.append("  s6-3.1 with the think act declared, an inseparable class decides the act through the cap: P(x) = 9/10 buys")
    L.append("         theta and plays scan, 1/10 refuses it and plays test, forever - now listed, as the cap reads best(state)")
    assert unwashable(echo_world()) == [] and unwashable(bonus_world()) == []
    L.append("  s6-3.2, 3.3 an honest against an echoing grader, and a per-state bonus on a colour: nothing listed - no act reads")
    L.append("         the after-report, and a per-state constant changes no act (v0 C4)")
    D2 = falsified_refit_world(); good = Counter({rec("a1", "a1", "say a1"): 16, rec("a2", "a2", "say a2"): 4})
    fals = rec("a2", "a1", "say a2")
    p_no = post_global(D2, good); p_yes = post_global(D2, good + Counter([fals]))
    perfect = lambda pg: sum(v for g, v in pg.items() if g[1] == "1")
    assert perfect(p_no) == F(10**20, 10**20 + 9**20) and perfect(p_yes) == 0
    for pg, want in ((p_no, "say a2"), (p_yes, "abstain")):
        w = episode_world(D2, Counter(), pg); b = REF.condition(w["prior"], w["O"]["ask"]["K"], "a2")
        assert REF.solve(b, w, 0)[1] == want
    D2["counts"] = good; D2["falsifiers"] = [fals]; D2["counts_sha"] = counts_sha(good, [fals])
    D2["score"] = loo_score(D2, good, [fals]); refuse(D2)
    assert post_global(D2, evidence(D2)) == p_yes
    L.append("  s6-5.1 a refit shipped a falsified plate's Counts: without the falsifying record P(ask perfect) = 10^20/(10^20 + 9^20)")
    L.append("         and it says a2; with it, 0 and it abstains - the falsifier now travels with its Counts (J26)")
    WJ = grader_global_world(); cls = [set(c) for c in unwashable(WJ)]
    assert {("4/5", "9/10"), ("9/10", "4/5")} in cls
    L.append("  s6-2.1 the grader declared a Global, the truth (ask 37/50, grader 1) on no grid: S15 still lists the confound")
    L.append("         {(4/5, 9/10), (9/10, 4/5)} - C27's 'only if the true value is on the grid' was false")
    A7 = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); A7["O"]["ask"]["price"] = F(7, 10)
    assert all(plate_value(A7, T) == 0 and plate_value(A7, T, one_run=True) == 0 for T in (1, 2, 3))
    L.append("  s6-2.2 appendix A with ask at 7/10: the model says ask teaches, yet the lesson is worth nothing under it, so the")
    L.append("         one-run maximiser abstains too (value 0); a truly perfect ask forgoes 3/10 an episode, unseen")
    L.append("  s5-7.17 v0's C8 over a plate: horizon 1 is worth 291/250 over two episodes, horizon 2 only 28/25 - C8 is a")
    L.append("         per-episode theorem (with C5); a longer horizon exploits within the episode and never buys the grade")
    # ---- brief 007's questions and SURFACE v0.2 session 1 (2026-09-24)
    Wq = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); lsq, gsq = vals(Wq["locals"]), vals(Wq["globals"])
    Wq["O"]["peek"] = {"K": {(l, g): {"drop": F(1, 2), "go": F(1, 2)} for l in lsq for g in gsq}, "price": F(0), "once": True,
                       "ends": {"drop"}, "u_end": {"drop": F(0)}}
    Wq["N"] = 2; Wq["d"] = 2
    try: refuse(Wq); assert False
    except Refused as e: assert str(e) == "AFTER"
    Wq["after"]["K"]["end:peek=drop"] = {(l, g): {l[0]: F(1)} for l in lsq for g in gsq}; refuse(Wq)
    assert realisable(Wq, ((("peek", "drop"),), "end:peek=drop", "a1")) and not realisable(Wq, ((("peek", "drop"), ("ask", "a1")), "say a1", "a1"))
    L.append("  Q8 an After-act kernel for every end, an ending outcome's included: refused AFTER without its row, accepted with it")
    pre = ((("ask", "a1"),), None, None)
    assert realisable(A, pre, falsifier=True) and not realisable(A, pre)
    L.append("  Q9 a falsifier from a report inside an episode - draws up to it, no end, no after-report - is shippable")
    Ws = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); c1 = Counter([rec("a1", "a1", "say a1")])
    Ws["counts"] = c1; Ws["falsifiers"] = [rec("a1", "a2", "say a1")]; Ws["counts_sha"] = counts_sha(c1, Ws["falsifiers"])
    Ws["score"] = loo_score(Ws, c1, Ws["falsifiers"]); refuse(Ws)
    assert counts_sha(c1, Ws["falsifiers"]) != counts_sha(c1)
    L.append("  s02-1.2 the digest covers the falsifying records: shipping one changes the digest, and the Score scores it")
    return L

def cap_world(pi):
    "session 6, 3.1: `k` emits the ending e with 1/2 under both Globals, but under y only in the z1 states; theta declared"
    L = [("h", ["sick", "well"]), ("z", ["z1", "z2"])]; ls = vals(L); gs = [("x",), ("y",)]; ph = {"sick": F(1, 5), "well": F(4, 5)}
    Kt = {"sick": {"+": F(9, 10), "-": F(1, 10)}, "well": {"+": F(1, 5), "-": F(4, 5)}}
    Ks = {"sick": {"y": F(9, 10), "n": F(1, 10)}, "well": {"y": F(2, 5), "n": F(3, 5)}}
    Kk = lambda l, g: {"e": F(1, 2), "m": F(1, 2)} if g == ("x",) else ({"e": F(1)} if l[1] == "z1" else {"m": F(1)})
    T = {"treat": {(l, g): (F(0) if l[0] == "sick" else F(-2)) for l in ls for g in gs},
         "leave": {(l, g): (F(-10) if l[0] == "sick" else F(0)) for l in ls for g in gs}}
    return {"locals": L, "globals": [("g", ["x", "y"])], "prior_global": {("x",): pi, ("y",): 1 - pi},
            "prior_local": {g: {l: ph[l[0]] * F(1, 2) for l in ls} for g in gs}, "T": T,
            "O": {"test": {"K": {(l, g): Kt[l[0]] for l in ls for g in gs}, "price": F(1, 2), "once": True},
                  "scan": {"K": {(l, g): Ks[l[0]] for l in ls for g in gs}, "price": F(1, 5), "once": True},
                  "k": {"K": {(l, g): Kk(l, g) for l in ls for g in gs}, "price": F(10), "once": True, "u_end": {"e": F(1, 5)}}},
            "N": 2, "d": 1, "dplus": 2, "fraction": F(1, 2), "rate": F(1, 400), "ops": {s_: F(25 * s_) for s_ in range(1, 9)}}

def echo_world():
    "session 6, 3.2: an honest grader against one that echoes the report's noise; one class, and no act reads the grade"
    L = [("X", ["a1", "a2"]), ("D", ["a1", "a2"])]; ls = vals(L); gs = [("honest",), ("echo",)]; oth = {"a1": "a2", "a2": "a1"}
    pl = {g: {l: F(1, 2) * (F(4, 5) if l[1] == l[0] else F(1, 5)) for l in ls} for g in gs}
    T = {"say a1": {(l, g): (F(1) if l[0] == "a1" else F(-2)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l[0] == "a2" else F(-2)) for l in ls for g in gs}, "abstain": {(l, g): F(0) for l in ls for g in gs}}
    aft = lambda l, g: {l[0]: F(1)} if g == ("honest",) else {l[1]: F(4, 5), oth[l[1]]: F(1, 5)}
    return {"locals": L, "globals": [("g", ["honest", "echo"])], "prior_global": {g: F(1, 2) for g in gs}, "prior_local": pl, "T": T,
            "O": {"ask": {"K": {(l, g): {l[1]: F(1)} for l in ls for g in gs}, "price": F(0), "once": True}},
            "after": {"K": {t: {(l, g): aft(l, g) for l in ls for g in gs} for t in T}, "price": F(0)}, "N": 1, "d": 1}

def bonus_world():
    "session 6, 3.3: appendix J's colour World with +1 on every terminal when red - a per-state constant"
    W = colour_world()
    W["T"] = {t: {(l, g): u + (F(1) if l[1] == "red" else F(0)) for (l, g), u in r.items()} for t, r in W["T"].items()}
    return W

def falsified_refit_world():
    "session 6, 5.1: Globals (base rate, rho); `ask` reports with rho; a free perfect After-act; -19 for a wrong answer"
    L = [("answer", ["a1", "a2"])]; G = [("base", ["lo", "hi"]), ("rho", ["1", "9/10"])]; ls, gs = vals(L), vals(G); oth = {"a1": "a2", "a2": "a1"}
    pa = {"lo": F(1, 5), "hi": F(4, 5)}
    T = {"say a1": {(l, g): (F(1) if l == ("a1",) else F(-19)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l == ("a2",) else F(-19)) for l in ls for g in gs}, "abstain": {(l, g): F(0) for l in ls for g in gs}}
    return {"locals": L, "globals": G, "prior_global": {g: F(1, 4) for g in gs},
            "prior_local": {g: {("a1",): pa[g[0]], ("a2",): 1 - pa[g[0]]} for g in gs}, "T": T,
            "O": {"ask": {"K": {(l, g): {l[0]: F(g[1]), oth[l[0]]: 1 - F(g[1])} for l in ls for g in gs}, "price": F(0), "once": True}},
            "after": {"K": {t: {(l, g): {l[0]: F(1)} for l in ls for g in gs} for t in T}, "price": F(0)}, "N": 1, "d": 1}

def grader_global_world():
    "session 6, 2.1: appendix J's confound with the grader's reliability a Global; ask on {4/5, 9/10, 1}, grader on {4/5, 9/10}"
    L = [("answer", ["a1", "a2"])]; G = [("ask", ["4/5", "9/10", "1"]), ("grader", ["4/5", "9/10"])]; ls, gs = vals(L), vals(G); oth = {"a1": "a2", "a2": "a1"}
    T = {"say a1": {(l, g): (F(1) if l == ("a1",) else F(-4)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l == ("a2",) else F(-4)) for l in ls for g in gs}, "abstain": {(l, g): F(0) for l in ls for g in gs}}
    return {"locals": L, "globals": G, "prior_global": {g: F(1, 6) for g in gs}, "prior_local": {g: {l: F(1, 2) for l in ls} for g in gs}, "T": T,
            "O": {"ask": {"K": {(l, g): {l[0]: F(g[0]), oth[l[0]]: 1 - F(g[0])} for l in ls for g in gs}, "price": F(0), "once": True}},
            "after": {"K": {t: {(l, g): {l[0]: F(g[1]), oth[l[0]]: 1 - F(g[1])} for l in ls for g in gs} for t in T}, "price": F(0)}, "N": 1, "d": 1}

def base_rate_world(price):
    "session 5, W1b: the Global governs the answer's base rate; `ask` reports perfectly at the given price; no After-act"
    L = [("answer", ["a1", "a2"])]; G = [("g", ["g1", "g2"])]; ls, gs = vals(L), vals(G)
    pa = {("g1",): F(4, 5), ("g2",): F(1, 5)}
    T = {"say a1": {(l, g): (F(1) if l == ("a1",) else F(-1)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l == ("a2",) else F(-1)) for l in ls for g in gs}}
    return {"locals": L, "globals": G, "prior_global": {g: F(1, 2) for g in gs},
            "prior_local": {g: {("a1",): pa[g], ("a2",): 1 - pa[g]} for g in gs}, "T": T,
            "O": {"ask": {"K": {(l, g): {l[0]: F(1)} for l in ls for g in gs}, "price": price, "once": True}}, "N": 1, "d": 1}

def confounded_world():
    "session 5, W2.1: reliability on {9/10, 1}; the grader declared to report the answer with 4/5; penalty -4"
    L = [("answer", ["a1", "a2"])]; ls = vals(L); gs = [("r9",), ("r1",)]; rho = {("r9",): F(9, 10), ("r1",): F(1)}; oth = {"a1": "a2", "a2": "a1"}
    T = {"say a1": {(l, g): (F(1) if l == ("a1",) else F(-4)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l == ("a2",) else F(-4)) for l in ls for g in gs}, "abstain": {(l, g): F(0) for l in ls for g in gs}}
    return {"locals": L, "globals": [("rho", ["r9", "r1"])], "prior_global": {g: F(1, 2) for g in gs},
            "prior_local": {g: {l: F(1, 2) for l in ls} for g in gs}, "T": T,
            "O": {"ask": {"K": {(l, g): {l[0]: rho[g], oth[l[0]]: 1 - rho[g]} for l in ls for g in gs}, "price": F(0), "once": True}},
            "after": {"K": {t: {(l, g): {l[0]: F(4, 5), oth[l[0]]: F(1, 5)} for l in ls for g in gs} for t in T}, "price": F(0)}, "N": 1, "d": 1}

def colour_world():
    "session 5, W3.1: the Global governs a colour that no utility, kernel or act reads"
    L = [("answer", ["a1", "a2"]), ("colour", ["red", "blue"])]; G = [("g", ["g1", "g2"])]; ls, gs = vals(L), vals(G); oth = {"a1": "a2", "a2": "a1"}
    red = {("g1",): F(1, 5), ("g2",): F(4, 5)}
    pl = {g: {l: F(1, 2) * (red[g] if l[1] == "red" else 1 - red[g]) for l in ls} for g in gs}
    T = {"say a1": {(l, g): (F(1) if l[0] == "a1" else F(-2)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l[0] == "a2" else F(-2)) for l in ls for g in gs}, "abstain": {(l, g): F(0) for l in ls for g in gs}}
    return {"locals": L, "globals": G, "prior_global": {g: F(1, 2) for g in gs}, "prior_local": pl, "T": T,
            "O": {"ask": {"K": {(l, g): {l[0]: F(4, 5), oth[l[0]]: F(1, 5)} for l in ls for g in gs}, "price": F(0), "once": True}},
            "after": {"K": {t: {(l, g): {l[0]: F(1)} for l in ls for g in gs} for t in T}, "price": F(0)}, "N": 1, "d": 1}

def w7a_world(N):
    "session 5, W7a: A fresh and free at 4/5 everywhere; B once at 1/10, perfect if good and 3/5 if poor; P(good) = 7/10"
    L = [("answer", ["a1", "a2"])]; G = [("g", ["good", "poor"])]; ls, gs = vals(L), vals(G); oth = {"a1": "a2", "a2": "a1"}
    rb = {("good",): F(1), ("poor",): F(3, 5)}
    T = {"say a1": {(l, g): (F(1) if l == ("a1",) else F(-2)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l == ("a2",) else F(-2)) for l in ls for g in gs}, "abstain": {(l, g): F(0) for l in ls for g in gs}}
    return {"locals": L, "globals": G, "prior_global": {("good",): F(7, 10), ("poor",): F(3, 10)},
            "prior_local": {g: {l: F(1, 2) for l in ls} for g in gs}, "T": T,
            "O": {"A": {"K": {(l, g): {l[0]: F(4, 5), oth[l[0]]: F(1, 5)} for l in ls for g in gs}, "price": F(0), "once": False},
                  "B": {"K": {(l, g): {l[0]: rb[g], oth[l[0]]: 1 - rb[g]} for l in ls for g in gs}, "price": F(1, 10), "once": True}},
            "after": {"K": {t: {(l, g): {l[0]: F(1)} for l in ls for g in gs} for t in T}, "price": F(0)}, "N": N, "d": N}

def stakes_world(rel_fixed=False):
    "session 4, 1.3: the penalty is a local that copies a stakes Global; the reliability is a second Global, or fixed"
    rels = ["good"] if rel_fixed else ["good", "poor"]; R = {"good": F(9, 10), "poor": F(3, 5)}
    G = [("rel", rels), ("stakes", ["hi", "lo"])]; L = [("answer", ["a1", "a2"]), ("penalty", ["hi", "lo"])]
    gs, ls = vals(G), vals(L); oth = {"a1": "a2", "a2": "a1"}
    pl = {g: {l: (F(1, 2) if l[1] == g[1] else F(0)) for l in ls} for g in gs}
    pen = {"hi": F(-4), "lo": F(-1)}
    T = {"say a1": {(l, g): (F(1) if l[0] == "a1" else pen[l[1]]) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l[0] == "a2" else pen[l[1]]) for l in ls for g in gs},
         "abstain": {(l, g): F(0) for l in ls for g in gs}}
    return {"locals": L, "globals": G, "prior_global": {g: F(1, len(gs)) for g in gs}, "prior_local": pl, "T": T,
            "O": {"ask": {"K": {(l, g): {l[0]: R[g[0]], oth[l[0]]: 1 - R[g[0]]} for l in ls for g in gs}, "price": F(0), "once": True}},
            "after": {"K": {t: {(l, g): {l[0]: F(1)} for l in ls for g in gs} for t in T}, "price": F(0)}, "N": 1, "d": 1}

def twin_world(py, pyp):
    "session 3, 3.1: appendix A with the poor rung written as two names with identical cells"
    L = [("answer", ["a1", "a2"])]; ls = vals(L); other = {"a1": "a2", "a2": "a1"}
    rel = {("x",): F(9, 10), ("y",): F(3, 5), ("yp",): F(3, 5)}; gs = list(rel)
    T = {"say a1": {(l, g): (F(1) if l == ("a1",) else F(-2)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l == ("a2",) else F(-2)) for l in ls for g in gs},
         "abstain": {(l, g): F(0) for l in ls for g in gs}}
    return {"locals": L, "globals": [("g", ["x", "y", "yp"])], "prior_global": {("x",): F(1, 2), ("y",): py, ("yp",): pyp},
            "prior_local": {g: {l: F(1, 2) for l in ls} for g in gs}, "T": T,
            "O": {"ask": {"K": {(l, g): {l[0]: rel[g], other[l[0]]: 1 - rel[g]} for l in ls for g in gs}, "price": F(0), "once": True}},
            "after": {"K": {t: {(l, g): {l[0]: F(1)} for l in ls for g in gs} for t in T}, "price": F(0)}, "N": 1, "d": 1}

def two_world():
    "session 2, 3.2: reliabilities (r1, r2) of two instruments on {3/5, 9/10}^2, uniform; check priced 3/20"
    L = [("answer", ["a1", "a2"])]; G = [("r1", ["3/5", "9/10"]), ("r2", ["3/5", "9/10"])]
    gs, ls = vals(G), vals(L); other = {"a1": "a2", "a2": "a1"}
    K = lambda i: {(l, g): {l[0]: F(g[i]), other[l[0]]: 1 - F(g[i])} for l in ls for g in gs}
    T = {"say a1": {(l, g): (F(1) if l == ("a1",) else F(-2)) for l in ls for g in gs},
         "say a2": {(l, g): (F(1) if l == ("a2",) else F(-2)) for l in ls for g in gs},
         "abstain": {(l, g): F(0) for l in ls for g in gs}}
    return {"locals": L, "globals": G, "prior_global": {g: F(1, 4) for g in gs}, "prior_local": {g: {l: F(1, 2) for l in ls} for g in gs},
            "T": T, "O": {"ask": {"K": K(0), "price": F(0), "once": True}, "check": {"K": K(1), "price": F(3, 20), "once": True}},
            "N": 2, "d": 2}

def railed_world():
    "session 2, 2.1: useA's bit is 7/10 under x and 3/10 under y; useB's is 1/2 under both, so B-records teach nothing"
    gs = [("x",), ("y",)]; L = [("sA", ["1", "0"]), ("sB", ["1", "0"])]; ls = vals(L)
    pA = {("x",): F(7, 10), ("y",): F(3, 10)}
    pl = {g: {l: (pA[g] if l[0] == "1" else 1 - pA[g]) * F(1, 2) for l in ls} for g in gs}
    return {"locals": L, "globals": [("g", ["x", "y"])], "prior_global": {g: F(1, 2) for g in gs}, "prior_local": pl,
            "T": {"useA": {(l, g): (F(1) if l[0] == "1" else F(-1)) for l in ls for g in gs},
                  "useB": {(l, g): (F(1) if l[1] == "1" else F(-1)) for l in ls for g in gs}},
            "O": {}, "after": {"K": {"useA": {(l, g): {l[0]: F(1)} for l in ls for g in gs},
                                     "useB": {(l, g): {l[1]: F(1)} for l in ls for g in gs}}, "price": F(0)},
            "N": 1, "d": 1}

def oscillating_world():
    """attack session 1, F11: Global g in {x, y}; the local is two instruments' success bits, independent given g;
    useA succeeds with 1/2 under x and 9/10 under y, useB the reverse; the after-act reveals the bit of the act fired."""
    gs = [("x",), ("y",)]; L = [("sA", ["1", "0"]), ("sB", ["1", "0"])]; ls = vals(L)
    pA = {("x",): F(1, 2), ("y",): F(9, 10)}; pB = {("x",): F(9, 10), ("y",): F(1, 2)}
    pl = {g: {l: (pA[g] if l[0] == "1" else 1 - pA[g]) * (pB[g] if l[1] == "1" else 1 - pB[g]) for l in ls} for g in gs}
    return {"locals": L, "globals": [("g", ["x", "y"])], "prior_global": {g: F(1, 2) for g in gs}, "prior_local": pl,
            "T": {"useA": {(l, g): (F(1) if l[0] == "1" else F(-1)) for l in ls for g in gs},
                  "useB": {(l, g): (F(1) if l[1] == "1" else F(-1)) for l in ls for g in gs}},
            "O": {}, "after": {"K": {"useA": {(l, g): {"A" + l[0]: F(1)} for l in ls for g in gs},
                                     "useB": {(l, g): {"B" + l[1]: F(1)} for l in ls for g in gs}}, "price": F(0)},
            "N": 1, "d": 1}

def decomposition_price():
    "appendix B: the price of the episode decomposition, by exact dynamic programming over the plate"
    from functools import lru_cache
    A = F(4, 5); TH = [F(99, 100), F(1, 2)]
    def val(r): return max(2 * r - 1, F(0))
    def Eth(w): return (w[0] * TH[0] + w[1] * TH[1]) / (w[0] + w[1])
    def upd(w, right): return (w[0] * (TH[0] if right else 1 - TH[0]), w[1] * (TH[1] if right else 1 - TH[1]))
    @lru_cache(None)
    def myopic(w, t):
        if t == 0: return F(0)
        if val(A) >= val(Eth(w)): return val(A) + myopic(w, t - 1)
        p = Eth(w); return val(Eth(w)) + p * myopic(upd(w, True), t - 1) + (1 - p) * myopic(upd(w, False), t - 1)
    @lru_cache(None)
    def plate(w, t):
        if t == 0: return F(0)
        p = Eth(w)
        return max(val(A) + plate(w, t - 1), val(Eth(w)) + p * plate(upd(w, True), t - 1) + (1 - p) * plate(upd(w, False), t - 1))
    w0 = (F(1, 2), F(1, 2))
    prices = {T: plate(w0, T) - myopic(w0, T) for T in (2, 3, 5, 8)}
    assert prices[2] == 0 and prices[3] == F(39319, 1000000) and prices[5] == F(3499390519, 10000000000)
    return prices

def paid_global_world():
    W = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    W["T"]["say a1"][(("a1",), ("9/10",))] = F(2); return W

def peek_world(drop=F(1, 2)):
    """brief 007's Q8 and brief 008's Q14 and Q15: appendix A with a free `once` act `peek` whose outcome `drop` ends the
    episode, N = 2, and an After-act row for the ending end. With drop = 0, `drop` is named and never has mass: a door that
    reports it falsifies the World, and the falsifying report is an ending outcome (Q15)."""
    W = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); ls, gs = vals(W["locals"]), vals(W["globals"])
    W["O"]["peek"] = {"K": {(l, g): {"drop": drop, "go": 1 - drop} for l in ls for g in gs}, "price": F(0), "once": True,
                      "ends": {"drop"}, "u_end": {"drop": {(l, g): F(0) for l in ls for g in gs}}}
    W["N"] = 2; W["d"] = 2
    W["after"]["K"]["end:peek=drop"] = {(l, g): {l[0]: F(1)} for l in ls for g in gs}
    return W

def ending_ask_world(drop):
    """QUESTIONS.md Q15's shape: appendix A whose informative act `ask` also names an ending outcome `drop`, with mass `drop`
    in every state, the rest reporting the answer with the reliability; an After-act row for end:ask=drop. The policy plays
    `ask`, so the plate reaches the ending outcome; with drop = 0, a door that reports it falsifies the World at an ending
    outcome, and the falsifying record is the prefix ((ask, drop),)."""
    W = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); ls, gs = vals(W["locals"]), vals(W["globals"])
    other = {"a1": "a2", "a2": "a1"}
    W["O"]["ask"]["K"] = {(l, g): {l[0]: (1 - drop) * F(g[0]), other[l[0]]: (1 - drop) * (1 - F(g[0])), "drop": drop} for l in ls for g in gs}
    W["O"]["ask"]["ends"] = {"drop"}; W["O"]["ask"]["u_end"] = {"drop": {(l, g): F(0) for l in ls for g in gs}}
    W["after"]["K"]["end:ask=drop"] = {(l, g): {l[0]: F(1)} for l in ls for g in gs}
    return W

# the pinned Worlds of the appendices, the attack sessions and the builder's questions, which the gate checks run on
PINNED = {"appendix A": lambda: reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)),
          "the router": lambda: router_world(False), "honest ignorance": two_world, "the stakes": stakes_world,
          "the held threshold": oscillating_world, "the railed act": railed_world, "the falsified refit": falsified_refit_world,
          "the echoing grader": echo_world, "the colour": colour_world, "the confound": confounded_world,
          "the grader a Global": grader_global_world, "the base rate": lambda: base_rate_world(F(0)), "C8 over a plate": lambda: w7a_world(2),
          "the cap": lambda: cap_world(F(9, 10)), "twins": lambda: twin_world(F(1, 3), F(1, 6)),
          "an ending outcome (Q8, Q14)": peek_world, "an ending outcome that never has mass": lambda: peek_world(F(0)),
          "the informative act ends the episode": lambda: ending_ask_world(F(1, 5)), "the informative act's ending outcome never has mass (Q15)": lambda: ending_ask_world(F(0))}

def run(impl, worlds, seed):
    rng = random.Random(seed); fails = {c: 0 for c, _ in CHECKS}; fails["REFUSE"] = 0
    for W, recs in worlds:
        for cname, chk in CHECKS:
            try: ok = chk(impl, W, recs, random.Random(rng.random()))
            except Exception: ok = False
            fails[cname] += not ok
    for Wbad, name in ((paid_global_world(), "GLOBAL"),):
        try: impl.declare(Wbad); fails["REFUSE"] += 1
        except Refused as e: fails["REFUSE"] += str(e) != name
    Rc = router_world(verdict=False, credence_prior=True)
    fails["REFUSE"] += impl.disclose(Rc) != unwashable(Rc)
    return fails

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=20260922); ap.add_argument("--worlds", type=int, default=40)
    a = ap.parse_args(); rng = random.Random(a.seed)
    worlds = []
    for _ in range(a.worlds):
        W = rand_world(rng)
        try: refuse(W)
        except Refused: continue
        worlds.append((W, rand_records(W, rng, rng.randint(3, 7))))
    Wa = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    worlds += [(Wa, [rec("a1", "a1"), rec("a2", "a1"), rec("a1", "a1")]), (Wa, [rec("a1", "a2"), rec("a2", "a2"), rec("a1", "a1")])]
    lw = levels_world(); worlds.append((lw, []))
    aw = after_world(); aw["after_informative"] = {"say a1": True}; worlds.append((aw, []))
    names = [c for c, _ in CHECKS] + ["REFUSE"]
    print(f"{len(worlds)} Worlds ({a.worlds} random drawn, identifiable ones kept, plus A, levels, after). Cells = Worlds failing.\n")
    print(f"{'implementation':72s}" + "".join(f"{c:>7s}" for c in names))
    ok = True
    ref = run(REFI, worlds, a.seed); print(f"{REFI.name[:72]:72s}" + "".join(f"{ref[c]:7d}" for c in names))
    if any(ref.values()): ok = False; print("  ^^ THE PAGE IS WRONG: the reference fails its own consequences")
    print()
    for p in POISONS:
        f = run(p, worlds, a.seed); killed = any(f.values())
        print(f"{p.name[:72]:72s}" + "".join(f"{f[c]:7d}" for c in names) + ("" if killed else "   <-- SURVIVES"))
        ok &= killed
    print("\nfrozen vectors:")
    for l in frozen(): print(l)
    pr = decomposition_price()
    print("  B  price of the episode decomposition: " + ", ".join(f"T={T} {float(v):.4f}" for T, v in pr.items()))
    print("\nPAGE PASSES" if ok else "\nPAGE FAILS"); sys.exit(0 if ok else 1)
