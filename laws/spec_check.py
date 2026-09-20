"""Throwaway model of the draft charter's section 2, over Fractions, to test the SPEC (not an implementation)."""
from fractions import Fraction as F
import random, itertools

def push(b, K):                      # predictive over outcomes
    outs = {}
    for w, p in b.items():
        for o, q in K[w].items():
            outs[o] = outs.get(o, 0) + p*q
    return outs

def condition(b, K, o):
    z = sum(p*K[w].get(o, 0) for w, p in b.items())
    assert z > 0, "WORLD_FALSIFIED"
    return {w: p*K[w].get(o, 0)/z for w, p in b.items()}

def E(b, f): return sum(p*f[w] for w, p in b.items())

def V(b, world, n, used=frozenset()):
    T, O = world["T"], world["O"]
    best, arg = None, None
    for t, u in T.items():                          # terminal acts first: ties prefer stopping
        v = E(b, u)
        if best is None or v > best: best, arg = v, t
    if n > 0:
        for k, spec in O.items():
            if spec["once"] and k in used: continue
            q = -spec["price"]
            for o, po in push(b, spec["K"]).items():
                if po == 0: continue
                bo = condition(b, spec["K"], o)
                if o in spec.get("ends", {}):
                    q += po * E(bo, spec["ends"][o])
                else:
                    q += po * V(bo, world, n-1, used | {k})[0]
            if q > best: best, arg = q, k
    return best, arg

def rand_world(rng, nW=3, nT=3, nO=2, nB=2):
    W = list(range(nW))
    raw = [rng.randint(1, 5) for _ in W]; s = sum(raw)
    prior = {w: F(r, s) for w, r in zip(W, raw)}
    T = {f"t{i}": {w: F(rng.randint(-9, 3)) for w in W} for i in range(nT)}
    O = {}
    for j in range(nO):
        K = {}
        for w in W:
            r = [rng.randint(1, 4) for _ in range(nB)]; z = sum(r)
            K[w] = {f"o{i}": F(x, z) for i, x in enumerate(r)}
        O[f"k{j}"] = {"K": K, "price": F(rng.randint(0, 3), 4), "once": True}
    return prior, {"T": T, "O": O}

rng = random.Random(7)
viol = {c: 0 for c in ["C3_gauge", "C3_naive(no price scaling)", "C4_surething", "C5_freeinfo", "C8_horizon", "C2_order"]}
N = 300
for _ in range(N):
    prior, world = rand_world(rng)
    v, a = V(prior, world, 2)
    # C3 gauge: u -> a*u + c with prices scaled by a
    al, c = F(rng.randint(1, 5)), F(rng.randint(-4, 4))
    w2 = {"T": {t: {w: al*x + c for w, x in u.items()} for t, u in world["T"].items()},
          "O": {k: {**s, "price": al*s["price"]} for k, s in world["O"].items()}}
    if V(prior, w2, 2)[1] != a: viol["C3_gauge"] += 1
    w2n = {"T": w2["T"], "O": world["O"]}           # naive statement: prices NOT scaled
    if V(prior, w2n, 2)[1] != a: viol["C3_naive(no price scaling)"] += 1
    # C4 sure-thing: add h(w), the same for every terminal act
    h = {w: F(rng.randint(-5, 5)) for w in prior}
    w3 = {"T": {t: {w: x + h[w] for w, x in u.items()} for t, u in world["T"].items()}, "O": world["O"]}
    if V(prior, w3, 2)[1] != a: viol["C4_surething"] += 1
    # C5 free information
    w4 = {"T": world["T"], "O": {k: {**s, "price": F(0)} for k, s in world["O"].items()}}
    if V(prior, w4, 1)[0] < V(prior, w4, 0)[0]: viol["C5_freeinfo"] += 1
    # C8 monotone horizon
    if not (V(prior, world, 2)[0] >= V(prior, world, 1)[0] >= V(prior, world, 0)[0]): viol["C8_horizon"] += 1
    # C2 order
    k0, k1 = world["O"]["k0"]["K"], world["O"]["k1"]["K"]
    if condition(condition(prior, k0, "o0"), k1, "o1") != condition(condition(prior, k1, "o1"), k0, "o0"): viol["C2_order"] += 1
print(f"{N} random worlds, horizon 2")
for c, n in viol.items(): print(f"  {c:32s} violations: {n}")

# Worked example: 2 states, 1 test, 2 terminal acts
prior = {"sick": F(1, 5), "well": F(4, 5)}
world = {"T": {"treat": {"sick": F(0), "well": F(-2)}, "leave": {"sick": F(-10), "well": F(0)}},
         "O": {"test": {"K": {"sick": {"+": F(9, 10), "-": F(1, 10)}, "well": {"+": F(1, 5), "-": F(4, 5)}},
                        "price": F(1, 2), "once": True}}}
print("\nworked example")
print("  E[treat], E[leave] at prior:", E(prior, world["T"]["treat"]), E(prior, world["T"]["leave"]))
pr = push(prior, world["O"]["test"]["K"]); print("  predictive:", pr)
for o in pr:
    bo = condition(prior, world["O"]["test"]["K"], o)
    print(f"  posterior | {o}:", bo, " V0:", V(bo, world, 0))
print("  V0, act:", V(prior, world, 0), "  V1, act:", V(prior, world, 1))
