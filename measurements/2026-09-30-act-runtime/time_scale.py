"""wald alone on Worlds of the oracle test's shape, larger than the toy worlds allow: n states in a binary tree
(a terminal per node, -beta * bits left open beneath it, -alpha elsewhere), q deterministic three-valued questions at kappa_ask."""
import math, random, statistics, time
from fractions import Fraction as F
import wald
class Door(wald.Door):
    def __init__(s, a): s.a = a
    def outcome(s, act): return s.a[act]
    def fire(s, act): pass
def spec(n, q, rng):
    states = [f"h{i:04d}" for i in range(n)]
    w = [rng.randint(1, 64) for _ in states]; tot = sum(w)
    prior = {h: F(x, tot) for h, x in zip(states, w)}
    T, lo, size = {}, 0, n
    nodes = []
    span = n
    while span >= 1:                                   # every dyadic block of leaves is a node
        nodes += [(a, min(a + span, n)) for a in range(0, n, span)]
        span //= 2
    for a, b in dict.fromkeys(nodes):
        top = F(math.log2(b - a))
        T[f"assert {a}:{b}"] = {h: (-top if a <= i < b else F(-9)) for i, h in enumerate(states)}
    O, ans = {}, {}
    for j in range(q):
        of = {h: f"v{(i + j) % 3}" for i, h in enumerate(states)}
        O[f"ask f{j}"] = {"K": {h: {of[h]: F(1)} for h in states}, "price": F(1), "once": True, "ends": {}}
        ans[f"ask f{j}"] = of[states[0]]
    return {"prior": prior, "T": T, "O": O, "N": 1, "d": 1, "closed": True,
            "table_sources": {"prior": "elicited", "utility": "elicited", "price": "elicited", "horizon": "elicited",
                              "depth": "elicited", "kernels": {k: ["elicited"] for k in O}}}, ans
print("states  terminals  questions   declare ms    run ms   rows/s")
for n in (8, 16, 32, 64, 128, 256, 400):
    for q in (0, 2, 5):
        rng = random.Random(7); dc, rn = [], []
        for _ in range(7):
            s, a = spec(n, q, rng)
            t = time.perf_counter(); W = wald.declare(s); t1 = time.perf_counter(); wald.run(W, Door(a)); t2 = time.perf_counter()
            dc.append((t1 - t) * 1e3); rn.append((t2 - t1) * 1e3)
        m = statistics.median
        print(f"{n:6} {len(s['T']):10} {q:10} {m(dc):12.2f} {m(rn):9.2f} {1e3/(m(dc)+m(rn)):8.1f}")
