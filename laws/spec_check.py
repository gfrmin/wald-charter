"""
spec_check.py - tests the PAGE (CHARTER.md), not any implementation.

Part 1  the reference semantics of CHARTER section 2, over Fractions.
Part 2  the consequences C1-C11 and rule S5 as black-box checks on any agent, plus E2 (the differential).
Part 3  poison agents: bug classes a coding agent really writes (several from the hkaddresses audit
        of 2026-09-20, several found by the attack sessions).
Part 4  every number claimed by the attack sessions, recomputed.
Part 5  the kill matrix. The page passes when
          (a) the reference passes every check on every world,
          (b) the floor (rolling depth 1) passes every consequence,
          (c) every poison is killed by at least one check, and
          (d) every attack finding reproduces.
        The consequences are NECESSARY, not sufficient (attack 2, finding 5.1). A poison marked
        "E2 only" is a bug class that only the differential on toy worlds can see. That is why the
        charter's E5 says `decide` exists once, in the kernel.

Run:  python3 laws/spec_check.py        (exit code 0 = page passes)
"""
from fractions import Fraction as F
import random, sys

class WorldFalsified(Exception): pass
class Refused(Exception): pass

# ---------------------------------------------------------------- Part 1: reference
class Ref:
    name = "reference (d = N)"
    def expect(self, b, f): return sum(p * f[w] for w, p in b.items())
    def push(self, b, K):
        out = {}
        for w, p in b.items():
            for o, q in K[w].items(): out[o] = out.get(o, F(0)) + p * q
        return out
    def condition(self, b, K, o):
        z = sum(p * K[w].get(o, F(0)) for w, p in b.items())
        if z == 0: raise WorldFalsified(o)
        return {w: p * K[w].get(o, F(0)) / z for w, p in b.items()}
    def price(self, spec): return spec["price"]
    def q(self, b, world, k, n, used=frozenset()):
        "Q_n(b,M,k): sums run over outcomes of positive mass; b is conditioned on every outcome, ending or not."
        spec = world["O"][k]; v = -self.price(spec)
        for o, po in self.push(b, spec["K"]).items():
            if po == 0: continue
            bo = self.condition(b, spec["K"], o)
            if o in spec["ends"]: v += po * self.expect(bo, spec["ends"][o])
            else:                 v += po * self.solve(bo, world, n - 1, used | {k})[0]
        return v
    def menu(self, world, used): return [k for k, s in world["O"].items() if not (s["once"] and k in used)]
    def solve(self, b, world, n, used=frozenset()):
        "(V_n, first menu entry attaining it). Menu order: terminal acts, then observational."
        best, arg = None, None
        for t, u in world["T"].items():
            v = self.expect(b, u)
            if best is None or v > best: best, arg = v, t
        if n > 0:
            for k in self.menu(world, used):
                v = self.q(b, world, k, n, used)
                if v > best: best, arg = v, k
        return best, arg
    def decide(self, b, world, n, used=frozenset()): return self.solve(b, world, n, used)[1]

REF = Ref()

class Rolling(Ref):
    "E3, the floor: with n observations left, play decide_min(d,n)."
    def __init__(self, d, name=None): self.d = d; self.name = name or f"the floor: rolling depth d={d}"
    def decide(self, b, world, n, used=frozenset()): return self.solve(b, world, min(self.d, n), used)[1]
class RollingR1(Ref):
    "attack 1, 4a: reading r1 of the draft-2 wording of E3"
    def __init__(self, d): self.d = d
    def decide(self, b, world, n, used=frozenset()): return self.solve(b, world, self.d if n >= 1 else 0, used)[1]

def validate(world, N, d):
    "What a pack must satisfy before anything runs (charter section 1, S4, E3)."
    if not world["T"]: raise Refused("T is empty")
    if any(p <= 0 for p in world["prior"].values()) or sum(world["prior"].values()) != 1: raise Refused("prior not strictly positive, or does not sum to 1")
    for k, s in world["O"].items():
        if any(sum(row.values()) != 1 for row in s["K"].values()): raise Refused(f"kernel {k}: a row does not sum to 1")
    if not (1 <= d <= N): raise Refused("depth must satisfy 1 <= d <= N")

def policy_value(agent, world, n, bt=None, ba=None, used=frozenset(), truth=None):
    """The value of a policy: the expected utility its episodes earn under the declared model.
    `truth` (default: the same world) lets a pack's policy be scored in a different world."""
    truth = truth or world
    bt = truth["prior"] if bt is None else bt
    ba = world["prior"] if ba is None else ba
    a = agent.decide(ba, world, n, used)
    if a in world["T"]: return REF.expect(bt, truth["T"][a])
    spec, tspec = world["O"][a], truth["O"][a]; v = -spec["price"]
    for o, po in REF.push(bt, tspec["K"]).items():
        if po == 0: continue
        bto = REF.condition(bt, tspec["K"], o)
        if o in tspec["ends"]: v += po * REF.expect(bto, tspec["ends"][o])
        else: v += po * policy_value(agent, world, n - 1, bto, agent.condition(ba, spec["K"], o), used | {a}, truth)
    return v

def act_invariant(exp_kept, kept_mass, u_lo, u_hi):
    "E2: with mass 1-kept_mass unevaluated, is the Bayes act the same for every belief consistent with the bound?"
    iv = {t: (kept_mass * e + (1 - kept_mass) * u_lo, kept_mass * e + (1 - kept_mass) * u_hi) for t, e in exp_kept.items()}
    floor_ = max(lo for lo, hi in iv.values())
    return sum(1 for lo, hi in iv.values() if hi >= floor_) == 1, iv

# ---------------------------------------------------------------- random worlds
def rand_world(rng):
    "Omega = E x Z (Z is a nuisance latent: utilities depend on e only)."
    Es, Zs = range(rng.choice([2, 3])), range(2)
    Wd = [(e, z) for e in Es for z in Zs]
    raw = [rng.randint(1, 5) for _ in Wd]; s = sum(raw)
    prior = {w: F(r, s) for w, r in zip(Wd, raw)}
    def u_e():
        ue = {e: F(rng.randint(-9, 3)) for e in Es}
        return {w: ue[w[0]] for w in Wd}
    T = {f"t{i}": u_e() for i in range(3)}
    O = {}
    for j in range(2):
        K = {}
        for w in Wd:
            r = [rng.choice([1, 1, 2, 5, 12]) for _ in range(2)]; z = sum(r)
            K[w] = {f"o{i}": F(x, z) for i, x in enumerate(r)}
        O[f"k{j}"] = {"K": K, "price": F(rng.randint(1, 4), 4), "once": rng.random() < 0.7, "ends": {}}
    if rng.random() < 0.4: O["k1"]["ends"] = {"o1": u_e()}
    return {"prior": prior, "T": T, "O": O}

def clone(world, T=None, O=None): return {"prior": world["prior"], "T": T or world["T"], "O": O or world["O"]}
def all_utils(world):
    vals = [x for u in world["T"].values() for x in u.values()]
    return vals + [x for s in world["O"].values() for ue in s["ends"].values() for x in ue.values()]

# ---------------------------------------------------------------- Part 2: checks (True = holds)
N = 2
def C1(agent, world, rng):
    for spec in world["O"].values():
        pr = agent.push(world["prior"], spec["K"])
        if sum(pr.values()) != 1 or min(pr.values()) < 0: return False
        for o in pr:
            b = agent.condition(world["prior"], spec["K"], o)
            if sum(b.values()) != 1 or min(b.values()) < 0: return False
    return True
def C2(agent, world, rng):
    k0, k1 = world["O"]["k0"]["K"], world["O"]["k1"]["K"]; c = agent.condition
    return c(c(world["prior"], k0, "o0"), k1, "o1") == c(c(world["prior"], k1, "o1"), k0, "o0")
def C3(agent, world, rng):
    a, c = F(rng.randint(2, 5)), F(rng.randint(-6, 6))
    T = {t: {w: a * x + c for w, x in u.items()} for t, u in world["T"].items()}
    O = {k: {**s, "price": a * s["price"], "ends": {o: {w: a * x + c for w, x in ue.items()} for o, ue in s["ends"].items()}} for k, s in world["O"].items()}
    return agent.decide(world["prior"], clone(world, T, O), N) == agent.decide(world["prior"], world, N)
def C4(agent, world, rng):
    h = {w: F(rng.randint(-6, 6)) for w in world["prior"]}
    T = {t: {w: x + h[w] for w, x in u.items()} for t, u in world["T"].items()}
    O = {k: {**s, "ends": {o: {w: x + h[w] for w, x in ue.items()} for o, ue in s["ends"].items()}} for k, s in world["O"].items()}
    return agent.decide(world["prior"], clone(world, T, O), N) == agent.decide(world["prior"], world, N)
def C5(agent, world, rng):
    pure = {k: {**s, "price": F(0)} for k, s in world["O"].items() if not s["ends"]}
    if not pure: return True
    return policy_value(agent, clone(world, O=pure), N) >= policy_value(agent, clone(world, O=pure), 0)
def C6(agent, world, rng):
    X = {w: F(rng.randint(-5, 5)) for w in world["prior"]}
    for spec in world["O"].values():
        for o in ("o0", "o1"):
            z = sum(p * spec["K"][w][o] for w, p in world["prior"].items())
            today = sum(p * spec["K"][w][o] * X[w] for w, p in world["prior"].items()) / z
            if agent.expect(agent.condition(world["prior"], spec["K"], o), X) != today: return False
    return True
def C7(agent, world, rng):
    e0 = {w: F(1 if w[0] == 0 else 0) for w in world["prior"]}
    for spec in world["O"].values():
        groups = {}
        for o, po in REF.push(world["prior"], spec["K"]).items():
            stated = agent.expect(agent.condition(world["prior"], spec["K"], o), e0)
            joint = sum(p * spec["K"][w][o] * e0[w] for w, p in world["prior"].items())
            g = groups.setdefault(stated, [F(0), F(0)]); g[0] += joint; g[1] += po
        if any(j / tot != stated for stated, (j, tot) in groups.items()): return False
    return True
def C8(agent, world, rng): return policy_value(agent, world, 2) >= policy_value(agent, world, 1) >= policy_value(agent, world, 0)
def C9a(agent, world, rng):
    top = max(all_utils(world)) + 1
    T = dict(world["T"]); T["t1"] = {w: top for w in world["prior"]}
    return agent.decide(world["prior"], clone(world, T=T), N) == "t1"
def C9b(agent, world, rng):
    vals = all_utils(world); over = max(vals) - min(vals) + 1
    return agent.decide(world["prior"], clone(world, O={k: {**s, "price": over} for k, s in world["O"].items()}), N) in world["T"]
def C10(agent, world, rng):
    b = world["prior"]
    if REF.solve(b, world, 1)[0] > REF.solve(b, world, 0)[0]: return agent.decide(b, world, N) not in world["T"]
    return True
def C11(agent, world, rng):
    "Garbling (Blackwell), one look left: a noisier copy of a pure act, same price, listed after it, is not played."
    B = dict(world["O"]["k0"]); B["once"] = True
    outs = list(next(iter(B["K"].values()))); m = len(outs)
    KA = {w: {o: F(1, 2) * row[o] + F(1, 2) * F(1, m) for o in outs} for w, row in B["K"].items()}
    O = {"B": B, "A": {"K": KA, "price": B["price"], "once": True, "ends": {}}}
    return agent.decide(world["prior"], clone(world, O=O), 1) != "A"
def S5(agent, world, rng):
    K = {w: {"o0": F(1), "o1": F(0)} for w in world["prior"]}
    try: agent.condition(world["prior"], K, "o1")
    except WorldFalsified: return True
    return False
def same_acts(agent, world, n, bt=None, ba=None, used=frozenset()):
    "E2: the agent plays the reference's act at every reachable (b, M, n). bt = true belief, ba = the agent's own."
    bt = world["prior"] if bt is None else bt
    ba = world["prior"] if ba is None else ba
    a = agent.decide(ba, world, n, used)
    if a != REF.decide(bt, world, n, used): return False
    if a in world["T"]: return True
    spec = world["O"][a]
    for o, po in REF.push(bt, spec["K"]).items():
        if po == 0 or o in spec["ends"]: continue
        if not same_acts(agent, world, n - 1, REF.condition(bt, spec["K"], o), agent.condition(ba, spec["K"], o), used | {a}): return False
    return True
def E2(agent, world, rng): return same_acts(agent, world, N)

CHECKS = [("C1", C1), ("C2", C2), ("C3", C3), ("C4", C4), ("C5", C5), ("C6", C6), ("C7", C7), ("C8", C8),
          ("C9a", C9a), ("C9b", C9b), ("C10", C10), ("C11", C11), ("S5", S5), ("E2", E2)]

# ---------------------------------------------------------------- Part 3: poisons
def marg_e(b):
    m = {}
    for (e, z), p in b.items(): m[e] = m.get(e, F(0)) + p
    return m
class NeverLook(Ref):
    name = "never looks (attack 1, finding 5)"
    def decide(self, b, world, n, used=frozenset()): return self.solve(b, world, 0, used)[1]
class FirstImproving(Ref):
    name = "plays the FIRST look that beats stopping (attack 2, 5.1)"
    pick = staticmethod(lambda qs: qs[0])
    def decide(self, b, world, n, used=frozenset()):
        v0, t = self.solve(b, world, 0, used)
        qs = [(self.q(b, world, k, 1, used), k) for k in self.menu(world, used)] if n >= 1 else []
        qs = [(v, k) for v, k in qs if v > v0]
        return self.pick(qs)[1] if qs else t
class WorstImproving(FirstImproving):
    name = "plays the WORST look that still beats stopping"
    pick = staticmethod(lambda qs: min(qs))
class Gate80(Ref):
    name = "gate: abstain (t0) unless confidence >= 4/5 (audit)"
    def decide(self, b, world, n, used=frozenset()):
        return "t0" if max(marg_e(b).values()) < F(4, 5) else super().decide(b, world, n, used)
class MaxForSum(Ref):
    name = "max over the nuisance latent where the model says sum (audit)"
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
    name = "posterior clipped at 1/2 then renormalised"
    def condition(self, b, K, o):
        c = {w: min(p, F(1, 2)) for w, p in super().condition(b, K, o).items()}; s = sum(c.values())
        return {w: p / s for w, p in c.items()}
class InfoMax(Ref):
    name = "buys the most informative test, ignoring price and stakes"
    def decide(self, b, world, n, used=frozenset()):
        if n > 0 and max(marg_e(b).values()) < F(9, 10):
            best, arg = None, None
            for k in self.menu(world, used):
                s = world["O"][k]
                g = sum(po * max(marg_e(self.condition(b, s["K"], o)).values()) for o, po in self.push(b, s["K"]).items() if po > 0)
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
    name = "WORLD poison: kernel rows sum to < 1 (audit, A34)"
    leaky = True

POISONS = [NeverLook(), FirstImproving(), WorstImproving(), Rolling(1, "ignores the declared depth, always d=1 (attack 2, 5.1)"),
           Gate80(), MaxForSum(), DoubleCount(), Dampen(), Clip(), InfoMax(), ZeroBaseline(), IgnorePrice(), SilentZero(), LeakyKernelWorld()]

def leak(world):
    return clone(world, O={k: {**s, "K": {w: {o: q * F(9, 10) for o, q in row.items()} for w, row in s["K"].items()}} for k, s in world["O"].items()})

# ---------------------------------------------------------------- Part 4: attack sessions, every claimed number
def Wd(prior, T, O): return {"prior": prior, "T": T, "O": O}
def act(K, price, once, ends=None): return {"K": K, "price": price, "once": once, "ends": ends or {}}
APPX_T = {"treat": {"sick": F(0), "well": F(-2)}, "leave": {"sick": F(-10), "well": F(0)}}
APPX_K = {"sick": {"+": F(9, 10), "-": F(1, 10)}, "well": {"+": F(1, 5), "-": F(4, 5)}}
def appendix(price, once): return Wd({"sick": F(1, 5), "well": F(4, 5)}, APPX_T, {"test": act(APPX_K, price, once)})

def attack_findings():
    out = []
    def claim(tag, got, want): out.append((tag, got == want, got))
    # ===== session 1 (on draft 2)
    Kp = {"x": {"p": F(3, 4), "m": F(1, 4)}, "y": {"p": F(1, 4), "m": F(3, 4)}}
    T = {"go": {"x": F(1), "y": F(-4)}, "hold": {"x": F(0), "y": F(0)}}
    P = Wd({"x": F(1, 2), "y": F(1, 2)}, T, {"k1": act(Kp, F(1, 20), True), "k2": act(Kp, F(1, 20), True)})
    st = [(w, d) for w in "xy" for d in "pm"]
    read = {(w, d): {"p": F(1 if d == "p" else 0), "m": F(1 if d == "m" else 0)} for (w, d) in st}
    P3 = Wd({(w, d): F(1, 2) * Kp[w][d] for (w, d) in st}, {t: {(w, d): u[w] for (w, d) in st} for t, u in T.items()},
            {"k1": act(read, F(1, 20), True), "k2": act(read, F(1, 20), True)})
    claim("s1 1a  independent-evidence pack believes", REF.solve(P["prior"], P, 2), (F(13, 160), "k1"))
    claim("s1 1a  ...and earns, scored where the draw is shared", policy_value(REF, P, 2, truth=P3), F(-1, 5))
    claim("s1 1a  with the draw in Omega (S2)", REF.solve(P3["prior"], P3, 2), (F(0), "hold"))
    Kh = {"x": {"sx": F(1, 2), "sy": F(0), "blank": F(1, 2)}, "y": {"sx": F(0), "sy": F(1, 2), "blank": F(1, 2)}}
    H = Wd({"x": F(1, 2), "y": F(1, 2)}, {"X": {"x": F(1), "y": F(0)}, "Y": {"x": F(0), "y": F(1)}}, {"peek": act(Kh, F(1, 10), False)})
    claim("s1 1b  Q_1(peek)", REF.solve(H["prior"], H, 1), (F(13, 20), "peek"))
    claim("s1 4c  Q_2(peek), zero-mass outcomes skipped", REF.solve(H["prior"], H, 2), (F(29, 40), "peek"))
    hit = {"x": F(1), "y": F(1)}
    W2 = Wd({"x": F(1, 3), "y": F(2, 3)}, {"concede": {"x": F(0), "y": F(0)}},
            {"gx": act({"x": {"hit": F(1), "miss": F(0)}, "y": {"hit": F(0), "miss": F(1)}}, F(0), True, {"hit": hit}),
             "gy": act({"x": {"hit": F(0), "miss": F(1)}, "y": {"hit": F(1), "miss": F(0)}}, F(0), True, {"hit": hit})})
    claim("s1 1c  decide_2 on W2", REF.solve(W2["prior"], W2, 2), (F(1), "gx"))
    try: validate(Wd(W2["prior"], {}, W2["O"]), 1, 1); claim("s1 4b  empty T refused", False, True)
    except Refused: claim("s1 4b  empty T refused", True, True)
    S = ["00", "01", "10", "11"]
    def look(i): return {w: {w[i]: F(1, 2), "blank": F(1, 2)} for w in S}
    X = Wd({w: F(1, 4) for w in S}, {"same": {w: F(1 if w[0] == w[1] else 0) for w in S}, "diff": {w: F(1 if w[0] != w[1] else 0) for w in S}},
           {"lookA": act(look(0), F(1, 100), False), "lookB": act(look(1), F(1, 100), False)})
    claim("s1 4a  decide_2 on X", REF.solve(X["prior"], X, 2), (F(61, 100), "lookA"))
    claim("s1 4a  policy value: reading r1, reading r2 = decide_min(d,n)", (policy_value(RollingR1(2), X, 3), policy_value(Rolling(2), X, 3)), (F(289, 400), F(29, 40)))
    A1 = appendix(F(1, 2), True)
    claim("s1 5   appendix decide_1", REF.solve(A1["prior"], A1, 1), (F(-51, 50), "test"))
    claim("s1 5   regret of never looking", REF.solve(A1["prior"], A1, 1)[0] - policy_value(NeverLook(), A1, 1), F(29, 50))
    # ===== session 2 (on draft 3)
    probe = act({"a": {"x": F(1)}, "b": {"y": F(1)}, "c": {"hit": F(1)}}, F(1, 10), True, {"hit": {"a": F(1), "b": F(1), "c": F(1)}})
    Z = Wd({"a": F(1, 2), "b": F(1, 2), "c": F(0)}, {f"say-{s}": {w: F(1 if w == s else 0) for w in "abc"} for s in "abc"}, {"probe-c": probe})
    try: validate(Z, 1, 1); claim("s2 1.1 a zero-prior state is refused (the Prior is strictly positive)", False, True)
    except Refused: claim("s2 1.1 a zero-prior state is refused (the Prior is strictly positive)", True, True)
    ok, iv = act_invariant({"t1": F(99, 197), "t2": F(98, 197)}, F(197, 200), F(0), F(1))
    claim("s2 1.2 dropping 3/200: intervals", iv, {"t1": (F(99, 200), F(102, 200)), "t2": (F(98, 200), F(101, 200))})
    claim("s2 1.2 ...the act is NOT invariant, so E2 makes the fast path evaluate more", ok, False)
    KX = {"a": {"1": F(1), "0": F(0)}, "bot": {"1": F(1, 2), "0": F(1, 2)}}
    Tb = {"bet": {"a": F(1), "bot": F(-3)}, "pass": {"a": F(0), "bot": F(0)}}
    L = Wd({"a": F(1, 2), "bot": F(1, 2)}, Tb, {"X": act(KX, F(1, 20), True), "Y": act(KX, F(1, 20), True)})
    KX2 = {"a": {"1": F(1), "0": F(0)}, "r1": {"1": F(1), "0": F(0)}, "r0": {"1": F(0), "0": F(1)}}
    L2 = Wd({"a": F(1, 2), "r1": F(1, 4), "r0": F(1, 4)}, {"bet": {"a": F(1), "r1": F(-3), "r0": F(-3)}, "pass": {"a": F(0), "r1": F(0), "r0": F(0)}},
            {"X": act(KX2, F(1, 20), True), "Y": act(KX2, F(1, 20), True)})
    claim("s2 1.3 the lump pack", REF.solve(L["prior"], L, 2), (F(3, 80), "X"))
    claim("s2 1.3 the split pack", REF.solve(L2["prior"], L2, 2), (F(0), "pass"))
    claim("s2 1.3 the lump's policy scored in the split world", policy_value(REF, L, 2, truth=L2), F(-27, 80))
    Kpa = {"a": {"hit": F(1), "miss": F(0)}, "b": {"hit": F(0), "miss": F(1)}}
    claim("s2 3.1 stated P(a) after `hit`: draft-3 loop (no condition) vs draft-4 loop", (F(1, 2), REF.condition({"a": F(1, 2), "b": F(1, 2)}, Kpa, "hit")["a"]), (F(1, 2), F(1)))
    A2 = appendix(F(1, 10), True)
    claim("s2 3.2 root", REF.solve(A2["prior"], A2, 2), (F(-31, 50), "test"))
    bplus = REF.condition(A2["prior"], APPX_K, "+")
    claim("s2 3.2 after +: V_0, Q_1 of the SPENT test, and the act with test out of M",
          (REF.solve(bplus, A2, 0)[0], REF.q(bplus, A2, "test", 1), REF.decide(bplus, A2, 1, frozenset({"test"}))), (F(-16, 17), F(-139, 170), "treat"))
    claim("s2 3.3 price 1/2 is 'above the range [-10,0]' yet decide_1 = test", REF.decide(A1["prior"], A1, 1), "test")
    A3 = appendix(F(1, 10), False)
    claim("s2 4.1 V_1(P0), and what rolling d=1 earns over N=2 (= V_2)",
          (REF.solve(A3["prior"], A3, 1)[0], policy_value(Rolling(1), A3, 2), REF.solve(A3["prior"], A3, 2)[0]), (F(-31, 50), F(-289, 500), F(-289, 500)))
    KA = {"sick": {"+": F(4, 5), "-": F(1, 5)}, "well": {"+": F(3, 10), "-": F(7, 10)}}
    FIw = Wd(A1["prior"], APPX_T, {"A": act(KA, F(1, 2), True), "B": act(APPX_K, F(1, 2), True)})
    claim("s2 5.1 Q_1(A), Q_1(B)", (REF.q(FIw["prior"], FIw, "A", 1), REF.q(FIw["prior"], FIw, "B", 1)), (F(-69, 50), F(-51, 50)))
    claim("s2 5.1 reference earns / first-improving earns", (policy_value(REF, FIw, 1), policy_value(FirstImproving(), FIw, 1)), (F(-51, 50), F(-69, 50)))
    bit = lambda i: {w: {"0": F(1 if w[i] == "0" else 0), "1": F(1 if w[i] == "1" else 0)} for w in S}
    Par = Wd({w: F(1, 4) for w in S}, {"even": {w: F(1 if w[0] == w[1] else 0) for w in S}, "odd": {w: F(1 if w[0] != w[1] else 0) for w in S}},
             {"X": act(bit(0), F(1, 10), True), "Y": act(bit(1), F(1, 10), True)})
    claim("s2 5.1 parity: reference at d=N=2 / impostor at d=1", (REF.solve(Par["prior"], Par, 2), policy_value(Rolling(1), Par, 2)), ((F(4, 5), "X"), F(1, 2)))
    # ===== session 3 (on draft 4): four ambiguities, each fixed to the reading this script already implemented
    one = lambda v: {"x": F(v), "y": F(v)}
    W1 = Wd({"x": F(1, 2), "y": F(1, 2)}, {"quit": one(0), "sulk": {"x": F(-1, 8), "y": F(-1, 8)}},
            {"g": act({"x": {"hit": F(1), "miss": F(0)}, "y": {"hit": F(0), "miss": F(1)}}, F(1, 4), True, {"hit": one(1)})})
    claim("s3 4.1 W1: decide_1 (C9 must count ending utilities, or it contradicts C10)", REF.solve(W1["prior"], W1, 1), (F(1, 4), "g"))
    Kk = {"a": {"x": F(3, 4), "y": F(1, 4)}, "b": {"x": F(1, 4), "y": F(3, 4)}}
    W2_ = Wd({"a": F(1, 2), "b": F(1, 2)}, {"A": {"a": F(1), "b": F(0)}, "B": {"a": F(0), "b": F(2)}}, {"k1": act(Kk, F(0), True), "k2": act(Kk, F(0), True)})
    bx = REF.condition(W2_["prior"], Kk, "x")
    claim("s3 4.2 W2: root, then after x with k1 spent (C11 must mean 'listed before it IN M')",
          (REF.solve(W2_["prior"], W2_, 2), REF.solve(bx, W2_, 1, frozenset({"k1"}))), ((F(39, 32), "k1"), (F(15, 16), "k2")))
    T01 = {"A": {"a": F(1), "b": F(0)}, "B": {"a": F(0), "b": F(1)}}
    W3 = Wd({"a": F(1, 2), "b": F(1, 2)}, T01,
            {"cheap": act({"a": {"x": F(9, 20), "y": F(1, 20), "z": F(1, 2)}, "b": {"x": F(1, 20), "y": F(9, 20), "z": F(1, 2)}}, F(1, 20), True),
             "exp": act({"a": {"al": F(1), "be": F(0)}, "b": {"al": F(0), "be": F(1)}}, F(1, 4), True)})
    claim("s3 4.3 W3: policy value, NET of prices, at d=1 and d=2 (regret of d=1 is 1/40)",
          (policy_value(Rolling(1), W3, 2), policy_value(Rolling(2), W3, 2)), (F(3, 4), F(31, 40)))
    W4 = Wd({"a": F(1, 2), "b": F(1, 2)}, T01,
            {"cheap": act({"a": {"al": F(1, 2), "be": F(0), "q": F(1, 2)}, "b": {"al": F(0), "be": F(1, 2), "q": F(1, 2)}}, F(1, 10), False),
             "exp": act({"a": {"al": F(1), "be": F(0)}, "b": {"al": F(0), "be": F(1)}}, F(3, 10), True)})
    class ByBelief(Ref):
        "keys its act on the belief alone: at the prior it always plays the root act"
        def decide(self, b, world, n, used=frozenset()):
            return "cheap" if (n >= 1 and b == world["prior"]) else super().decide(b, world, n, used)
    claim("s3 4.4 W4: the reference plays cheap at (P0,M,2) and exp at (P0,M,1)",
          (REF.decide(W4["prior"], W4, 2), REF.decide(W4["prior"], W4, 1)), ("cheap", "exp"))
    claim("s3 4.4 W4: reference value / keyed-by-belief kernel's value / does E2 over (b,M,n) catch it",
          (policy_value(REF, W4, 2), policy_value(ByBelief(), W4, 2), same_acts(ByBelief(), W4, 2)), (F(3, 4), F(29, 40), False))
    return out

# ---------------------------------------------------------------- Part 5: kill matrix
def run(agent, worlds):
    fails = {c: 0 for c, _ in CHECKS}
    for i, world in enumerate(worlds):
        w = leak(world) if getattr(agent, "leaky", False) else world
        for cname, check in CHECKS:
            try: good = check(agent, w, random.Random(1000 + i))
            except WorldFalsified: good = False
            if not good: fails[cname] += 1
    return fails

if __name__ == "__main__":
    rng = random.Random(20260920)
    worlds = [rand_world(rng) for _ in range(200)]
    for w in worlds: validate(w, N, N)
    names = [c for c, _ in CHECKS]; ok = True
    row = lambda name, f: f"{name[:62]:62s}" + "".join(f"{f[c]:4d}" for c in names)
    print(f"{len(worlds)} random worlds, horizon {N}. Cells = worlds on which the check FAILS.\n")
    print(f"{'agent':62s}" + "".join(f"{c:>4s}" for c in names))
    ref = run(REF, worlds); print(row(REF.name, ref))
    if any(ref.values()): ok = False; print("  ^^ THE PAGE IS WRONG: the reference violates its own consequences")
    fl = Rolling(1); f = run(fl, worlds); print(row(fl.name, f))
    reg = [REF.solve(w["prior"], w, N)[0] - policy_value(fl, w, N) for w in worlds]
    print(f"    regret of d=1 against d=N: > 0 on {sum(r > 0 for r in reg)} worlds, mean {float(sum(reg) / len(reg)):.4f}, max {float(max(reg)):.4f}")
    if any(f[c] for c in names if c != "E2"): ok = False; print("  ^^ the floor violates a consequence")
    print()
    for p in POISONS:
        f = run(p, worlds); by_c = [c for c in names if c != "E2" and f[c] > 0]
        mark = "" if by_c else ("   <-- E2 only" if f["E2"] else "   <-- SURVIVES EVERYTHING")
        print(row(p.name, f) + mark)
        if not by_c and not f["E2"]: ok = False
    print("\nattack sessions - every claimed number, recomputed:")
    for tag, good, got in attack_findings():
        print(f"  {'reproduced' if good else 'NOT REPRODUCED':15s} {tag}")
        if not good: ok = False; print("       got:", got)
    print("\nPAGE PASSES" if ok else "\nPAGE FAILS")
    sys.exit(0 if ok else 1)
