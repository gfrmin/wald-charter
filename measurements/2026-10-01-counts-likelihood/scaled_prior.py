"""Does the lookahead's cost come from the belief's bits, or from its normalisation? Play the
same episode from (a) the kernel's normalised prior and (b) the same measure scaled to integers
by a common denominator. Exact both ways; the acts and the final belief must agree."""
import math, sys, time
from collections import Counter
from fractions import Fraction
import wald
from wald import counts as C
from wald.belief import _sealed, _weights
from wald.plate import plate
from wald.episode import _play

PACK = sys.argv[1]; MULTS = [int(x) for x in sys.argv[2].split(",")]

class ScriptedDoor(wald.Door):
    def outcome(self, act):
        return {"confidence": "b1", "agreement": "all", "second_opinion": "same"}.get(act, "right")
    def fire(self, act): pass

def scaled_prior(plated, counts):
    "P(Global | Counts) P(local | Global) times one integer: every weight an int"
    recs = list(counts)
    L = {r: {g: C.likelihood(plated, r, g) for g in plated.pg} for r in recs}
    D = {r: math.lcm(*[x.denominator for x in L[r].values()]) for r in recs}
    Dg = math.lcm(*[p.denominator for p in plated.pg.values()])
    Dl = math.lcm(*[p.denominator for pl in plated.pl.values() for p in pl.values()])
    out = {}
    for g, pg in plated.pg.items():
        w = pg.numerator * (Dg // pg.denominator)
        for r in recs:
            x = L[r][g]
            w *= (x.numerator * (D[r] // x.denominator)) ** counts[r]
        if not w: continue
        for state, p in plated.pl[g].items():
            if p: out[state] = w * p.numerator * (Dl // p.denominator)
    return _sealed(out)

t = time.time(); world = wald.declare(wald.load_pack(open(PACK, encoding="utf-8", newline="").read(), ".")); print(f"load {time.time()-t:.0f}s", flush=True)
plated = plate(world)._plated; base = Counter(plated.counts)
for m in MULTS:
    counts = Counter({r: n * m for r, n in base.items()})
    t = time.time(); ep = C.episode_prior(plated, counts); t_ep = time.time() - t
    t = time.time(); sp = scaled_prior(plated, counts); t_sp = time.time() - t
    w = _weights(sp); bits = max(x.bit_length() for x in w.values())
    t = time.time(); r1 = _play(plated.world, ep, ScriptedDoor()); t1 = time.time() - t; plated.world._work = None
    t = time.time(); r2 = _play(plated.world, sp, ScriptedDoor()); t2 = time.time() - t; plated.world._work = None
    same_final = _weights(r1.final) == _weights(r2.final)
    print(f"T={sum(counts.values()):5d}: prior {t_ep:5.2f}s / scaled {t_sp:5.2f}s (int bits {bits}) | _play normalised {t1:6.2f}s | _play integer {t2:6.2f}s | acts equal {r1.acts == r2.acts} | final equal {same_final} | ops {r1.operations} {r2.operations}", flush=True)
