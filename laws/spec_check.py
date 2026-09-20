"""
spec_check.py - tests the PAGE (CHARTER.md), not any implementation.

Part 1  the reference semantics of CHARTER section 2, in ~60 lines over Fractions.
Part 2  the consequences C1-C9 and rule S5 as black-box checks on any agent.
Part 3  poison agents: each one is a bug class a coding agent really writes
        (several are from the hkaddresses audit of 2026-09-20).
Part 4  the kill matrix. The page passes when
          (a) the reference agent passes every check on every world, and
          (b) every poison is killed by at least one check that does NOT consult the reference.
        A poison that only the differential check E2 can kill means section 4 is missing a consequence.

Run:  python3 laws/spec_check.py        (exit code 0 = page passes)
"""
from fractions import Fraction as F
import random, sys

class WorldFalsified(Exception): pass

# ---------------------------------------------------------------- Part 1: reference
class Ref:
    name = "reference"
    def expect(self, b, f):            return sum(p * f[w] for w, p in b.items())
    def push(self, b, K):
        out = {}
        for w, p in b.items():
            for o, q in K[w].items(): out[o] = out.get(o, F(0)) + p * q
        return out
    def condition(self, b, K, o):
        z = sum(p * K[w].get(o, F(0)) for w, p in b.items())
        if z == 0: raise WorldFalsified(o)
        return {w: p * K[w].get(o, F(0)) / z for w, p in b.items()}
    def price(self, spec):             return spec["price"]
    def solve(self, b, world, n, used=frozenset()):
        """(V_n, first menu entry attaining it). Menu order: terminal acts, then observational."""
        best, arg = None, None
        for t, u in world["T"].items():
            v = self.expect(b, u)
            if best is None or v > best: best, arg = v, t
        if n > 0:
            for k, spec in world["O"].items():
                if spec["once"] and k in used: continue
                q = -self.price(spec)
                for o, po in self.push(b, spec["K"]).items():
                    if po == 0: continue
                    bo = self.condition(b, spec["K"], o)
                    if o in spec["ends"]: q += po * self.expect(bo, spec["ends"][o])
                    else:                 q += po * self.solve(bo, world, n - 1, used | {k})[0]
                if q > best: best, arg = q, k
        return best, arg
    def decide(self, b, world, n, used=frozenset()): return self.solve(b, world, n, used)[1]

REF = Ref()

def policy_value(agent, world, n, bt=None, ba=None, used=frozenset()):
    """Exact expected utility of the agent's policy under the declared model.
    bt = true posterior (reference), ba = the agent's own belief (may be wrong)."""
    bt = world["prior"] if bt is None else bt
    ba = world["prior"] if ba is None else ba
    a = agent.decide(ba, world, n, used)
    if a in world["T"]: return REF.expect(bt, world["T"][a])
    spec = world["O"][a]; v = -spec["price"]
    for o, po in REF.push(bt, spec["K"]).items():
        if po == 0: continue
        bto = REF.condition(bt, spec["K"], o)
        if o in spec["ends"]: v += po * REF.expect(bto, spec["ends"][o])
        else: v += po * policy_value(agent, world, n - 1, bto, agent.condition(ba, spec["K"], o), used | {a})
    return v

# ---------------------------------------------------------------- random worlds
def rand_world(rng, ends=True):
    """Omega = E x Z (Z is a nuisance latent: utilities depend on e only)."""
    Es, Zs = range(rng.choice([2, 3])), range(2)
    W = [(e, z) for e in Es for z in Zs]
    raw = [rng.randint(1, 5) for _ in W]; s = sum(raw)
    prior = {w: F(r, s) for w, r in zip(W, raw)}
    def u_e(): 
        ue = {e: F(rng.randint(-9, 3)) for e in Es}
        return {w: ue[w[0]] for w in W}
    T = {f"t{i}": u_e() for i in range(3)}
    O = {}
    for j in range(2):
        K = {}
        for w in W:
            r = [rng.choice([1, 1, 2, 5, 12]) for _ in range(2)]; z = sum(r)
            K[w] = {f"o{i}": F(x, z) for i, x in enumerate(r)}
        O[f"k{j}"] = {"K": K, "price": F(rng.randint(1, 4), 4), "once": rng.random() < 0.7, "ends": {}}
    if ends and rng.random() < 0.4: O["k1"]["ends"] = {"o1": u_e()}
    return {"prior": prior, "T": T, "O": O}

def clone(world, T=None, O=None):
    return {"prior": world["prior"], "T": T or world["T"], "O": O or world["O"]}

def all_utils(world):
    vals = [x for u in world["T"].values() for x in u.values()]
    vals += [x for s in world["O"].values() for ue in s["ends"].values() for x in ue.values()]
    return vals

# ---------------------------------------------------------------- Part 2: checks (True = holds)
N = 2
def C1(agent, world, rng):   # coherence of posterior and of predictive
    for spec in world["O"].values():
        pr = agent.push(world["prior"], spec["K"])
        if sum(pr.values()) != 1 or min(pr.values()) < 0: return False
        for o in pr:
            b = agent.condition(world["prior"], spec["K"], o)
            if sum(b.values()) != 1 or min(b.values()) < 0: return False
    return True
def C2(agent, world, rng):   # order
    k0, k1 = world["O"]["k0"]["K"], world["O"]["k1"]["K"]
    c = agent.condition
    return c(c(world["prior"], k0, "o0"), k1, "o1") == c(c(world["prior"], k1, "o1"), k0, "o0")
def C3(agent, world, rng):   # gauge: u -> a*u + c, price -> a*price
    a, c = F(rng.randint(2, 5)), F(rng.randint(-6, 6))
    T = {t: {w: a * x + c for w, x in u.items()} for t, u in world["T"].items()}
    O = {k: {**s, "price": a * s["price"], "ends": {o: {w: a * x + c for w, x in ue.items()} for o, ue in s["ends"].items()}}
         for k, s in world["O"].items()}
    return agent.decide(world["prior"], clone(world, T, O), N) == agent.decide(world["prior"], world, N)
def C4(agent, world, rng):   # sure-thing: add h(w) to every terminal and ending utility
    h = {w: F(rng.randint(-6, 6)) for w in world["prior"]}
    T = {t: {w: x + h[w] for w, x in u.items()} for t, u in world["T"].items()}
    O = {k: {**s, "ends": {o: {w: x + h[w] for w, x in ue.items()} for o, ue in s["ends"].items()}} for k, s in world["O"].items()}
    return agent.decide(world["prior"], clone(world, T, O), N) == agent.decide(world["prior"], world, N)
def C5(agent, world, rng):   # free information (acts without ending outcomes) never lowers realised value
    pure = {k: {**s, "price": F(0)} for k, s in world["O"].items() if not s["ends"]}
    if not pure: return True
    return policy_value(agent, clone(world, O=pure), N) >= policy_value(agent, clone(world, O=pure), 0)
def C6(agent, world, rng):   # no diachronic book: the price of a called-off bet today = the price after seeing o
    X = {w: F(rng.randint(-5, 5)) for w in world["prior"]}
    for spec in world["O"].values():
        for o in ("o0", "o1"):
            z = sum(p * spec["K"][w][o] for w, p in world["prior"].items())
            today = sum(p * spec["K"][w][o] * X[w] for w, p in world["prior"].items()) / z
            if agent.expect(agent.condition(world["prior"], spec["K"], o), X) != today: return False
    return True
def C7(agent, world, rng):   # self-calibration, exactly: among outcomes where the agent states p for event A, A has frequency p
    e0 = {w: F(1 if w[0] == 0 else 0) for w in world["prior"]}
    for spec in world["O"].values():
        groups = {}
        for o, po in REF.push(world["prior"], spec["K"]).items():
            stated = agent.expect(agent.condition(world["prior"], spec["K"], o), e0)
            joint = sum(p * spec["K"][w][o] * e0[w] for w, p in world["prior"].items())
            g = groups.setdefault(stated, [F(0), F(0)]); g[0] += joint; g[1] += po
        if any(j / tot != stated for stated, (j, tot) in groups.items()): return False
    return True
def C8(agent, world, rng):   # horizon: more allowed observations never lowers realised value
    return policy_value(agent, world, 2) >= policy_value(agent, world, 1) >= policy_value(agent, world, 0)
def C9a(agent, world, rng):  # dominance: a terminal act better than everything in every state is played at once
    top = max(all_utils(world)) + 1
    T = dict(world["T"]); T["t1"] = {w: top for w in world["prior"]}
    return agent.decide(world["prior"], clone(world, T=T), N) == "t1"
def C9b(agent, world, rng):  # an observational act priced above the whole utility range is never chosen
    vals = all_utils(world); over = max(vals) - min(vals) + 1
    O = {k: {**s, "price": over} for k, s in world["O"].items()}
    return agent.decide(world["prior"], clone(world, O=O), N) in world["T"]
def S5(agent, world, rng):   # zero evidence in a closed world is refused by name, never handled
    K = {w: ({"o0": F(1), "o1": F(0)}) for w in world["prior"]}
    try: agent.condition(world["prior"], K, "o1")
    except WorldFalsified: return True
    return False
def E2(agent, world, rng):   # differential: realised value equals the reference optimum (the only check that consults it)
    return policy_value(agent, world, N) == REF.solve(world["prior"], world, N)[0]

CHECKS = [("C1", C1), ("C2", C2), ("C3", C3), ("C4", C4), ("C5", C5), ("C6", C6), ("C7", C7), ("C8", C8),
          ("C9a", C9a), ("C9b", C9b), ("S5", S5), ("E2", E2)]

# ---------------------------------------------------------------- Part 3: poisons
def marg_e(b):
    m = {}
    for (e, z), p in b.items(): m[e] = m.get(e, F(0)) + p
    return m

class Gate80(Ref):
    "audit: a 0.8 confidence gate deciding outside the loss"
    name = "gate: abstain (t0) unless confidence >= 4/5"
    def decide(self, b, world, n, used=frozenset()):
        return "t0" if max(marg_e(b).values()) < F(4, 5) else super().decide(b, world, n, used)
class MaxForSum(Ref):
    "audit: best path kept where the model says sum (Viterbi for marginal)"
    name = "max over the nuisance latent where the model says sum"
    def expect(self, b, f):
        m, rep = {}, {}
        for (e, z), p in b.items():
            if p > m.get(e, F(-1)): m[e] = p
            rep[e] = f[(e, z)]
        s = sum(m.values())
        return sum(m[e] / s * rep[e] for e in m)
class DoubleCount(Ref):
    name = "one observation conditioned on twice"
    def condition(self, b, K, o): return super().condition(super().condition(b, K, o), K, o)
class Dampen(Ref):
    name = "tempered update (likelihood mixed with a constant)"
    def condition(self, b, K, o):
        z = sum(p * (K[w][o] + 1) / 2 for w, p in b.items())
        return {w: p * (K[w][o] + 1) / 2 / z for w, p in b.items()}
class Clip(Ref):
    name = "posterior clipped at 1/2 then renormalised (never be sure)"
    def condition(self, b, K, o):
        c = {w: min(p, F(1, 2)) for w, p in super().condition(b, K, o).items()}; s = sum(c.values())
        return {w: p / s for w, p in c.items()}
class InfoMax(Ref):
    name = "buys the most informative test, ignoring price and stakes"
    def decide(self, b, world, n, used=frozenset()):
        if n > 0 and max(marg_e(b).values()) < F(9, 10):
            best, arg = None, None
            for k, s in world["O"].items():
                if s["once"] and k in used: continue
                g = sum(po * max(marg_e(self.condition(b, s["K"], o)).values()) for o, po in self.push(b, s["K"]).items())
                if best is None or g > best: best, arg = g, k
            if arg: return arg
        return super().decide(b, world, 0, used)
class ZeroBaseline(Ref):
    name = "responds only if expected utility > 0 (hard-coded baseline)"
    def decide(self, b, world, n, used=frozenset()):
        a = super().decide(b, world, n, used)
        return a if (a not in world["T"] or self.expect(b, world["T"][a]) > 0) else "t0"
class IgnorePrice(Ref):
    name = "treats every price as zero"
    def price(self, spec): return F(0)
class SilentZero(Ref):
    name = "zero evidence silently handled (returns the prior)"
    def condition(self, b, K, o):
        try: return super().condition(b, K, o)
        except WorldFalsified: return dict(b)
class LeakyKernelWorld(Ref):
    "audit: the channel is not a proper distribution (A34). A WORLD poison: the agent is the reference."
    name = "world whose kernel rows sum to < 1"
    leaky = True

POISONS = [Gate80(), MaxForSum(), DoubleCount(), Dampen(), Clip(), InfoMax(), ZeroBaseline(), IgnorePrice(), SilentZero(), LeakyKernelWorld()]

def leak(world):
    O = {k: {**s, "K": {w: {o: q * F(9, 10) for o, q in row.items()} for w, row in s["K"].items()}} for k, s in world["O"].items()}
    return clone(world, O=O)

# ---------------------------------------------------------------- Part 4: kill matrix
def run(agent, worlds):
    fails = {c: 0 for c, _ in CHECKS}
    for i, world in enumerate(worlds):
        w = leak(world) if getattr(agent, "leaky", False) else world
        for cname, check in CHECKS:
            try: ok = check(agent, w, random.Random(1000 + i))
            except WorldFalsified: ok = False
            if not ok: fails[cname] += 1
    return fails

if __name__ == "__main__":
    rng = random.Random(20260920)
    worlds = [rand_world(rng) for _ in range(200)]
    names = [c for c, _ in CHECKS]
    print(f"{len(worlds)} random worlds, horizon {N}. Cells = worlds on which the check FAILS.\n")
    print(f"{'agent':58s}" + "".join(f"{c:>5s}" for c in names))
    ok = True
    ref = run(REF, worlds); print(f"{REF.name:58s}" + "".join(f"{ref[c]:5d}" for c in names))
    if any(ref.values()): ok = False; print("  ^^ THE PAGE IS WRONG: the reference violates its own consequences")
    print()
    for p in POISONS:
        f = run(p, worlds); killed = [c for c in names if c != "E2" and f[c] > 0]
        print(f"{p.name:58s}" + "".join(f"{f[c]:5d}" for c in names) + ("" if killed else "   <-- SURVIVES every consequence"))
        if not killed: ok = False
    print("\nPAGE PASSES" if ok else "\nPAGE FAILS")
    sys.exit(0 if ok else 1)
