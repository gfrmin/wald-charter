"""
kit.py - judges an IMPLEMENTATION against the signed page. Author-side: lives in wald-charter, never in the builder's repo.

  python3 laws/kit.py --impl PATH_TO_src [--worlds 300] [--seed INT | --seed-file PATH]      (seed defaults to 1)
  CI passes --seed-file; the file is read and deleted, and the seed spent, before the implementation is imported (kit v0.14).

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
9. kit v0.11: CHARTER v0.2 (kit_counts.py, counts_check.py): what is learned between episodes - Globals, the After-act, Counts, S15's disclosure, E7, the public plate.
10. kit v0.12: SURFACE v0.2 (surface_check.py and its corpus through kit_surface.py; model.py's shapes, V2.13's digest and V2.8's Score through kit_counts.py K7); wald.law names charter-v0.2 and surface-v0.2.
11. kit v0.13: brief 008's questions (Q10-Q17) answered in the reference and pinned in the corpus; R9, R10 in kit_surface.py (a raw
    surrogate, a Score of tens of thousands of digits, the corpus's mutations against the reference's verdicts); K8, K9 in
    kit_counts.py (an unnamed Global value, realisability as v0's loop, a prefix falsifier at an ending outcome, the plate at an
    ending outcome, the implementation's plate read back); L5 in kit_library.py (wald.digest, wald.score, wald.e7 in public).
12. kit v0.14: the seed (kit_seed.py). Read from a file and deleted, never from the environment; every suite's seed derived
    from it one way and the kit's Worlds drawn before the implementation is imported; the wire's server gets no kit environment.
Exit code 0 = the implementation passes. Nothing else counts.
"""
import argparse, importlib, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_check as S
import kit_seed

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

def prepare(argv=None):
    """Everything the seed decides, decided before the implementation is in the process (kit v0.14): the file is read and
    deleted, each suite gets its own seed by a one-way hash, the kit's Worlds are drawn, and the master seed does not
    outlive this call. Returns (args, the suites' seeds, the Worlds)."""
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--worlds", type=int, default=300)
    g = ap.add_mutually_exclusive_group(); g.add_argument("--seed", type=int); g.add_argument("--seed-file")
    a = ap.parse_args(argv)
    if "KIT_SEED" in os.environ:
        raise SystemExit("kit v0.14: KIT_SEED is in the environment of the process that would import the implementation; pass --seed-file")
    seeds = kit_seed.suite_seeds(kit_seed.take(a.seed_file) if a.seed_file else (1 if a.seed is None else a.seed))
    a.seed = a.seed_file = None
    rng = random.Random(seeds.pop("kit")); worlds = [S.rand_world(rng) for _ in range(a.worlds)]
    return a, seeds, worlds

def load_agent(impl):
    sys.path.insert(0, os.path.abspath(impl))
    return Impl(importlib.import_module("wald.kit_adapter").make_agent())

def main():
    a, seeds, worlds = prepare()
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
    agent = load_agent(a.impl)
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
    if not kit_surface.main(a.impl, seeds["surface"]): ok = False
    import kit_wordle
    if not kit_wordle.main(a.impl, seeds["wordle"]): ok = False
    import kit_wordle_big
    if not kit_wordle_big.main(a.impl, seeds["wordle_big"]): ok = False
    import kit_think
    if not kit_think.main(a.impl, seeds["think"]): ok = False
    import kit_wordle_think
    if not kit_wordle_think.main(a.impl, seeds["wordle_think"]): ok = False
    import kit_library
    if not kit_library.main(a.impl, seeds["library"]): ok = False
    import kit_counts
    if not kit_counts.main(a.impl, seeds["counts"]): ok = False
    print("IMPLEMENTATION PASSES" if ok else "IMPLEMENTATION FAILS"); return 0 if ok else 1

if __name__ == "__main__": sys.exit(main())
