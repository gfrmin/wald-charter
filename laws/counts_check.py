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

# ---------------------------------------------------------------- Part 1: the amendment
def vals(dims): return [tuple(x) for x in itertools.product(*[v for _, v in dims])] if dims else [()]
def skey(l, g): return ",".join(l) + "|" + ",".join(g)
def unkey(s):
    l, g = s.split("|"); return (tuple(l.split(",")) if l else ()), (tuple(g.split(",")) if g else ())
def strK(K): return {skey(l, g): row for (l, g), row in K.items()}

def counts_sha(counts):
    rows = sorted([[[list(x) for x in obs], t, oa, n] for (obs, t, oa), n in counts.items()], key=json.dumps)
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()

def record_lik(W, rec, g):
    "P(this episode's reports and after-report | Global g): the local state is summed out under P(local | g)"
    obs, t, oa = rec; tot = F(0)
    for l, pl in W["prior_local"][g].items():
        p = pl
        for k, o in obs: p *= W["O"][k]["K"][(l, g)].get(o, F(0))
        if oa is not None: p *= W["after"]["K"][t][(l, g)].get(oa, F(0))
        tot += p
    return tot

def post_global(W, counts):
    "the declared prior over Globals conditioned on Counts - v0 `condition`, applied to a multiset of records"
    w = {g: W["prior_global"][g] for g in vals(W["globals"])}
    for rec, n in counts.items():
        for g in w: w[g] *= record_lik(W, rec, g) ** n
    s = sum(w.values())
    if s == 0: raise Refused("FALSIFIED")
    return {g: v / s for g, v in w.items()}

def episode_world(W, counts, prior=None):
    "an INTERFACE (v0) World for one episode: prior = P(Global | Counts) x P(local | Global); locals start fresh"
    pg = post_global(W, counts) if prior is None else prior
    p = {skey(l, g): pg[g] * pl for g in pg for l, pl in W["prior_local"][g].items() if pg[g] * pl > 0}
    return {"prior": p, "T": {t: strK(u) for t, u in W["T"].items()},
            "O": {k: {"K": strK(s["K"]), "price": s["price"], "once": s["once"], "ends": {}} for k, s in W["O"].items()},
            "N": W["N"], "d": W["d"], "declared_prior": {g: W["prior_global"][g] for g in pg}}

def record_dist(W, g, t):
    "the joint law of every observational act's outcome and the after-outcome under terminal t, locals summed out"
    acts = sorted(W["O"]); dist = {}
    after = W.get("after")
    for l, pl in W["prior_local"][g].items():
        if pl == 0: continue
        rows = [list(W["O"][k]["K"][(l, g)].items()) for k in acts]
        arow = after["K"][t][(l, g)] if (after and t is not None) else {None: F(1)}
        for combo in itertools.product(*rows):
            p = pl
            for _, q in combo: p *= q
            for oa, qa in arow.items():
                key = (tuple(o for o, _ in combo), oa); dist[key] = dist.get(key, F(0)) + p * qa
    return {k: v for k, v in dist.items() if v != 0}

def identifiable(W):
    """S15: no two Global values are indistinguishable under every terminal with every act taken. Taking every act is the
    most informative design, so a pair it cannot separate no policy can: refusing on this test never refuses a World
    that could learn."""
    gs = vals(W["globals"])
    ts = list(W["T"]) if W.get("after") else [None]
    dists = {t: {g: record_dist(W, g, t) for g in gs} for t in ts}
    return all(any(dists[t][g1] != dists[t][g2] for t in ts) for g1, g2 in itertools.combinations(gs, 2))

def refuse(W):
    "v0.2's refusals, by name"
    gs, ls = vals(W["globals"]), vals(W["locals"])
    for t, u in W["T"].items():                                        # S11: a Global is unpaid
        for l in ls:
            if len({u[(l, g)] for g in gs}) > 1: raise Refused("GLOBAL")
    if sum(W["prior_global"].values()) != 1 or min(W["prior_global"].values()) <= 0: raise Refused("PRIOR")
    for g in gs:
        if sum(W["prior_local"][g].values()) != 1: raise Refused("PRIOR")
    if W["globals"] and not identifiable(W): raise Refused("UNIDENTIFIED")   # S15
    if W.get("counts"):                                                # S13, S14
        if W.get("counts_sha") != counts_sha(W["counts"]): raise Refused("PLATE")
        if "score" not in W: raise Refused("UNSCORED")
    return W

def diagnostic(W, counts):
    """E7: for each design (acts taken, terminal fired), the total variation distance between the empirical distribution
    of records in Counts and their posterior predictive. Free, always printed. When a Global is misdeclared - a label
    that discards negatives, a grid that cannot hold the true rate - it does not shrink as the plate grows."""
    pg = post_global(W, counts); by = {}
    for (obs, t, oa), n in counts.items(): by.setdefault((tuple(k for k, _ in obs), t), Counter())[(obs, t, oa)] += n
    tv = {}
    for design, c in by.items():
        tot = sum(c.values()); acts, t = design
        # every record this design can produce, so predictive mass on records never seen is counted too
        outs = [sorted({o for row in W["O"][k]["K"].values() for o in row}) for k in acts]
        aouts = sorted({o for row in W["after"]["K"][t].values() for o in row}, key=str) if W.get("after") else [None]
        recs = [(tuple(zip(acts, combo)), t, oa) for combo in itertools.product(*outs) for oa in aouts]
        tv[design] = sum(abs(F(c.get(r, 0), tot) - sum(pg[g] * record_lik(W, r, g) for g in pg)) for r in recs) / 2
    return tv

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
    name = "reference (CHARTER v0.2 draft 5)"
    def declare(self, W): return refuse(W)
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
class AcceptsUnidentified(Reference):
    name = "accepts an unidentifiable Global (credence's router: symmetry broken by a hand-set prior)"
    def declare(self, W):
        if W["globals"] and not identifiable(W): return W
        return refuse(W)
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
           ProbabilityOfBest(), AcceptsUnidentified(), AcceptsPaidGlobal()]

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

def router_world(verdict):
    """credence's router in miniature (src/routing.jl): a turn is correct (C, local) with probability theta (the model's
    quality, Global); the exec signal e fires with rho if correct and sigma if not (Globals). No ground truth unless a
    verdict reveals C."""
    grid = ["1/4", "3/4"]
    L = [("C", ["1", "0"])]; G = [("theta", grid), ("rho", grid), ("sigma", grid)]
    gs, ls = vals(G), vals(L)
    Kx = {(l, g): {"1": F(g[1] if l == ("1",) else g[2]), "0": 1 - F(g[1] if l == ("1",) else g[2])} for l in ls for g in gs}
    T = {"use": {(l, g): (F(1) if l == ("1",) else F(-1)) for l in ls for g in gs}, "skip": {(l, g): F(0) for l in ls for g in gs}}
    W = {"locals": L, "globals": G, "prior_global": {g: F(1, len(gs)) for g in gs},
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
    try: refuse(reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False)); assert False
    except Refused as e: assert str(e) == "UNIDENTIFIED"
    L.append("  A' the same World with no after-act: refused UNIDENTIFIED (P(report) = 1/2 whatever the reliability)")
    # credence's router: unidentifiable without ground truth, identified with it
    try: refuse(router_world(verdict=False)); assert False
    except Refused as e: assert str(e) == "UNIDENTIFIED"
    refuse(router_world(verdict=True))
    L.append("  R  credence's router (quality x exec reliability x false success, no ground truth): refused UNIDENTIFIED;")
    L.append("     the same World with a verdict that reveals correctness: accepted")
    # credence's governor, both halves of the failure
    Wg = reliability_world([F(1, 2), F(9, 10)], [F(1, 2), F(1, 2)], F(-19))
    gaps = []
    for n in (200, 2000):
        c = Counter({rec("a1", "a1"): 99 * n // 200, rec("a2", "a2"): 99 * n // 200, rec("a1", "a2"): n // 200, rec("a2", "a1"): n // 200})
        pg = post_global(Wg, c); gap = diagnostic(Wg, c)[(("ask",), "abstain")]; gaps.append(gap)
        assert pg[("9/10",)] > F(999, 1000) and F(8, 100) < gap < F(1, 10), (float(pg[("9/10",)]), float(gap))
    L.append(f"  G1 credence's degenerate label: 99% 'right' on a grid capped at 9/10 -> certain of 9/10; E7 gap {float(gaps[0]):.4f}")
    L.append(f"     at n = 200 and {float(gaps[1]):.4f} at n = 2000: the governor's own |p1 - rate|, which more data does not close")
    Wr = reliability_world([F(1, 2), F(97, 100)], [F(1, 2), F(1, 2)], F(-19))  # break-even 19/20
    last = None
    for n in (100, 1000):
        c = Counter({rec("a1", "a1"): 93 * n // 100, rec("a1", "a2"): 7 * n // 100})
        w = episode_world(Wr, c); b = REF.condition(w["prior"], w["O"]["ask"]["K"], "a1")
        v, act = REF.solve(b, w, 0); m = post_global(Wr, c)[("97/100",)]
        assert act == "say a1" and v > 0 and (last is None or m > last); last = m
    L.append("  G2 the railed rung: true rate 93/100, grid {1/2, 97/100}, break-even 19/20 -> the agent answers (right")
    L.append("     side for 97/100, wrong for 93/100), and grows more certain as n goes 100 -> 1000")
    # PLATE: Counts are content-addressed
    Wp = reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); Wp["counts"] = Counter([rec("a1", "a1")])
    Wp["score"] = F(1, 2); Wp["counts_sha"] = counts_sha(Wp["counts"]); refuse(Wp)
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
    return L

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

def run(impl, worlds, seed):
    rng = random.Random(seed); fails = {c: 0 for c, _ in CHECKS}; fails["REFUSE"] = 0
    for W, recs in worlds:
        for cname, chk in CHECKS:
            try: ok = chk(impl, W, recs, random.Random(rng.random()))
            except Exception: ok = False
            fails[cname] += not ok
    for Wbad, name in ((router_world(False), "UNIDENTIFIED"), (paid_global_world(), "GLOBAL")):
        try: impl.declare(Wbad); fails["REFUSE"] += 1
        except Refused as e: fails["REFUSE"] += str(e) != name
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
