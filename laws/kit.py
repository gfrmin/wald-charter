"""
kit.py - judges an IMPLEMENTATION against the signed page. Author-side: lives in wald-charter, never in the builder's repo.

  python3 laws/kit.py --impl PATH_TO_src [--worlds 300] [--seed INT]      (seed defaults to $KIT_SEED, else 1)

1. Kit integrity: the oracle passes every check and every poison is killed (the same test the page passed).
2. The implementation, through its adapter `wald.kit_adapter.make_agent()` (see INTERFACE.md), must pass
   C1-C11, S5 and E2 (the oracle's act at every reachable (b, M, n)) on worlds drawn from a seed the builder never sees,
   on forced-tie variants of those worlds (J3), and on the appendix vector.
4. kit v0.3: the SURFACE page (kit_surface.py): the pack corpus, and random Worlds printed as packs and read back.
3. kit v0.1: the structural surface (kit_structural.py): seals, inert Display, named refusals, single-use Obs, the loop's order.
5. kit v0.7: the think act (kit_think.py) under CHARTER v0.1: step's five buckets, C12-C20, E2 on the pinned Worlds, refusals by name.
6. kit v0.8: SURFACE v0.1 (the corpus grows: depth_plus, think, cost, rate, score), RATE for r < 0, C19 on the reference only.
7. kit v0.9: the think act on Wordle (kit_wordle_think.py, wordle_meta_oracle.py): two adaptive packs, the oracle's buckets and costs, the E3 curves.
8. kit v0.10: wald as a library (kit_library.py): the public names, wald.law against the lock, the wire spec, tools/serve.py over JSON lines.
Exit code 0 = the implementation passes. Nothing else counts.
"""
import argparse, importlib, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_check as S

class Impl:
    "Wraps the builder's agent; translates its WorldFalsified into the kit's."
    name = "implementation"
    def __init__(self, agent): self.a = agent
    def _call(self, f, *args):
        try: return f(*args)
        except Exception as e:
            if type(e).__name__ == "WorldFalsified": raise S.WorldFalsified(str(e))
            raise
    def push(self, b, K): return self._call(self.a.push, b, K)
    def condition(self, b, K, o): return self._call(self.a.condition, b, K, o)
    def expect(self, b, f): return self._call(self.a.expect, b, f)
    def decide(self, b, world, n, used=frozenset()): return self._call(self.a.decide, b, world, n, used)

def tie_variants(world):
    "J3 is part of the semantics, and random worlds almost never tie. These force exact ties; the first menu entry must win."
    F = S.F; out = []
    T = dict(world["T"]); T["t_copy"] = dict(world["T"]["t0"]); T["t_copy2"] = dict(world["T"]["t2"])
    out.append(S.clone(world, T=T))                                   # duplicated terminal acts
    flat = {w: {"o0": F(1, 2), "o1": F(1, 2)} for w in world["prior"]}
    O = dict(world["O"]); O["k_flat"] = {"K": flat, "price": F(0), "once": True, "ends": {}}
    out.append(S.clone(world, O=O))                                   # a free, uninformative look: ties with stopping
    O = dict(world["O"]); O["k0_copy"] = dict(world["O"]["k0"])
    out.append(S.clone(world, O=O))                                   # duplicated observational act
    return out

class TieLast(S.Ref):
    "poison: on a tie, the LAST menu entry wins"
    name = "ties go to the last menu entry (violates J3)"
    def solve(self, b, world, n, used=frozenset()):
        best, arg = None, None
        for t, u in world["T"].items():
            v = self.expect(b, u)
            if best is None or v >= best: best, arg = v, t
        if n > 0:
            for k in self.menu(world, used):
                v = self.q(b, world, k, n, used)
                if v >= best: best, arg = v, k
        return best, arg

def show(world):
    fr = lambda d: {str(k): (fr(v) if isinstance(v, dict) else str(v)) for k, v in d.items()}
    return fr({"prior": world["prior"], "T": world["T"], "O": {k: {"K": s["K"], "price": s["price"], "once": str(s["once"]), "ends": s["ends"]} for k, s in world["O"].items()}})

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--worlds", type=int, default=300)
    ap.add_argument("--seed", type=int, default=int(os.environ.get("KIT_SEED") or 1)); a = ap.parse_args()
    ok = True
    # 1. kit integrity (fixed public seed)
    rng = random.Random(20260920); ws = [S.rand_world(rng) for _ in range(60)]
    if any(S.run(S.REF, ws).values()): print("KIT BROKEN: the oracle fails its own checks"); return 2
    for p in S.POISONS:
        if not any(S.run(p, ws).values()): print("KIT BROKEN: poison survives:", p.name); return 2
    ties = [v for w in ws[:30] for v in tie_variants(w)]
    if not all(S.same_acts(S.REF, v, S.N) for v in ties): print("KIT BROKEN: the oracle fails the tie worlds"); return 2
    if all(S.same_acts(TieLast(), v, S.N) for v in ties): print("KIT BROKEN: the tie-breaking poison survives"); return 2
    print("kit integrity: oracle clean,", len(S.POISONS) + 1, "poisons killed")
    # 2. the implementation
    sys.path.insert(0, os.path.abspath(a.impl))
    agent = Impl(importlib.import_module("wald.kit_adapter").make_agent())
    rng = random.Random(a.seed); worlds = [S.rand_world(rng) for _ in range(a.worlds)]
    worlds += [S.appendix(S.F(1, 2), True), S.appendix(S.F(1, 10), True), S.appendix(S.F(1, 10), False)]
    fails = {}
    for i, w in enumerate(worlds):
        random_world = i < a.worlds
        for cname, check in S.CHECKS:
            if not random_world and cname != "E2": continue          # vectors: differential only
            try: good = check(agent, w, random.Random(1000 + i))
            except S.WorldFalsified: good = False
            except Exception as e: good = False; fails.setdefault(cname + " (raised " + type(e).__name__ + ")", w)
            if not good: fails.setdefault(cname, w)
    for w in worlds[:a.worlds]:
        for v in tie_variants(w):
            if not S.same_acts(agent, v, S.N): fails.setdefault("E2 on a forced tie (J3: first menu entry, terminal acts first)", v)
    if fails:
        ok = False
        for cname, w in fails.items(): print(f"FAIL {cname}\n  first failing world: {show(w)}")
    import kit_structural
    if not kit_structural.main(a.impl): ok = False
    import kit_surface
    if not kit_surface.main(a.impl, a.seed): ok = False
    import kit_wordle
    if not kit_wordle.main(a.impl, a.seed): ok = False
    import kit_wordle_big
    if not kit_wordle_big.main(a.impl, a.seed): ok = False
    import kit_think
    if not kit_think.main(a.impl, a.seed): ok = False
    import kit_wordle_think
    if not kit_wordle_think.main(a.impl, a.seed): ok = False
    import kit_library
    if not kit_library.main(a.impl, a.seed): ok = False
    print("IMPLEMENTATION PASSES" if ok else "IMPLEMENTATION FAILS"); return 0 if ok else 1

if __name__ == "__main__": sys.exit(main())
