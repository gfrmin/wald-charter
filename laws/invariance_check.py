"""
invariance_check.py - a gate check for SURFACE v0.2 and CHARTER v0.2: every equivalence the theory respects leaves a
lawful World lawful - with the same first act, the same value, the same belief over the original Globals - and leaves a
refused World refused by the same name. The equivalences: renaming every name; padding with a one-valued local or Global
component, and removing one; splitting a Global value into twins. Three refusal rules were beaten by exactly these
re-spellings in attack sessions (S15's refusal and prior rules, SURFACE K19); this runs before any attack does.
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from fractions import Fraction as F
import counts_check as C, surface_check as SC
from spec_check import REF, Refused

def remap(W, fl=lambda l: l, fg=lambda g: g, fname=lambda x: x, locals_=None, globals_=None, pg=None, pl=None):
    "rebuild a World under maps of locals, Globals and names"
    st = lambda k: (fl(k[0]), fg(k[1]))
    rec = lambda r: (tuple((fname(a), fname(o)) for a, o in r[0]), None if r[1] is None else fname(r[1]), None if r[2] is None else fname(r[2]))
    V = {"locals": locals_ if locals_ is not None else [(fname(c), [fname(v) for v in vs]) for c, vs in W["locals"]],
         "globals": globals_ if globals_ is not None else [(fname(c), [fname(v) for v in vs]) for c, vs in W["globals"]],
         "prior_global": pg if pg is not None else {fg(g): p for g, p in W["prior_global"].items()},
         "prior_local": pl if pl is not None else {fg(g): {fl(l): p for l, p in row.items()} for g, row in W["prior_local"].items()},
         "T": {fname(t): {st(k): u for k, u in r.items()} for t, r in W["T"].items()},
         "O": {fname(k): {**a, "K": {st(s): {fname(o): p for o, p in row.items()} for s, row in a["K"].items()}} for k, a in W["O"].items()},
         "N": W["N"], "d": W["d"]}
    if W.get("after"):
        V["after"] = {"K": {fname(e): {st(s): {fname(o): p for o, p in row.items()} for s, row in K.items()} for e, K in W["after"]["K"].items()},
                      "price": W["after"]["price"], "name": fname(W["after"].get("name", "after"))}
    if W.get("counts") is not None and "counts_sha" in W:
        c = Counter({rec(r): n for r, n in W["counts"].items()}); fs = [rec(f) for f in W.get("falsifiers", [])]
        V["counts"] = c; V["counts_sha"] = C.counts_sha(c, fs); V["score"] = C.loo_score(V, c, fs)
        if fs: V["falsifiers"] = fs
    return V

def rename(W):
    f = lambda x: x + "~"
    return remap(W, fl=lambda l: tuple(f(v) for v in l), fg=lambda g: tuple(f(v) for v in g), fname=f), (lambda g: tuple(v[:-1] for v in g))

def pad_local(W):
    L = W["locals"] + [("pad", ["only"])]
    return remap(W, fl=lambda l: l + ("only",), locals_=L, pl={g: {l + ("only",): p for l, p in row.items()} for g, row in W["prior_local"].items()}), (lambda g: g)

def pad_global(W):
    G = W["globals"] + [("padg", ["only"])]
    return remap(W, fg=lambda g: g + ("only",), globals_=G, pg={g + ("only",): p for g, p in W["prior_global"].items()},
                 pl={g + ("only",): row for g, row in W["prior_local"].items()}), (lambda g: g[:-1])

def unpad(W):
    "remove every one-valued local component (the direction that refused K19's monitor)"
    keep = [i for i, (c, vs) in enumerate(W["locals"]) if len(vs) > 1]
    if len(keep) == len(W["locals"]): return None, None
    cut = lambda l: tuple(l[i] for i in keep)
    return remap(W, fl=cut, locals_=[W["locals"][i] for i in keep], pl={g: {cut(l): p for l, p in row.items()} for g, row in W["prior_local"].items()}), (lambda g: g)

def twin(W):
    gs = C.vals(W["globals"])
    if not gs or gs == [()]: return None, None
    g0 = gs[0]; name, vs = W["globals"][0]; tw = vs + [vs[0] + "'"] if len(W["globals"]) == 1 else None
    if tw is None: return None, None
    V = remap(W); V["globals"] = [(name, tw)]; g1 = (vs[0] + "'",)
    V["prior_global"] = dict(V["prior_global"]); half = V["prior_global"][g0] / 2; V["prior_global"][g0] = half; V["prior_global"][g1] = half
    V["prior_local"] = dict(V["prior_local"]); V["prior_local"][g1] = dict(V["prior_local"][g0])
    for t in V["T"]: V["T"][t].update({(l, g1): u for (l, g), u in list(V["T"][t].items()) if g == g0})
    for k in V["O"]: V["O"][k]["K"].update({(l, g1): r for (l, g), r in list(V["O"][k]["K"].items()) if g == g0})
    if V.get("after"):
        for e in V["after"]["K"]: V["after"]["K"][e].update({(l, g1): r for (l, g), r in list(V["after"]["K"][e].items()) if g == g0})
    if V.get("counts") is not None and "counts_sha" in V: V["score"] = C.loo_score(V, V["counts"], V.get("falsifiers", []))
    return V, (lambda g: (g[0].rstrip("'"),) if g[0].endswith("'") else g)

def verdict(W):
    try:
        C.refuse(W); SC.check(SC.to_pack_v02(W)); return "ok"
    except (Refused, Exception) as e: return getattr(e, "name", None) or str(e).split(":")[0]

def summary(W, back):
    "the first act, its value, and the belief over the original Globals, after the plate's evidence"
    ew = C.episode_world(W, C.evidence(W)); v, a = REF.solve(ew["prior"], ew, ew["N"])
    pg = Counter()
    for g, p in C.post_global(W, C.evidence(W)).items(): pg[back(g)] += p
    return v, a, dict(pg)

TRANSFORMS = [("rename", rename), ("pad a local", pad_local), ("pad a Global", pad_global), ("remove a one-valued local", unpad), ("split a Global into twins", twin)]

def worlds():
    here = os.path.dirname(os.path.abspath(__file__)); out = []
    for fn in sorted(os.listdir(os.path.join(here, "packs/ok"))):
        t = open(os.path.join(here, "packs/ok", fn), encoding="utf-8", newline="").read()
        if any(k in t for k in ("globals(", "after(", "counts(")):
            out.append((fn, SC.check(t, {}, os.path.join(here, "packs/ok"))))
    rng = random.Random(5)
    while len(out) < 40:
        W = C.rand_world(rng)
        try: C.refuse(W)
        except Refused: continue
        out.append((f"random-{len(out)}", W))
    return out

def poisons():
    "semantic refusals as Worlds, which a re-spelling must not rescue"
    A = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    out = [("GLOBAL", C.paid_global_world())]
    Wa = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); del Wa["after"]["K"]["abstain"]; out.append(("AFTER", Wa))
    Wp = dict(A); c = Counter([C.rec("a1", "a1", "say a1")]); Wp["counts"] = c; Wp["counts_sha"] = "0" * 64; Wp["score"] = C.loo_score(A, c); out.append(("PLATE", Wp))
    return out

def main():
    fails, n = [], 0
    for label, W in worlds():
        base = summary(W, lambda g: g)
        for tname, T in TRANSFORMS:
            V, back = T(W)
            if V is None: continue
            n += 1; v = verdict(V)
            if v != "ok": fails.append(f"{label}: '{tname}' turns a lawful World into one refused {v}"); continue
            got = summary(V, back)
            if got[0] != base[0] or got[2] != base[2]: fails.append(f"{label}: '{tname}' changes the value or the belief ({base[0]} -> {got[0]})")
    for name, W in poisons():
        for tname, T in TRANSFORMS:
            V, _ = T(W)
            if V is None: continue
            if name == "PLATE" and V.get("counts_sha"): V["counts_sha"] = "0" * 64      # keep the broken digest broken
            n += 1; v = verdict(V)
            if v != name: fails.append(f"a World refused {name}: '{tname}' makes it {v}")
    for f in fails[:12]: print("FAIL", f)
    print(f"invariance: {n} transformed Worlds; " + ("INVARIANCE PASSES" if not fails else f"INVARIANCE FAILS ({len(fails)})"))
    return not fails

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
