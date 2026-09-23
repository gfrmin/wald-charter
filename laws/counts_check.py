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

def design_dist(W, g, seq, t):
    "the law of a design's outcomes and the after-report under end t, the local summed out under P(local | g)"
    dist, after = {}, W.get("after")
    for l, pl in W["prior_local"][g].items():
        if pl == 0: continue
        rows = [list(W["O"][k]["K"][(l, g)].items()) for k in seq]
        arow = after["K"][t][(l, g)] if (after and t is not None) else {None: F(1)}
        for combo in itertools.product(*rows):
            p = pl
            for _, q in combo: p *= q
            for oa, qa in arow.items():
                key = (tuple(o for o, _ in combo), oa); dist[key] = dist.get(key, F(0)) + p * qa
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

def identifiable(W):
    """S15 as of draft 7: refuse iff nothing is learnable (every Global value in one class), or the declared prior is
    not constant on some class - a prior would then decide what no plate can (credence's router). Inseparable values
    under an equal prior are honest ignorance, and learning the rest may still change the act (session 2, 3.2)."""
    cls = classes(W)
    if len(vals(W["globals"])) > 1 and len(cls) == 1: return False
    return all(len({W["prior_global"][g] for g in c}) == 1 for c in cls)

def refuse(W):
    "v0.2's refusals, by name"
    gs, ls = vals(W["globals"]), vals(W["locals"])
    for t, u in W["T"].items():                                        # S11: a Global is unpaid
        for l in ls:
            if len({u[(l, g)] for g in gs}) > 1: raise Refused("GLOBAL")
    if sum(W["prior_global"].values()) != 1 or min(W["prior_global"].values()) <= 0: raise Refused("PRIOR")
    for g in gs:
        if sum(W["prior_local"][g].values()) != 1: raise Refused("PRIOR")
    if W["globals"] and not identifiable(W): raise Refused("UNIDENTIFIED")   # S15 (draft 7)
    if W.get("counts"):                                                # S13, S14
        if W.get("counts_sha") != counts_sha(W["counts"]): raise Refused("PLATE")
        if "score" not in W: raise Refused("UNSCORED")
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
    before it, so no selection enters (attack session 2, 1.3: a per-design predictive printed 1/2 on a correct World)."""
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
        den = sum(pg[g] * seq_prob(W, g, list(hist), t) for g in pg)
        tv[(hist, k, t)] = sum(abs(F(c.get(o, 0), tot) - sum(pg[g] * seq_prob(W, g, list(hist) + [(k, o)], t) for g in pg) / den)
                               for o in outs) / 2
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
    name = "reference (CHARTER v0.2 draft 8)"
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
    try: refuse(reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False)); assert False
    except Refused as e: assert str(e) == "UNIDENTIFIED"
    L.append("  A' the same World with no after-act: refused UNIDENTIFIED (P(report) = 1/2 whatever the reliability)")
    # credence's router: what was wrong was the prior, not the unidentifiability alone
    try: refuse(router_world(verdict=False, credence_prior=True)); assert False
    except Refused as e: assert str(e) == "UNIDENTIFIED"
    refuse(router_world(verdict=False)); refuse(router_world(verdict=True, credence_prior=True))
    L.append("  R  credence's router (quality x exec reliability x false success, no ground truth) with credence's prior")
    L.append("     E[rho] = 2/3 > E[sigma] = 1/3: refused UNIDENTIFIED - the prior decides what no plate can. Under an equal")
    L.append("     prior on each swapped pair: accepted, honest ignorance. With a verdict revealing correctness: accepted")
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
    try: refuse(F1); assert False
    except Refused as e: assert str(e) == "UNIDENTIFIED"
    L.append("  s2-3.1 appendix F with N = 1: refused UNIDENTIFIED - one report is uninformative, and no realisable design takes two")
    TW = two_world(); refuse(TW)
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
    return L

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

def run(impl, worlds, seed):
    rng = random.Random(seed); fails = {c: 0 for c, _ in CHECKS}; fails["REFUSE"] = 0
    for W, recs in worlds:
        for cname, chk in CHECKS:
            try: ok = chk(impl, W, recs, random.Random(rng.random()))
            except Exception: ok = False
            fails[cname] += not ok
    for Wbad, name in ((router_world(False, credence_prior=True), "UNIDENTIFIED"), (paid_global_world(), "GLOBAL")):
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
