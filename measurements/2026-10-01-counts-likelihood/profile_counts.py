"""Where an episode's seconds go on the arena's World (1,152 Global values) as the Counts grow.
Exact throughout; every variant of the posterior is asserted equal to the kernel's."""
import cProfile, pstats, io, resource, sys, time
from collections import Counter
from fractions import Fraction
import wald
from wald import counts as C
from wald.belief import _sealed, _weights
from wald.plate import plate
from wald.episode import _play

PACK = sys.argv[1]
MULTS = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0, 1, 2]

class ScriptedDoor(wald.Door):
    def outcome(self, act):
        return {"confidence": "b1", "agreement": "all", "second_opinion": "same"}.get(act, "right")
    def fire(self, act): pass

def post_once(plated, counts):
    "reference-style: multiply every token in, normalise once"
    w = dict(plated.pg)
    for rec, n in counts.items():
        for g in w: w[g] *= C.likelihood(plated, rec, g) ** n
    s = sum(w.values())
    return _sealed({g: v / s for g, v in w.items() if v})

def post_int(plated, counts):
    "integer-only: per Global one numerator and one denominator, no gcd until the end"
    num = {g: p.numerator for g, p in plated.pg.items()}
    den = {g: p.denominator for g, p in plated.pg.items()}
    for rec, n in counts.items():
        for g in num:
            L = C.likelihood(plated, rec, g)
            num[g] *= L.numerator ** n; den[g] *= L.denominator ** n
    # common denominator D = lcm is costly; use the product-free form: w_g = num_g/den_g, s = sum
    s = sum(Fraction(num[g], den[g]) for g in num)
    return _sealed({g: Fraction(num[g], den[g]) / s for g in num if num[g]})

t = time.time(); world = wald.declare(wald.load_pack(open(PACK, encoding="utf-8", newline="").read(), ".")); print(f"load_pack {time.time()-t:.1f}s", flush=True)
pl = plate(world); plated = pl._plated
base = Counter(plated.counts)
print(f"shipped Counts: {sum(base.values())} records, {len(base)} distinct; Global values {len(plated.pg)}", flush=True)
liks = {g: [C.likelihood(plated, r, g) for r in base] for g in list(plated.pg)[:3]}
print("likelihood bits (3 Globals, max over distinct records):", [max(max(l.numerator.bit_length(), l.denominator.bit_length()) for l in ls) for ls in liks.values()], flush=True)

for m in MULTS:
    counts = Counter({r: n * m for r, n in base.items()}) if m else Counter()
    T = sum(counts.values())
    t = time.time(); pg = C.posterior_global(plated, counts); t_pg = time.time() - t
    t = time.time(); pg1 = post_once(plated, counts); t_once = time.time() - t
    t = time.time(); pg2 = post_int(plated, counts); t_int = time.time() - t
    assert _weights(pg) == _weights(pg1) == _weights(pg2)
    w = _weights(pg)
    bits = max(max(f.numerator.bit_length(), f.denominator.bit_length()) for f in w.values())
    t = time.time(); ep = C.episode_prior(plated, counts); t_ep = time.time() - t
    t = time.time(); r = _play(plated.world, ep, ScriptedDoor()); t_play = time.time() - t
    print(f"T={T:5d}: posterior kernel {t_pg:6.2f}s  once {t_once:6.2f}s  int {t_int:6.2f}s | mass bits {bits:6d} | states {len(w)} | episode_prior {t_ep:6.2f}s | _play {t_play:6.2f}s  acts {r.acts}", flush=True)
    plated.world._work = None

# profile one episode at the last multiplicity: counts vs decide
counts = Counter({r: n * MULTS[-1] for r, n in base.items()})
pr = cProfile.Profile(); pr.enable()
ep = C.episode_prior(plated, counts); r = _play(plated.world, ep, ScriptedDoor())
pr.disable()
s = io.StringIO(); ps = pstats.Stats(pr, stream=s).sort_stats("cumulative"); ps.print_stats(18); print(s.getvalue()[:4000])
print(f"maxrss {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6:.2f} GB")
