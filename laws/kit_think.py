"""
kit_think.py - kit v0.7: judges an implementation's think act against CHARTER v0.1 (`laws/meta_check.py` is the reference).

Called from kit.py as kit_think.main(impl, seed) -> bool.  What it asks of the implementation (INTERFACE.md, kit v0.7):

  agent.step(b, world, n, used) -> (act, how, paid)     the v0.1 step: `how` in {"floor", "struck_n", "struck_cap",
                                                        "refused", "think"} (S7's buckets; "floor" for a World without
                                                        theta), `paid` the predicted cost c charged (0 unless "think").
  wald.world.declare(spec)                              refuses by name FRACTION, COST, DEPTH_PLUS, RATE, UNSCORED.

A World dict may carry d, dplus, fraction, rate, ops (and table_sources gains fraction, cost, rate; score for a fitted
meta-table).  Without dplus it is a v0 World and step must report "floor" and play decide_min(d, n).

Self-test:  python3 laws/kit_think.py --standin      runs main against the reference itself (must pass) and against a
poison (must fail), so the kit is tested before anyone implements the brief.
"""
import importlib, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction as F
import spec_check as S
import meta_check as M

class Impl:
    "Wraps the builder's agent for meta_check's checks: they call step/decide/solve-free interfaces only."
    name = "implementation"
    def __init__(self, agent): self.a = agent
    def step(self, b, world, n, used=frozenset()):
        act, how, paid = self.a.step(b, world, n, used)
        return act, how, F(paid)
    def decide(self, b, world, n, used=frozenset()): return self.step(b, world, n, used)[0]

def v0_spec(w, **extra):
    "A declare() spec for a World dict: the v0 keys the kernel needs plus the v0.1 ones."
    spec = {"prior": w["prior"], "T": w["T"], "O": w["O"], "N": w["N"], "d": w.get("d", 1), "closed": True,
            "table_sources": {"prior": "elicited", "utility": "elicited", "price": "elicited", "horizon": "elicited",
                              "depth": "elicited", "kernels": {k: ["elicited"] for k in w["O"]}}}
    if "dplus" in w:
        spec.update({"dplus": w["dplus"], "fraction": w["fraction"], "rate": w["rate"], "ops": w["ops"]})
        spec["table_sources"].update({"fraction": "elicited", "cost": "elicited", "rate": "elicited"})
    spec.update(extra); return spec

def refusal_cases():
    "(name, spec) pairs the kernel must refuse, each by that name."
    A = M.vector_A()
    bad_ts = lambda **kw: {**v0_spec(A)["table_sources"], **kw}
    return [
        ("FRACTION", v0_spec(A, fraction=F(3, 2))),
        ("FRACTION", v0_spec(A, fraction=F(-1, 4))),
        ("FRACTION", v0_spec(A, table_sources=bad_ts(fraction="data"))),
        ("COST", v0_spec(A, ops={2: F(1)})),                           # a missing cell
        ("COST", v0_spec(A, ops={1: F(1), 2: F(-1)})),
        ("COST", v0_spec(A, table_sources=bad_ts(cost="data"))),
        ("DEPTH_PLUS", v0_spec(A, dplus=1)),
        ("DEPTH_PLUS", v0_spec(A, dplus=3, N=3)),
        ("DEPTH_PLUS", v0_spec(A, d=2, N=3, dplus=3)),
        ("DEPTH_PLUS", v0_spec(A, N=1, dplus=2)),
        ("RATE", v0_spec(A, table_sources=bad_ts(rate="fitted"))),
        ("UNSCORED", v0_spec(A, table_sources=bad_ts(fraction="fitted"))),
        ("UNSCORED", v0_spec(A, table_sources=bad_ts(cost="fitted"))),
    ]

def main(impl, seed, agent=None, declare=None, refused_cls=None, quiet=False):
    say = (lambda *a: None) if quiet else print
    ok = True
    # 1. kit integrity: the reference passes its own checks and every poison dies (the test the page passed)
    rng = random.Random(20260921); ws = [M.rand_meta_world(rng) for _ in range(30)]
    ws += [w for w in (M.rand_meta_world(rng) for _ in range(3000)) if M.forced(w)][:30]
    if any(M.run(M.DPLUS, ws).values()): say("KIT BROKEN: the v0.1 reference fails its own checks"); return False
    for p in M.POISONS:
        if not any(M.run(p, ws).values()): say("KIT BROKEN: think poison survives:", p.name); return False
    M.frozen(False); M.attack_findings()
    say("think kit integrity: reference clean,", len(M.POISONS), "poisons killed, appendix vectors and attack Worlds hold")
    # 2. the implementation
    if agent is None:
        sys.path.insert(0, os.path.abspath(impl))
        a = importlib.import_module("wald.kit_adapter").make_agent()
        if not hasattr(a, "step"): say("FAIL think: the adapter has no `step` (INTERFACE.md, kit v0.7)"); return False
        agent = Impl(a)
        world_mod = importlib.import_module("wald.world"); declare = world_mod.declare
        refused_cls = importlib.import_module("wald.refusals").Refused
    fails = {}
    rng = random.Random(seed)
    worlds = [M.rand_meta_world(rng) for _ in range(40)]
    worlds += [w for w in (M.rand_meta_world(rng) for _ in range(4000)) if M.forced(w)][:20]
    fixed = M.fixed_worlds()
    for i, w in enumerate(worlds + list(fixed.values())):
        for cname, check in M.CHECKS:
            if i >= len(worlds) and cname != "E2": continue          # pinned Worlds: differential only
            try: good = check(agent, w, random.Random(1000 + i))
            except Exception as e: good = False; fails.setdefault(f"{cname} (raised {type(e).__name__}: {e})", w)
            if not good:
                label = cname if i < len(worlds) else f"{cname} on World {list(fixed)[i - len(worlds)]}"
                fails.setdefault(label, w)
    # a v0 World (no theta): step says "floor" and plays decide_min(d, n)
    rng2 = random.Random(seed + 1)
    for w in ({**S.rand_world(rng2), "N": 3, "d": 1} for _ in range(30)):
        try:
            a_, how, paid = agent.step(w["prior"], w, 3)
            if (a_, how, paid) != (S.Rolling(1).decide(w["prior"], w, 3), "floor", 0): fails.setdefault("v0 World: step must report 'floor' and play decide_min(d,n) at cost 0", w)
        except Exception as e: fails.setdefault(f"v0 World: step raised {type(e).__name__}", w)
    # 3. refusals by name
    for name, spec in refusal_cases():
        try: declare(spec); fails.setdefault(f"refusal {name}: the pack was accepted", spec)
        except Exception as e:
            got = getattr(e, "name", None) or str(e)
            if not (refused_cls is None or isinstance(e, refused_cls)) or got != name:
                fails.setdefault(f"refusal {name}: got {type(e).__name__} {got!r}", spec)
    for label, w in fails.items():
        ok = False; say("FAIL think:", label); say("  first failing world:", {k: str(v) if not isinstance(v, dict) else "..." for k, v in w.items()})
    say(f"think: {len(worlds)} Worlds + {len(fixed)} pinned, {len(refusal_cases())} refusals:", "pass" if ok else "FAIL")
    return ok

if __name__ == "__main__":
    if "--standin" in sys.argv:
        class Decl:
            "a stand-in declare: refuses exactly what refuse_meta refuses, plus RATE and UNSCORED from table_sources"
            @staticmethod
            def declare(spec):
                M.refuse_meta(spec)
                ts = spec.get("table_sources", {})
                if "dplus" in spec:
                    if ts.get("fraction") not in ("elicited", "fitted"): raise S.Refused("FRACTION")
                    if ts.get("cost") not in ("elicited", "fitted"): raise S.Refused("COST")
                    if ts.get("rate") != "elicited": raise S.Refused("RATE")
                    if "fitted" in (ts.get("fraction"), ts.get("cost")) and "score" not in spec: raise S.Refused("UNSCORED")
                return spec
        good = main(None, 5, agent=M.DPLUS, declare=Decl.declare, refused_cls=S.Refused)
        bad = main(None, 5, agent=M.Peek(), declare=Decl.declare, refused_cls=S.Refused, quiet=True)
        lazy = main(None, 5, agent=M.DPLUS, declare=lambda spec: spec, refused_cls=S.Refused, quiet=True)
        print("stand-in: reference passes:", good, "| peeking poison fails:", not bad, "| accept-everything declare fails:", not lazy)
        sys.exit(0 if (good and not bad and not lazy) else 1)
    sys.exit(0 if main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1) else 1)
