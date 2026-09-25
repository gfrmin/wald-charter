"""
kit_structural.py - kit v0.2: the parts of the page the four-method adapter cannot see.
Judges the real API named in INTERFACE.md ("The structural surface"). Called by kit.py; can be run alone:
    python3 laws/kit_structural.py --impl PATH_TO_src
ST1 surface (S1, E5)   ST2 seals (section 1)   ST3 inert Display (S1)   ST4 named refusals (section 1, S2, S4, S5, E3, S3)
ST5 single-use Obs (S2)   ST6 the episode loop, in the page's order (section 2, E3)
"""
import argparse, importlib, os, sys
from fractions import Fraction as F

ALLOWED_TOP = {"declare", "run", "Door", "report", "Display", "refusals",          # kit v0.1
               "load_pack", "from_json", "to_json", "law",                           # kit v0.10 (brief 006, Q5)
               "plate",                                                              # kit v0.11 (CHARTER v0.2)
               "digest", "score", "e7"}                                              # kit v0.13 (brief 009)
SRC = {"prior": "data", "utility": "elicited", "price": "elicited", "horizon": "elicited", "depth": "elicited"}

def spec(prior, T, O, N=1, d=1, **kw):
    s = {"prior": prior, "T": T, "O": O, "N": N, "d": d, "closed": True,
         "table_sources": {**SRC, "kernels": {k: ["data"] for k in O}}}
    s.update(kw); return s
def act(K, price, once=True, ends=None): return {"K": K, "price": price, "once": once, "ends": ends or {}}
AP_T = {"treat": {"sick": F(0), "well": F(-2)}, "leave": {"sick": F(-10), "well": F(0)}}
AP_K = {"sick": {"+": F(9, 10), "-": F(1, 10)}, "well": {"+": F(1, 5), "-": F(4, 5)}}
def appendix(price=F(1, 2), once=True, N=1, d=1): return spec({"sick": F(1, 5), "well": F(4, 5)}, AP_T, {"test": act(AP_K, price, once)}, N, d)

def run_all(impl_path):
    sys.path.insert(0, os.path.abspath(impl_path))
    W = importlib.import_module("wald"); R = importlib.import_module("wald.refusals")
    world_m = importlib.import_module("wald.world"); B = importlib.import_module("wald.belief")
    E = importlib.import_module("wald.episode"); D = importlib.import_module("wald.display"); Ob = importlib.import_module("wald.obs")
    results = []
    def check(tag, cond, note=""): results.append((tag, bool(cond), note))
    def guarded(tag, f):
        try: cond, note = f()
        except Exception as e: cond, note = False, f"raised {type(e).__name__}: {e}"
        check(tag, cond, note)
    def raises(exc, f):
        try: f()
        except exc: return True
        except Exception as e: return False
        return False
    def refusal_name(s):
        try: world_m.declare(s)
        except R.Refused as e: return e.name
        except Exception as e: return "raised " + type(e).__name__
        return "ACCEPTED"

    class Script(E.Door):
        "the author's door: plays back a script of raw outcomes and records what the loop asks of it"
        def __init__(self, outs): self.outs = list(outs); self.calls = []
        def outcome(self, a):
            self.calls.append(("outcome", a))
            if not self.outs: raise RuntimeError("the loop asked the door for more observations than the World allows")
            return self.outs.pop(0)
        def fire(self, a): self.calls.append(("fire", a))

    # ST1
    top = set(getattr(W, "__all__", ["<no __all__>"]))
    check("ST1 wald.__all__ exports nothing beyond " + str(sorted(ALLOWED_TOP)), top <= ALLOWED_TOP, str(sorted(top - ALLOWED_TOP)))
    # ST2
    w = world_m.declare(appendix()); b = B.prior(w)
    check("ST2 Belief cannot be constructed directly", raises(Exception, lambda: B.Belief()) and raises(Exception, lambda: B.Belief({"sick": F(1)})))
    check("ST2 Obs cannot be constructed directly", raises(Exception, lambda: Ob.Obs()) and raises(Exception, lambda: Ob.Obs("test", "+")))
    check("ST2 Display cannot be constructed directly", raises(Exception, lambda: D.Display()) and raises(Exception, lambda: D.Display("1/2")))
    pub = [a for a in dir(b) if not a.startswith("_")]
    check("ST2 a Belief has no public attributes", pub == [], str(pub))
    check("ST2 a Belief cannot be mutated", raises(Exception, lambda: setattr(b, "x", 1)))
    # ST3
    d = B.report(b)
    ops = {"<": lambda: d < 1, "<=": lambda: d <= 1, ">": lambda: d > 1, ">=": lambda: d >= 1, "==": lambda: d == 1, "!=": lambda: d != 1,
           "+": lambda: d + 1, "-": lambda: d - 1, "*": lambda: d * 2, "/": lambda: d / 2, "float": lambda: float(d), "int": lambda: int(d),
           "bool": lambda: bool(d), "hash": lambda: hash(d), "iter": lambda: iter(d), "len": lambda: len(d), "getitem": lambda: d[0]}
    alive = [k for k, f in ops.items() if not raises(TypeError, f)]
    check("ST3 a Display supports no operation (each raises TypeError)", alive == [], str(alive))
    check("ST3 a Display renders to text", isinstance(str(d), str) and len(str(d)) > 0)
    # ST4
    good = appendix()
    check("ST4 a lawful World is accepted", refusal_name(good) == "ACCEPTED", refusal_name(good))
    twin = appendix(); twin["O"]["test_copy"] = act(AP_K, F(1, 2)); twin["table_sources"]["kernels"]["test_copy"] = ["data"]; twin["N"] = 2
    check("ST4 two acts with identical kernels and private sources are accepted", refusal_name(twin) == "ACCEPTED", refusal_name(twin))
    def bad(**kw): s = appendix(); s.update(kw); return s
    cases = [("EMPTY_T", bad(T={})),
             ("PRIOR", bad(prior={"sick": F(1), "well": F(0)})), ("PRIOR", bad(prior={"sick": F(1, 5), "well": F(3, 5)})),
             ("KERNEL_ROW", bad(O={"test": act({"sick": {"+": F(9, 10), "-": F(1, 20)}, "well": AP_K["well"]}, F(1, 2))})),
             ("DEPTH", bad(d=0)), ("DEPTH", bad(d=2)),
             ("ZERO_EVIDENCE", {k: v for k, v in appendix().items() if k != "closed"}),
             ("TABLE_SOURCE", bad(table_sources={**SRC, "kernels": {"test": ["guessed"]}})),
             ("TABLE_SOURCE", bad(table_sources={k: v for k, v in SRC.items() if k != "prior"} | {"kernels": {"test": ["data"]}}))]
    cases.append(("PRICE", bad(O={"test": act(AP_K, F(-1, 2))})))
    cases.append(("TABLE_SHAPE", bad(T={"treat": {"sick": F(0)}, "leave": AP_T["leave"]})))                       # a utility missing a state
    cases.append(("TABLE_SHAPE", bad(O={"test": act({"sick": AP_K["sick"]}, F(1, 2))})))                          # a kernel missing a state
    cases.append(("TABLE_SHAPE", bad(O={"test": act(AP_K, F(1, 2), True, {"boom": {"sick": F(0), "well": F(0)}})})))  # an ending outcome the kernel cannot emit
    cases.append(("TABLE_SHAPE", bad(O={"test": act(AP_K, F(1, 2), True, {"+": {"sick": F(0)}})})))                # a u_end missing a state
    fresh_named = appendix(F(1, 2), False); fresh_named["sources"] = {"test": ["the_draw"]}
    cases.append(("SHARED_SOURCE", fresh_named))                                                                  # S2: two executions of a fresh act read it twice
    shared = dict(twin); shared["sources"] = {"test": ["the_draw"], "test_copy": ["the_draw"]}
    cases.append(("SHARED_SOURCE", shared))
    for want, s in cases:
        got = refusal_name(s); check(f"ST4 refused by name: {want}", got == want, "got " + got)
    ok_shared = dict(shared); ok_shared["components"] = ["the_draw"]
    check("ST4 a shared source that is a declared component of Omega is accepted", refusal_name(ok_shared) == "ACCEPTED", refusal_name(ok_shared))
    nob = {k: v for k, v in appendix().items() if k != "closed"}; nob["bottom"] = "well"   # 'well' has full support over + and -
    check("ST4 a World with a full-support bottom state is accepted", refusal_name(nob) == "ACCEPTED", refusal_name(nob))
    zero_k = {"sick": {"+": F(1), "-": F(0)}, "well": {"+": F(0), "-": F(1)}}
    nob2 = dict(nob); nob2["O"] = {"test": act(zero_k, F(1, 2))}
    check("ST4 refused by name: ZERO_EVIDENCE (bottom without full support)", refusal_name(nob2) == "ZERO_EVIDENCE", "got " + refusal_name(nob2))
    # ST5
    def st5():
        door = Script(["+"]); obs = door.observe("test"); b1 = B.condition(b, w, obs)
        exact = B.expect(b1, {"sick": F(1), "well": F(0)}) == F(9, 17)
        return exact and raises(R.ObsSpent, lambda: B.condition(b, w, obs)), f"posterior exact: {exact}"
    guarded("ST5 an Obs conditions exactly once; a second use raises ObsSpent", st5)
    # ST6
    def play(s_, outs): dr = Script(outs); return E.run(world_m.declare(s_), dr), dr
    for out, want in (("+", ("test", "treat")), ("-", ("test", "leave"))):
        def f(out=out, want=want):
            r, dr = play(appendix(), [out])
            return tuple(r.acts) == want and r.status == "TERMINAL" and r.paid == F(1, 2) and dr.calls[-1] == ("fire", want[1]), f"{r.acts} {r.status} {r.paid} {dr.calls}"
        guarded(f"ST6 appendix, door says {out}: acts {want}", f)
    def f():
        r, dr = play(appendix(F(1, 10), True, 2, 2), ["+"]); return tuple(r.acts) == ("test", "treat"), str(r.acts)
    guarded("ST6 a `once` act leaves the menu (after +, treat)", f)
    def f():
        r, dr = play(appendix(F(1, 10), False, 2, 2), ["+", "+"]); return tuple(r.acts)[:2] == ("test", "test") and r.paid == F(1, 5), f"{r.acts} {r.paid}"
    guarded("ST6 a `fresh` act may be repeated (after +, test again)", f)
    Kh = {"x": {"sx": F(1, 2), "sy": F(0), "blank": F(1, 2)}, "y": {"sx": F(0), "sy": F(1, 2), "blank": F(1, 2)}}
    H = spec({"x": F(1, 2), "y": F(1, 2)}, {"X": {"x": F(1), "y": F(0)}, "Y": {"x": F(0), "y": F(1)}}, {"peek": act(Kh, F(1, 10), False)}, N=2, d=1)
    def f():
        r, dr = play(H, ["blank", "blank"])
        return tuple(r.acts) == ("peek", "peek", "X") and r.paid == F(1, 5) and len([c for c in dr.calls if c[0] == "outcome"]) == 2, f"{r.acts} {r.paid}"
    guarded("ST6 the horizon binds: two blank peeks, then X (decide_min(d,n))", f)
    say = {f"say-{s_}": {w_: F(1 if w_ == s_ else 0) for w_ in "ab"} for s_ in "ab"}
    Kz = {"a": {"x": F(1), "y": F(0), "hit": F(0)}, "b": {"x": F(0), "y": F(1), "hit": F(0)}}
    Z = spec({"a": F(1, 2), "b": F(1, 2)}, say, {"probe": act(Kz, F(1, 10), True, {"hit": {"a": F(100), "b": F(100)}})})
    def f():
        r, dr = play(Z, ["hit"])
        return r.status == "WORLD_FALSIFIED" and r.paid == F(1, 10) and not any(c[0] == "fire" for c in dr.calls), f"{r.status} {r.paid}"
    guarded("ST6 a zero-mass outcome falsifies the World BEFORE it can end the episode; the price is already paid", f)
    Ke = {"a": {"hit": F(1), "miss": F(0)}, "b": {"hit": F(0), "miss": F(1)}}
    Wn = spec({"a": F(1, 2), "b": F(1, 2)}, say, {"probe": act(Ke, F(1, 10), True, {"hit": {"a": F(1), "b": F(1)}})})
    def f():
        r, dr = play(Wn, ["hit"]); return r.status == "ENDED" and B.expect(r.final, {"a": F(1), "b": F(0)}) == F(1), f"{r.status}"
    guarded("ST6 an ending outcome is conditioned on, then ends the episode", f)
    return results

def main(impl_path):
    try: results = run_all(impl_path)
    except Exception as e:
        import traceback; traceback.print_exc(); print("STRUCTURAL: could not run -", type(e).__name__, e); return False
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"structural: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); sys.exit(0 if main(ap.parse_args().impl) else 1)
