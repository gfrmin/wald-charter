"""
meta_check.py - tests CHARTER v0.1 (the think act) against the trusted reference in spec_check.py.

Part 1  the amendment's semantics as an agent over spec_check.Ref: cap, gain bound, predicted cost,
        theta on the menu, decide+; the policy value net of think costs; the omniscient meta-policy (E3).
Part 2  the consequences C12-C17, C19-C20 as black-box checks on any agent, plus the act-by-act comparison.
Part 3  poison agents: the ways a thinking rule goes wrong.
Part 4  the two frozen vectors of the v0.1 appendix, every attack finding as a fixed World, the kill matrix.

Worlds are the dicts of INTERFACE.md plus five keys: d (the floor), dplus (the depth a think act buys, or
absent for a v0 World), fraction (f in [0,1]), rate (utility per operation), ops ({live states: operations}).

Run:  python3 laws/meta_check.py [--seed S] [--worlds K] [--verbose]     (exit 0 = the page passes)
"""
from fractions import Fraction as F
import argparse, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec_check import Ref, REF, Rolling, policy_value, rand_world, all_utils, Refused, WorldFalsified

# ---------------------------------------------------------------- Part 1: the amendment
THETA = "θ"

def live(b): return sum(1 for p in b.values() if p > 0)

def refuse_meta(world):
    "S6, the cost table total over s, d < d+ <= N.  Refusal names FRACTION, COST, DEPTH_PLUS."
    if "dplus" not in world: return
    if not (0 <= world["fraction"] <= 1): raise Refused("FRACTION")
    if world["rate"] < 0 or set(world["ops"]) != set(range(1, len(world["prior"]) + 1)) or min(world["ops"].values()) < 0:
        raise Refused("COST")
    if not (world["d"] == 1 and world["dplus"] == 2 and world["N"] >= 2): raise Refused("DEPTH_PLUS")   # J11 (attack 2, 1.1)

class DecidePlus(Ref):
    """CHARTER v0.1 section 2.  `decide` has INTERFACE's signature and returns the act; `step` also says how the
    step was settled ('floor' for a v0 World, 'bounds', 'belief', 'think') and the predicted cost paid."""
    name = "decide+ (CHARTER v0.1)"
    def cap(self, b, world, used=frozenset()):
        """max( V_0, sum_w b(w) best(w) - cheapest price in M ); V_0 alone when M has no observational act.  [J12]
        best(w) = the largest terminal utility in w, or ending utility reachable in w (K(o|w) > 0), over acts in M."""
        M = self.menu(world, used); v0 = self.solve(b, world, 0, used)[0]
        if not M: return v0
        total = F(0)
        for w, p in b.items():
            if p == 0: continue
            best = max(u[w] for u in world["T"].values())
            for k in M:
                spec = world["O"][k]
                for o, ue in spec["ends"].items():
                    if spec["K"][w].get(o, F(0)) > 0: best = max(best, ue[w])
            total += p * best
        return max(v0, total - min(world["O"][k]["price"] for k in M))
    def vacuous(self, n, world, used):
        "the first S7 bucket: the deeper evaluation is the same evaluation, or there is nothing to look through"
        return n <= world["d"] or not self.menu(world, used)
    def gain_bound(self, b, world, n, vd, used):
        if self.vacuous(n, world, used): return F(0)
        return self.cap(b, world, used) - vd
    def cost(self, b, world): return world["rate"] * world["ops"][live(b)]
    def step(self, b, world, n, used=frozenset()):
        """how is S7's bucket: 'floor' (a v0 World), 'struck_n' (n <= d or M has no observational act),
        'struck_cap' (cap - V_d <= c), 'refused' (Q(theta) formed, not bought), 'think' (theta executed)."""
        d = world.get("d", n)                       # a kit World has had min(d, n) applied already (INTERFACE)
        vd, ad = self.solve(b, world, min(d, n), used)
        if "dplus" not in world: return ad, "floor", F(0)
        if self.vacuous(n, world, used): return ad, "struck_n", F(0)
        g = self.gain_bound(b, world, n, vd, used)
        c = self.cost(b, world)
        if g <= c: return ad, "struck_cap", F(0)                           # S7: theta struck, f not read
        if vd + world["fraction"] * g - c > vd:                             # theta last in M: strict (J14)
            return self.solve(b, world, min(world["dplus"], n), used)[1], "think", c    # C17: bought is played
        return ad, "refused", F(0)
    def decide(self, b, world, n, used=frozenset()): return self.step(b, world, n, used)[0]

HOWS = ("floor", "struck_n", "struck_cap", "refused", "think")

DPLUS = DecidePlus()

def value_net(agent, world, n=None, b=None, used=frozenset(), stats=None):
    "The value of a policy under v0.1: expected utility net of prices AND of predicted think costs.  [J15]"
    n = world["N"] if n is None else n; b = world["prior"] if b is None else b
    a, how, paid = agent.step(b, world, n, used)
    if stats is not None: stats[how] = stats.get(how, 0) + 1
    if a in world["T"]: return REF.expect(b, world["T"][a]) - paid
    spec = world["O"][a]; v = -spec["price"] - paid
    for o, po in REF.push(b, spec["K"]).items():
        if po == 0: continue
        bo = REF.condition(b, spec["K"], o)
        if o in spec["ends"]: v += po * REF.expect(bo, spec["ends"][o])
        else: v += po * value_net(agent, world, n - 1, bo, used | {a}, stats)
    return v

def omniscient_value(world, n=None, b=None, used=frozenset()):
    """E3: the meta-policy that executes theta exactly where doing so raises the policy value (ties: not think).
    An oracle, not a law (C18): it reads the deeper value before paying, which S9 forbids the agent."""
    n = world["N"] if n is None else n; b = world["prior"] if b is None else b
    def cont(a, paid):
        if a in world["T"]: return REF.expect(b, world["T"][a]) - paid
        spec = world["O"][a]; v = -spec["price"] - paid
        for o, po in REF.push(b, spec["K"]).items():
            if po == 0: continue
            bo = REF.condition(b, spec["K"], o)
            v += po * (REF.expect(bo, spec["ends"][o]) if o in spec["ends"] else omniscient_value(world, n - 1, bo, used | {a}))
        return v
    shallow = cont(REF.solve(b, world, min(world["d"], n), used)[1], F(0))
    if "dplus" not in world or n <= world["d"]: return shallow
    return max(shallow, cont(REF.solve(b, world, min(world["dplus"], n), used)[1], DPLUS.cost(b, world)))

def reachable(agent, world, n=None, b=None, used=frozenset()):
    "Every (b, used, n) the agent's own play reaches, with its decision."
    n = world["N"] if n is None else n; b = world["prior"] if b is None else b
    a, how, paid = agent.step(b, world, n, used); out = [(b, used, n, a, how)]
    if a in world["T"]: return out
    spec = world["O"][a]
    for o, po in REF.push(b, spec["K"]).items():
        if po == 0 or o in spec["ends"]: continue
        out += reachable(agent, world, n - 1, REF.condition(b, spec["K"], o), used | {a})
    return out

class FixedDepth(DecidePlus):
    "Always plays decide_min(depth, n); never thinks.  depth = d is 'fixed d', depth = dplus 'always d+' (paying)."
    def __init__(self, depth, pay=False): self.depth, self.pay = depth, pay
    def step(self, b, world, n, used=frozenset()):
        a = self.solve(b, world, min(self.depth, n), used)[1]
        if self.pay and "dplus" in world and n > world["d"]: return a, "think", self.cost(b, world)
        return a, "floor", F(0)

def variants(w, **kw): return {**w, **kw}

# ---------------------------------------------------------------- Part 2: checks (True = holds)
def C12(agent, w, rng):
    "V_d <= V_m <= cap for d <= m <= n at every reachable node; theta never executed when n <= d."
    for b, used, n, a, how in reachable(agent, w):
        vd = REF.solve(b, w, min(w["d"], n), used)[0]; cp = DPLUS.cap(b, w, used)
        if any(not (vd <= REF.solve(b, w, m, used)[0] <= cp) for m in range(min(w["d"], n), n + 1)): return False
        if how == "think" and n <= w["d"]: return False
    return True
def _same(agent, w1, w2):
    return [(a, h) for *_, a, h in reachable(agent, w1)] == [(a, h) for *_, a, h in reachable(agent, w2)]
def _scaled(w, a, c, h=None):
    h = h or {s: F(0) for s in w["prior"]}
    T = {t: {s: a * v + c + h[s] for s, v in u.items()} for t, u in w["T"].items()}
    O = {k: {**sp, "price": a * sp["price"], "ends": {o: {s: a * v + c + h[s] for s, v in ue.items()} for o, ue in sp["ends"].items()}}
         for k, sp in w["O"].items()}
    w2 = variants(w, T=T, O=O)
    if "dplus" in w: w2["rate"] = a * w["rate"]
    return w2
def C13(agent, w, rng): "gauge: u -> 3u - 7, price and rate x3"; return _same(agent, w, _scaled(w, F(3), F(-7)))
def C14(agent, w, rng):
    "sure-thing: add h(w) to every utility"
    return _same(agent, w, _scaled(w, F(1), F(0), {s: F(i * 5 - 3, 2) for i, s in enumerate(w["prior"])}))
def C15(agent, w, rng):
    "cost dominance: f = 0, or the cheapest thought dearer than the widest utility gap, means theta is never executed"
    if "dplus" not in w: return True
    rng_u = max(all_utils(w)) - min(all_utils(w)); mn = min(w["ops"].values())
    ws = [variants(w, fraction=F(0))] + ([variants(w, rate=rng_u / mn + 1)] if mn > 0 else [])
    return not any(how == "think" for w2 in ws for *_, how in reachable(agent, w2))
def C16(agent, w, rng):
    "free thought: r = 0, f = 1: theta executed exactly where the gain bound is positive"
    if "dplus" not in w: return True
    w2 = variants(w, fraction=F(1), rate=F(0))
    for b, used, n, a, how in reachable(agent, w2):
        g = DPLUS.gain_bound(b, w2, n, REF.solve(b, w2, min(w2["d"], n), used)[0], used)
        if (g > 0) != (how == "think"): return False
    return True
def C17(agent, w, rng):
    "bought is played: having thought, the act is decide_min(d+,n)'s"
    return all(a == REF.solve(b, w, min(w["dplus"], n), used)[1] for b, used, n, a, how in reachable(agent, w) if how == "think")
def C19(agent, w, rng):
    """the cap is not deliberation: it reads no d+ and no value above depth d.  Tested by varying d+ on the dict --
    a dict with d+ = N is not a lawful v0.1 World (J11, refused DEPTH_PLUS); it is a probe of the function."""
    if "dplus" not in w or w["N"] < 3: return True
    hows = {agent.step(w["prior"], variants(w, dplus=dp), w["N"])[1] for dp in (2, w["N"])}
    return len(hows) == 1 and DPLUS.cap(w["prior"], w) == DPLUS.cap(w["prior"], variants(w, dplus=w["N"]))
def C20(agent, w, rng):
    "monotone price AT A NODE: at every node the reference reaches, raising r never turns a non-think into a think (attack 1, 2c: over an episode the count can rise)"
    if "dplus" not in w: return True
    for b, used, n, a, how in reachable(DPLUS, w):
        prev = None
        for k in (0, 1, 2, 4, 8, 16):
            t = agent.step(b, variants(w, rate=(w["rate"] * k if w["rate"] else F(k, 100))), n, used)[1] == "think"
            if prev is not None and t and not prev: return False
            prev = t
    return True
def C9a(agent, w, rng):
    "v0 C9a stands under theta: a terminal act better in every state than every other utility is played at once, no thought bought"
    for t, u in w["T"].items():
        others = [x for t2, u2 in w["T"].items() if t2 != t for x in u2.values()] + [x for sp in w["O"].values() for ue in sp["ends"].values() for x in ue.values()]
        if others and min(u.values()) > max(others):
            return agent.step(w["prior"], w, w["N"])[:2] == (t, "struck_cap" if "dplus" in w else "floor")
    return True
def C10(agent, w, rng):
    "v0 C10 stands under theta: if some Q_1(k) > V_0 the act played is not terminal, thought or not"
    b = w["prior"]; v0 = REF.solve(b, w, 0)[0]
    if w["N"] >= 1 and any(REF.q(b, w, k, 1) > v0 for k in w["O"]):
        return agent.decide(b, w, w["N"]) not in w["T"]
    return True
def E2(agent, w, rng):
    "the differential: the agent's act and think decision are the reference's at every node it reaches, and its value"
    for b, used, n, a, how in reachable(agent, w):
        if (a, how) != DPLUS.step(b, w, n, used)[:2]: return False
    return value_net(agent, w) == value_net(DPLUS, w)
CHECKS = [("C12", C12), ("C13", C13), ("C14", C14), ("C15", C15), ("C16", C16), ("C17", C17), ("C19", C19), ("C20", C20), ("C9a", C9a), ("C10", C10), ("E2", E2)]

# ---------------------------------------------------------------- random worlds
def rand_meta_world(rng):
    """spec_check's random World (E x Z, two acts, sometimes an ending outcome) with N in {2,3}, d = 1, d+ mostly 2,
    f from {0, 1, u[0,1]}, ops ~ s^2, and r drawn so r*ops(|Omega|) is between 0 and 1 (r = 0 one time in five)."""
    w = rand_world(rng); S = len(w["prior"])
    N = rng.choice([2, 3]); ops = {s: F(rng.randint(1, 10) * s * s) for s in range(1, S + 1)}
    return {**w, "N": N, "d": 1, "dplus": 2,
            "fraction": rng.choice([F(0), F(1), F(rng.randint(0, 8), 8), F(rng.randint(0, 8), 8)]),
            "rate": F(0) if rng.random() < 0.2 else F(rng.randint(1, 12), 12) / ops[S], "ops": ops}

def forced(w):
    "a World on which depth d+ changes an act somewhere the floor policy reaches"
    return any(n > w["d"] and REF.solve(b, w, min(w["dplus"], n), used)[1] != a
               for b, used, n, a, how in reachable(FixedDepth(w["d"]), w))

# ---------------------------------------------------------------- Part 3: poisons
class WithCap(DecidePlus):
    "the page's rule with a different cap"
    def __init__(self, name, capfn): self.name, self.capfn = name, capfn
    def cap(self, b, world, used=frozenset()): return self.capfn(self, b, world, used)

def cap_root_posterior(self, b, world, used):
    "the other draft 1's cap (2026-09-21): ending branches valued at the root posterior.  NOT a bound (FIXED_CAP)."
    M = self.menu(world, used); v0 = self.solve(b, world, 0, used)[0]
    if not M: return v0
    perfect = sum(p * max(u[w] for u in world["T"].values()) for w, p in b.items() if p > 0)
    ends = [REF.expect(REF.condition(b, world["O"][k]["K"], o), ue) for k in M for o, ue in world["O"][k]["ends"].items()
            if REF.push(b, world["O"][k]["K"]).get(o, F(0)) > 0]
    return max([v0, perfect - min(world["O"][k]["price"] for k in M)] + ends)

class Peek(DecidePlus):
    name = "peeks: consults V_d+ before paying, thinks iff the act would change (S9)"
    def step(self, b, world, n, used=frozenset()):
        vd, ad = self.solve(b, world, min(world["d"], n), used)
        if "dplus" not in world or n <= world["d"]: return ad, "floor", F(0)
        ap = self.solve(b, world, min(world["dplus"], n), used)[1]
        return (ap, "think", self.cost(b, world)) if ap != ad else (ad, "refused", F(0))
class NoBounds(DecidePlus):
    name = "applies f to the utility range, not the proven gap (S6/S7)"
    def gain_bound(self, b, world, n, vd, used):
        if n <= world["d"]: return F(0)
        return max(all_utils(world)) - min(all_utils(world))
class Myopic(DecidePlus):
    name = "skips the floor: think decision from V_0, plays decide_0 otherwise"
    def step(self, b, world, n, used=frozenset()):
        v0, a0 = self.solve(b, world, 0, used)
        if "dplus" not in world or n <= world["d"]: return self.solve(b, world, min(world["d"], n), used)[1], "floor", F(0)
        g = self.cap(b, world, used) - v0; c = self.cost(b, world)
        if g > c and v0 + world["fraction"] * g - c > v0: return self.solve(b, world, min(world["dplus"], n), used)[1], "think", c
        return a0, "refused", F(0)
class IgnoresResult(DecidePlus):
    name = "pays for the thought, plays the shallow act anyway (C17)"
    def step(self, b, world, n, used=frozenset()):
        a, how, paid = DecidePlus.step(self, b, world, n, used)
        return (self.solve(b, world, min(world["d"], n), used)[1], how, paid) if how == "think" else (a, how, paid)
class RealisedCost(DecidePlus):
    name = "decides on a cost the pack did not declare (a measured count, here 3 x ops) (J13)"
    def cost(self, b, world): return 3 * world["rate"] * world["ops"][live(b)]
class ThinkFirst(DecidePlus):
    name = "theta before O in the menu: a tie buys the thought (J14)"
    def step(self, b, world, n, used=frozenset()):
        vd, ad = self.solve(b, world, min(world["d"], n), used)
        if "dplus" not in world: return ad, "floor", F(0)
        g = self.gain_bound(b, world, n, vd, used); c = self.cost(b, world)
        if g <= c: return ad, "struck_cap", F(0)
        if vd + world["fraction"] * g - c >= vd: return self.solve(b, world, min(world["dplus"], n), used)[1], "think", c
        return ad, "refused", F(0)
class ForgetsN(DecidePlus):
    name = "gain bound cap - V_d even when n <= d (thinks for nothing)"
    def vacuous(self, n, world, used): return False
    def gain_bound(self, b, world, n, vd, used): return self.cap(b, world, used) - vd
class Clock(DecidePlus):
    name = "cost from a clock: a stand-in that reads nothing declared (E6)"
    def cost(self, b, world): return F(len(self.menu(world, frozenset())) + len(world["T"]), 10)
class LowerCap(DecidePlus):
    name = "uses V_0, a lower bound, where an upper bound is required (C12)"
    def cap(self, b, world, used=frozenset()): return self.solve(b, world, 0, used)[0]
class ThinksTwice(DecidePlus):
    name = "after buying d+, buys d+ + 1 too (J11)"
    def step(self, b, world, n, used=frozenset()):
        a, how, paid = DecidePlus.step(self, b, world, n, used)
        if how == "think" and n > world["dplus"]: return self.solve(b, world, min(world["dplus"] + 1, n), used)[1], "think", 2 * paid
        return a, how, paid
class FreeThought(DecidePlus):
    name = "never charges the thought in the value (J15)"
    def step(self, b, world, n, used=frozenset()): a, how, _ = DecidePlus.step(self, b, world, n, used); return a, how, F(0)
class Schedule(DecidePlus):
    name = "thinks when more than two states are live: a rule, not a price"
    def step(self, b, world, n, used=frozenset()):
        ad = self.solve(b, world, min(world["d"], n), used)[1]
        if "dplus" not in world or n <= world["d"]: return ad, "floor", F(0)
        return (self.solve(b, world, min(world["dplus"], n), used)[1], "think", self.cost(b, world)) if live(b) > 2 else (ad, "refused", F(0))

POISONS = [WithCap("the other draft 1's cap: ending branches at the root posterior", cap_root_posterior),
           WithCap("computes the cap by searching to d+ (deliberation about deliberation)",
                   lambda self, b, w, used: self.solve(b, w, min(w["dplus"], w["N"]), used)[0]),
           Schedule(), FixedDepth(2, pay=True), FixedDepth(1), Peek(), NoBounds(), Myopic(), IgnoresResult(),
           RealisedCost(), ThinkFirst(), ForgetsN(), Clock(), LowerCap(), ThinksTwice(), FreeThought()]
for _p, _n in ((POISONS[3], "always thinks (ignores the price)"), (POISONS[4], "never thinks")): _p.name = _n

# ---------------------------------------------------------------- Part 4: frozen vectors and fixed worlds
def act(K, price, once, ends=None): return {"K": K, "price": price, "once": once, "ends": ends or {}}
APPX_T = {"treat": {"sick": F(0), "well": F(-2)}, "leave": {"sick": F(-10), "well": F(0)}}
APPX_K = {"sick": {"+": F(9, 10), "-": F(1, 10)}, "well": {"+": F(1, 5), "-": F(4, 5)}}
SCAN_K = {"sick": {"y": F(9, 10), "n": F(1, 10)}, "well": {"y": F(2, 5), "n": F(3, 5)}}
META = {"N": 2, "d": 1, "dplus": 2, "fraction": F(1, 2), "rate": F(1, 1000), "ops": {1: F(100), 2: F(200)}}

def vector_A():
    "appendix A: the thought that changes nothing.  One `fresh` test."
    return {"prior": {"sick": F(1, 5), "well": F(4, 5)}, "T": APPX_T, "O": {"test": act(APPX_K, F(1, 2), False)}, **META}
def vector_B():
    "appendix B (from the other draft 1): the thought that changes the act.  `test` and `scan`, both once."
    return {"prior": {"sick": F(1, 5), "well": F(4, 5)}, "T": APPX_T,
            "O": {"test": act(APPX_K, F(1, 2), True), "scan": act(SCAN_K, F(1, 5), True)}, **META}
def world_FIXED_CAP():
    """finding on the other draft 1 (2026-09-21), reproduced against its own Ref: a cap that values ending branches
    at the root posterior is below V_N.  Omega = {A,B}; `reveal` once, 1/100, tells omega; `lottery` fresh, free,
    ending outcome o worth 100 in A and 0 in B, K(o|A) = 1/10, K(o|B) = 9/10.  N = 5."""
    return {"prior": {"A": F(1, 2), "B": F(1, 2)}, "T": {"t0": {"A": F(0), "B": F(0)}},
            "O": {"reveal": act({"A": {"a": F(1)}, "B": {"b": F(1)}}, F(1, 100), True),
                  "lottery": act({"A": {"o": F(1, 10), "x": F(9, 10)}, "B": {"o": F(9, 10), "x": F(1, 10)}}, F(0), False,
                                 {"o": {"A": F(100), "B": F(0)}})},
            "N": 5, "d": 1, "dplus": 2, "fraction": F(1, 2), "rate": F(0), "ops": {1: F(1), 2: F(1)}}

def expected_thoughts(agent, w, n=None, b=None, used=frozenset()):
    n = w["N"] if n is None else n; b = w["prior"] if b is None else b
    a, how, paid = agent.step(b, w, n, used); e = F(1 if how == "think" else 0)
    if a in w["T"]: return e
    sp = w["O"][a]
    for o, po in REF.push(b, sp["K"]).items():
        if po == 0 or o in sp["ends"]: continue
        e += po * expected_thoughts(agent, w, n - 1, REF.condition(b, sp["K"], o), used | {a})
    return e

def fixed_worlds():
    "Every World the page's appendix and the attack sessions pinned, by name.  The kit runs E2 on all of them."
    coin = {"prior": {"A": F(1, 2), "B": F(1, 2)},
            "T": {"pass": {"A": F(0), "B": F(0)}, "guessA": {"A": F(1), "B": F(-5)}, "guessB": {"A": F(-5), "B": F(1)}},
            "O": {"test": act({"A": {"+": F(2, 3), "-": F(1, 3)}, "B": {"+": F(1, 3), "-": F(2, 3)}}, F(1, 25), False)},
            "N": 3, "d": 1, "dplus": 2, "fraction": F(1, 2), "rate": F(1, 1000), "ops": {1: F(10), 2: F(10)}}
    S3 = ["1", "2", "3"]
    c20 = {"prior": {"1": F(1, 10), "2": F(9, 20), "3": F(9, 20)}, "T": {f"t{i}": {s: F(1 if s == i else 0) for s in S3} for i in S3},
           "O": {"Y": act({s: {"o": F(2, 3), "r" + s: F(1, 3)} for s in S3}, F(1, 20), True),
                 "W": act({s: {"o": F(9, 10), "r" + s: F(1, 10)} for s in S3}, F(1, 400), True),
                 "Z": act({"1": {"z1": F(1)}, "2": {"z2": F(1)}, "3": {"z2": F(1)}}, F(1, 200), True)},
           "N": 4, "d": 1, "dplus": 2, "fraction": F(1), "rate": F(11, 25), "ops": {1: F(1), 2: F(100), 3: F(1)}}
    noop = vector_A(); noop["O"] = {"noop": act({"sick": {"z": F(1)}, "well": {"z": F(1)}}, F(0), True), **noop["O"]}
    return {"A": vector_A(), "B": vector_B(), "A_N3": variants(vector_A(), N=3), "FIXED_CAP": world_FIXED_CAP(),
            "S1-2B": {"prior": {"A": F(1, 2), "B": F(1, 2)}, "T": {"a": {"A": F(1), "B": F(0)}, "b": {"A": F(0), "B": F(1)}},
                      "O": {"k": act({"A": {"x": F(1, 2), "y": F(1, 2)}, "B": {"x": F(1, 2), "y": F(1, 2)}}, F(0), False)},
                      "N": 2, "d": 1, "dplus": 2, "fraction": F(1), "rate": F(1, 4), "ops": {1: F(1), 2: F(1)}},
            "S1-2C": c20, "S1-2C-lo": variants(c20, rate=F(1, 25)), "COIN-d2": coin, "NOOP": noop,
            "A-split": {"prior": {"sick": F(1, 5), "well1": F(2, 5), "well2": F(2, 5)},
                        "T": {"treat": {"sick": F(0), "well1": F(-2), "well2": F(-2)}, "leave": {"sick": F(-10), "well1": F(0), "well2": F(0)}},
                        "O": {"test": act({"sick": APPX_K["sick"], "well1": APPX_K["well"], "well2": APPX_K["well"]}, F(1, 2), False)},
                        "N": 2, "d": 1, "dplus": 2, "fraction": F(1, 2), "rate": F(1, 1000), "ops": {1: F(100), 2: F(200), 3: F(600)}}}

def attack_findings():
    "Attack session 1 on draft 3 (2026-09-21): every reproduced finding as a World.  Returns lines."
    L = []
    # 1a  two readings: theta inside v0's max at depth d+.  Reading B leaves the step with no act.
    w = vector_A(); b = w["prior"]
    qt = REF.solve(b, w, 1)[0] + w["fraction"] * F(13, 25) - F(1, 5)
    assert qt == F(-24, 25) > REF.solve(b, w, 2)[0] == F(-51, 50)
    L.append("  s1 1a  Q(theta) = -24/25 > V_2 = -51/50: theta would attain the depth-d+ max; page now says theta is not in the M handed to v0 section 2")
    # 2a  C8 fails for the adaptive policy: Appendix A at N = 3 buys a second empty thought at b|+.
    vals = {N: value_net(DPLUS, variants(vector_A(), N=N)) for N in (2, 3, 4)}
    assert vals == {2: F(-61, 50), 3: F(-161, 125), 4: F(-161, 125)}
    w = variants(vector_A(), N=3); bp = REF.condition(b, w["O"]["test"]["K"], "+")
    assert DPLUS.step(bp, w, 2) == ("treat", "think", F(1, 5))
    assert all(value_net(FixedDepth(1), variants(vector_A(), N=N)) == F(-51, 50) for N in (2, 3, 4))
    L.append("  s1 2a  C8: adaptive value -61/50 at N=2, -161/125 at N=3 (b|+ thinks again, returns treat); fixed d unchanged.  Conceded: C8 is exempted for the adaptive policy")
    # 2b  C5 fails: a free uninformative act raises the cap, the agent buys a useless thought.
    def kw(p): return {"prior": {"A": F(1, 2), "B": F(1, 2)}, "T": {"a": {"A": F(1), "B": F(0)}, "b": {"A": F(0), "B": F(1)}},
                       "O": {"k": act({"A": {"x": F(1, 2), "y": F(1, 2)}, "B": {"x": F(1, 2), "y": F(1, 2)}}, p, False)},
                       "N": 2, "d": 1, "dplus": 2, "fraction": F(1), "rate": F(1, 4), "ops": {1: F(1), 2: F(1)}}
    assert DPLUS.step(kw(F(1, 2))["prior"], kw(F(1, 2)), 2)[:2] == ("a", "struck_cap") and value_net(DPLUS, kw(F(1, 2))) == F(1, 2)
    assert DPLUS.step(kw(F(0))["prior"], kw(F(0)), 2)[:2] == ("a", "think") and value_net(DPLUS, kw(F(0))) == F(1, 4) < F(1, 2)
    L.append("  s1 2b  C5: making k free: value 1/2 -> 1/4 < V_0 = 1/2.  Conceded: C5 is exempted for the adaptive policy")
    # 2c  C20 per episode: raising r moves the agent onto a branch where it thinks twice.
    S3 = ["1", "2", "3"]; T3 = {f"t{i}": {s: F(1 if s == i else 0) for s in S3} for i in S3}
    O3 = {"Y": act({s: {"o": F(2, 3), "r" + s: F(1, 3)} for s in S3}, F(1, 20), True),
          "W": act({s: {"o": F(9, 10), "r" + s: F(1, 10)} for s in S3}, F(1, 400), True),
          "Z": act({"1": {"z1": F(1)}, "2": {"z2": F(1)}, "3": {"z2": F(1)}}, F(1, 200), True)}
    def c20(r): return {"prior": {"1": F(1, 10), "2": F(9, 20), "3": F(9, 20)}, "T": T3, "O": O3, "N": 4, "d": 1, "dplus": 2,
                        "fraction": F(1), "rate": r, "ops": {1: F(1), 2: F(100), 3: F(1)}}
    lo, hi = c20(F(1, 25)), c20(F(11, 25))
    assert DPLUS.step(lo["prior"], lo, 4)[:2] == ("Z", "think") and expected_thoughts(DPLUS, lo) == F(1) and value_net(DPLUS, lo) == F(1277, 2000)
    assert DPLUS.step(hi["prior"], hi, 4)[:2] == ("Y", "struck_cap") and expected_thoughts(DPLUS, hi) == F(19, 15) and value_net(DPLUS, hi) == F(59, 500)
    assert C20(DPLUS, lo, None) and C20(DPLUS, hi, None)          # per node it holds
    L.append("  s1 2c  C20: r 1/25 -> 11/25 raises E[#theta] 1 -> 19/15.  C20 restated at a node, where it holds")
    # 4a  notation: V_{d+} means V_min(d+,n); at n = 1 the literal V_2 exceeds V_1 while ghat = 0.
    w = variants(vector_B(), fraction=F(0)); w["O"] = {k: {**sp, "once": False} for k, sp in w["O"].items()}
    bp = REF.condition(w["prior"], w["O"]["test"]["K"], "+")
    assert DPLUS.gain_bound(bp, w, 1, REF.solve(bp, w, 1)[0], frozenset()) == 0 and REF.solve(bp, w, 2)[0] == F(-91, 100) > F(-16, 17)
    L.append("  s1 4a  literal V_2(b|+) = -91/100 > V_1 = -16/17 at n = 1 while ghat = 0: the Throughout line now covers d+")
    # 6.5  C15's range must include u_end.
    w = {"prior": {"A": F(1, 2), "B": F(1, 2)}, "T": {"t": {"A": F(0), "B": F(0)}},
         "O": {"k": act({"A": {"e": F(1, 2), "x": F(1, 2)}, "B": {"e": F(1, 2), "x": F(1, 2)}}, F(0), False, {"e": {"A": F(10), "B": F(10)}})},
         "N": 2, "d": 1, "dplus": 2, "fraction": F(1), "rate": F(1), "ops": {1: F(1), 2: F(1)}}
    assert DPLUS.step(w["prior"], w, 2)[:2] == ("k", "think") and DPLUS.cap(w["prior"], w) == 10
    L.append("  s1 6.5 C15 read over terminal u only is false (theta executed with r*min ops = 1 >= 0); page says u and u_end")
    # ---- attack session 2 on draft 4 (2026-09-21)
    # 1.1  two readings of d+: a pack with (d, d+) != (1, 2) -- refused by name DEPTH_PLUS (J11).  Under the other
    #      reading it would run; COIN shows what it would do, so the refusal is act-changing and the name is needed.
    coin = {"prior": {"A": F(1, 2), "B": F(1, 2)},
            "T": {"pass": {"A": F(0), "B": F(0)}, "guessA": {"A": F(1), "B": F(-5)}, "guessB": {"A": F(-5), "B": F(1)}},
            "O": {"test": act({"A": {"+": F(2, 3), "-": F(1, 3)}, "B": {"+": F(1, 3), "-": F(2, 3)}}, F(1, 25), False)},
            "N": 3, "d": 1, "dplus": 3, "fraction": F(1, 2), "rate": F(1, 1000), "ops": {1: F(10), 2: F(10)}}
    try: refuse_meta(coin); assert False
    except Refused as e: assert str(e) == "DEPTH_PLUS"
    assert DPLUS.step(coin["prior"], coin, 3) == ("test", "think", F(1, 100)) and value_net(DPLUS, coin) == F(-1, 90)
    assert value_net(DPLUS, variants(coin, dplus=2)) == F(-1, 100)
    L.append("  s2 1.1 COIN with d+ = 3: refused DEPTH_PLUS; had it run, theta buys test for -1/90 (d+ = 2 buys pass for -1/100)")
    # 5   the unit is representation-dependent: Appendix A with `well` written twice pays ops(3) and is struck.
    Ap = {"prior": {"sick": F(1, 5), "well1": F(2, 5), "well2": F(2, 5)},
          "T": {"treat": {"sick": F(0), "well1": F(-2), "well2": F(-2)}, "leave": {"sick": F(-10), "well1": F(0), "well2": F(0)}},
          "O": {"test": act({"sick": APPX_K["sick"], "well1": APPX_K["well"], "well2": APPX_K["well"]}, F(1, 2), False)},
          "N": 2, "d": 1, "dplus": 2, "fraction": F(1, 2), "rate": F(1, 1000), "ops": {1: F(100), 2: F(200), 3: F(600)}}
    assert DPLUS.step(Ap["prior"], Ap, 2)[:2] == ("test", "struck_cap") and value_net(DPLUS, Ap) == F(-51, 50)
    L.append("  s2 5   A with `well` split in two: same V, cap, ghat; s = 3, c = 3/5 > 13/25, struck.  Named as a residue: the unit counts rows")
    # confirmation: "returns 0" is not "changes nothing" -- a free noop first in O is decide_2 by J3.
    w = vector_A(); w["O"] = {"noop": act({"sick": {"z": F(1)}, "well": {"z": F(1)}}, F(0), True), **w["O"]}
    assert REF.solve(w["prior"], w, 2) == (F(-51, 50), "noop") and DPLUS.step(w["prior"], w, 2) == ("noop", "think", F(1, 5))
    L.append("  s2 c   noop first in O: V_2 = V_1 yet a+ = noop != test (J3); C18's gap opens at result 0")
    # 3   agent Lambda (eager, counter-booked) is indistinguishable by construction: nothing to pin; the page's
    #     claim that E6 witnesses it is withdrawn.
    return L

def frozen(verbose):
    lines = []
    # A
    w = vector_A(); b = w["prior"]
    v1, a1 = REF.solve(b, w, 1); v2, a2 = REF.solve(b, w, 2); cp = DPLUS.cap(b, w); g = DPLUS.gain_bound(b, w, 2, v1, frozenset())
    assert (v1, a1, v2, a2) == (F(-51, 50), "test", F(-51, 50), "test")
    assert cp == F(-1, 2) and g == F(13, 25) and DPLUS.cost(b, w) == F(1, 5)
    assert DPLUS.step(b, w, 2) == ("test", "think", F(1, 5))
    assert DPLUS.step(b, variants(w, rate=F(1, 100)), 2)[1] == "struck_cap"
    assert DPLUS.step(b, variants(w, fraction=F(0)), 2)[1] == "refused"
    assert DPLUS.step(b, variants(w, fraction=F(1), rate=F(0)), 2)[1] == "think"
    st = {}; fixed = value_net(FixedDepth(1), w); adaptive = value_net(DPLUS, w, stats=st); om = omniscient_value(w)
    assert fixed == F(-51, 50) and adaptive == F(-61, 50) and om == fixed and st == {"think": 1, "struck_n": 2}
    lines.append(f"  A: V_1 = {v1} ({a1}), V_2 = {v2} ({a2}), cap = {cp}, gain bound = {g}, c = 1/5: thinks, plays {a2}, gains 0")
    lines.append(f"     fixed-d {fixed}, adaptive {adaptive}, omniscient {om}; steps {st}")
    # B
    w = vector_B(); b = w["prior"]
    v1, a1 = REF.solve(b, w, 1); v2, a2 = REF.solve(b, w, 2); cp = DPLUS.cap(b, w); g = DPLUS.gain_bound(b, w, 2, v1, frozenset())
    assert (v1, a1, v2, a2) == (F(-51, 50), "test", F(-479, 500), "scan") and cp == F(-1, 5) and g == F(41, 50)
    assert DPLUS.step(b, w, 2) == ("scan", "think", F(1, 5))
    assert DPLUS.step(b, variants(w, rate=F(1, 400)), 2)[:2] == ("test", "refused")
    assert DPLUS.step(b, variants(w, rate=F(1, 200)), 2)[:2] == ("test", "struck_cap")
    fixed = value_net(FixedDepth(1), w); adaptive = value_net(DPLUS, w); om = omniscient_value(w)
    assert fixed == v1 and adaptive == v2 - F(1, 5) and om == fixed and v2 - v1 == F(31, 500)
    lines.append(f"  B: V_1 = {v1} ({a1}), V_2 = {v2} ({a2}), cap = {cp}, gain bound = {g}, c = 1/5: thinks, plays {a2}")
    lines.append(f"     true gain {v2 - v1} < cost 1/5: fixed-d {fixed}, adaptive {adaptive}, omniscient {om} (does not think)")
    # FIXED_CAP
    w = world_FIXED_CAP(); b = w["prior"]
    bad = cap_root_posterior(DPLUS, b, w, frozenset()); good = DPLUS.cap(b, w); vN = REF.solve(b, w, 5)[0]
    assert bad == F(10) and vN == F(40951, 2000) and bad < vN <= good
    lines.append(f"  FIXED_CAP: root-posterior cap {bad} < V_5 {vN} <= page cap {good}")
    # v0 Worlds: decide+ is the floor
    rng = random.Random(7)
    for _ in range(100):
        w = {**rand_world(rng), "N": 3, "d": 1}; b = w["prior"]
        assert DPLUS.decide(b, w, 3) == Rolling(1).decide(b, w, 3) and DPLUS.step(b, w, 3)[1] == "floor"
    lines.append("  v0 Worlds (no theta): decide+ = Rolling(1) on 100 random Worlds, every step 'floor'")
    for bad_w, name in ((variants(vector_A(), fraction=F(3, 2)), "FRACTION"), (variants(vector_A(), ops={2: F(1)}), "COST"),
                        (variants(vector_A(), dplus=1), "DEPTH_PLUS")):
        try: refuse_meta(bad_w); assert False
        except Refused as e: assert str(e) == name
    lines.append("  refusals: FRACTION, COST, DEPTH_PLUS by name")
    return lines

def run(agent, worlds):
    fails = {c: 0 for c, _ in CHECKS}
    for i, w in enumerate(worlds):
        for cname, check in CHECKS:
            try: good = check(agent, w, random.Random(1000 + i))
            except Exception: good = False
            if not good: fails[cname] += 1
    return fails

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=20260921); ap.add_argument("--worlds", type=int, default=120)
    ap.add_argument("--verbose", action="store_true"); args = ap.parse_args()
    rng = random.Random(args.seed)
    worlds = [rand_meta_world(rng) for _ in range(args.worlds // 2)]; draws = 0
    while len(worlds) < args.worlds and draws < 50000:
        draws += 1; w = rand_meta_world(rng)
        if forced(w): worlds.append(w)
    for w in worlds: refuse_meta(w)
    print(f"{args.worlds // 2} random Worlds + {len(worlds) - args.worlds // 2} forced (d+ changes an act; {draws} draws). Cells = worlds on which the check FAILS.\n")
    names = [c for c, _ in CHECKS]; ok = True
    row = lambda nm, f: f"{nm[:64]:64s}" + "".join(f"{f[c]:5d}" for c in names)
    print(f"{'agent':64s}" + "".join(f"{c:>5s}" for c in names))
    ref = run(DPLUS, worlds); print(row(DPLUS.name, ref))
    if any(ref.values()): ok = False; print("  ^^ THE PAGE IS WRONG: the reference violates its own consequences")
    print()
    for p in POISONS:
        f = run(p, worlds); by_c = [c for c in names if c != "E2" and f[c] > 0]
        mark = "" if by_c else ("   <-- E2 only" if f["E2"] else "   <-- SURVIVES EVERYTHING")
        print(row(p.name, f) + mark)
        if not by_c and not f["E2"]: ok = False
    st = {}; changed = thought = 0; reg = {"fixed d": F(0), "always d+": F(0), "adaptive": F(0)}; opt = 0
    for w in worlds:
        for b, used, n, a, how in reachable(DPLUS, w):
            st[how] = st.get(how, 0) + 1
            if how == "think": thought += 1; changed += a != REF.solve(b, w, min(w["d"], n), used)[1]
        om = omniscient_value(w); va = value_net(DPLUS, w)
        reg["fixed d"] += om - value_net(FixedDepth(1), w); reg["always d+"] += om - value_net(FixedDepth(w["dplus"], True), w); reg["adaptive"] += om - va
        opt += va == om
    print(f"\nsteps settled {dict(sorted(st.items()))}; think acts that changed the act {changed}/{thought}")
    print("E3 mean regret vs the omniscient meta-policy: " + ", ".join(f"{k} {float(v / len(worlds)):.4f}" for k, v in reg.items())
          + f"; adaptive optimal on {opt}/{len(worlds)}")
    print("\nfrozen vectors and fixed worlds:")
    for l in frozen(args.verbose): print(l)
    print("\nattack findings, reproduced:")
    for l in attack_findings(): print(l)
    print("\nPAGE PASSES" if ok else "\nPAGE FAILS"); sys.exit(0 if ok else 1)
