"""wald against hkaddresses' decide on the same collapsed posteriors: milliseconds a call. Reads only."""
import random, statistics, sys, time
sys.path.insert(0, ".")
import wald
from hkaddresses.decide import decide
from hkaddresses.world import build_world
from tests.test_ask import _draw, _hypotheses, DRAW_FIELDS
from tests.test_decide import towers_world
from tests.toy_worlds import corner
from tests.test_wald_oracle import LOSS, _Answer, _world_spec

def timed(f):
    t = time.perf_counter(); r = f(); return r, (time.perf_counter() - t) * 1e3

def fixed(rng, world, n, fields):            # _draw, at exactly n states
    while True:
        post, exact, groups = _draw(rng, world, width=n, fields=fields)
        if len(exact) == n: return post, exact, groups

worlds = {"towers": towers_world(), "corner": build_world(corner())}
print("world   states  ask  n   decide ms   declare ms   run ms   wald ms   ratio   wald rows/s")
for wname, world in worlds.items():
    top = len(_hypotheses(world))
    for n in [w for w in (2, 4, 8, 16, 32, 64) if w <= top]:
        for ask in (False, True):
            rng = random.Random(7); d, dc, rn, same, k = [], [], [], 0, 0
            for _ in range(60 if n <= 16 else 20):
                post, exact, groups = fixed(rng, world, n, DRAW_FIELDS[0])
                dec, td = timed(lambda: decide(world, post, LOSS, groups if ask else None))
                spec, answers = _world_spec(world, exact, groups, LOSS, ask=ask)
                W, t1 = timed(lambda: wald.declare(spec))
                res, t2 = timed(lambda: wald.run(W, _Answer(answers)))
                d.append(td); dc.append(t1); rn.append(t2); k += 1
            m = statistics.median
            w = m(dc) + m(rn)
            print(f"{wname:7} {n:6}  {'y' if ask else 'n'}   {k:3} {m(d):9.3f} {m(dc):11.2f} {m(rn):9.2f} {w:9.2f} {w/m(d):7.0f} {1e3/w:12.1f}")
