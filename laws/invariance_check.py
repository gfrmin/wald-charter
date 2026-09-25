"""
invariance_check.py - a gate check for SURFACE v0.2 and CHARTER v0.2: every equivalence the theory respects leaves a
lawful World lawful - with the same first act, the same value, the same belief over the original Globals - and leaves a
refused World refused by the same name. The equivalences: renaming every name; padding with a one-valued local or Global
component, and removing one; splitting a Global value into twins; and (kit v0.13) a component value the prior does not
name, which is not a state (QUESTIONS.md Q11). Three refusal rules were beaten by exactly these re-spellings in attack
sessions (S15's refusal and prior rules, SURFACE K19); this runs before any attack does. Kit v0.13 adds the text around
names: comments removed, moved or added, blank lines, a byte-order mark - each changes no pack's verdict, or changes
every pack's to one refusal name (QUESTIONS.md Q16).
"""
import ast, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from fractions import Fraction as F
import counts_check as C, surface_check as SC
from spec_check import REF, Refused

def remap(W, fl=lambda l: l, fg=lambda g: g, fname=lambda x: x, locals_=None, globals_=None, pg=None, pl=None):
    "rebuild a World under maps of locals, Globals and names"
    st = lambda k: (fl(k[0]), fg(k[1]))
    ending = {f"end:{k}={o}": f"end:{fname(k)}={fname(o)}" for k, a in W["O"].items() for o in a.get("ends", ())}
    fend = lambda e: ending.get(e) or fname(e)          # an ending end renames its act and its outcome, not the string (kit v0.13)
    rec = lambda r: (tuple((fname(a), fname(o)) for a, o in r[0]), None if r[1] is None else fend(r[1]), None if r[2] is None else fname(r[2]))
    V = {"locals": locals_ if locals_ is not None else [(fname(c), [fname(v) for v in vs]) for c, vs in W["locals"]],
         "globals": globals_ if globals_ is not None else [(fname(c), [fname(v) for v in vs]) for c, vs in W["globals"]],
         "prior_global": pg if pg is not None else {fg(g): p for g, p in W["prior_global"].items()},
         "prior_local": pl if pl is not None else {fg(g): {fl(l): p for l, p in row.items()} for g, row in W["prior_local"].items()},
         "T": {fname(t): {st(k): u for k, u in r.items()} for t, r in W["T"].items()},
         "O": {fname(k): {**a, "K": {st(s): {fname(o): p for o, p in row.items()} for s, row in a["K"].items()},
                          **({"ends": {fname(o) for o in a["ends"]}} if "ends" in a else {}),
                          **({"u_end": {fname(o): {st(s): u for s, u in ue.items()} for o, ue in a["u_end"].items()}} if "u_end" in a else {})} for k, a in W["O"].items()},
         "N": W["N"], "d": W["d"]}
    if W.get("after"):
        V["after"] = {"K": {fend(e): {st(s): {fname(o): p for o, p in row.items()} for s, row in K.items()} for e, K in W["after"]["K"].items()},
                      "price": W["after"]["price"], "name": fname(W["after"].get("name", "after"))}
    if W.get("counts") is not None and "counts_sha" in W:
        c = Counter({rec(r): n for r, n in W["counts"].items()}); fs = [rec(f) for f in W.get("falsifiers", [])]
        V["counts"] = c; V["counts_sha"] = C.counts_sha(c, fs); V["score"] = C.loo_score(V, c, fs)
        if fs: V["falsifiers"] = fs
    return V

def deep(f):
    "apply a renaming to a name, or element by element to a product outcome (a tuple of names)"
    return lambda x: tuple(deep(f)(v) for v in x) if isinstance(x, tuple) else f(x)

def rename(W):
    f = deep(lambda x: x + "~")
    return remap(W, fl=lambda l: tuple(f(v) for v in l), fg=lambda g: tuple(f(v) for v in g), fname=f), (lambda g: tuple(v[:-1] for v in g))

HOSTILE = ['"', "\\", "\t", "=", ":", "é", "中", "😀", "\x7f", " ", "/", "\x01"]
def hostile(W):
    """rename every name with a suffix from the characters that meet the page's own syntax: quotes, backslashes, control
    characters, '=' and ':' (the ending end's syntax), non-ASCII and astral characters (attack session 4, 3.1 and 4.1).
    Only what a stated rule forbids is avoided: CR and surrogates (V2.11), and a terminal beginning 'end:' (V2.6)."""
    names = sorted({x for c, vs in W["locals"] + W["globals"] for x in [c] + list(vs)} | set(W["T"]) | set(W["O"])
                   | {v for a in W["O"].values() for row in a["K"].values() for o in row for v in (o if isinstance(o, tuple) else (o,))}
                   | ({W["after"].get("name", "after")} | {o for K in W["after"]["K"].values() for row in K.values() for o in row} if W.get("after") else set()))
    m = {x: x + HOSTILE[i % len(HOSTILE)] + str(i) for i, x in enumerate(names)}
    f = deep(lambda x: m.get(x, x))
    back = {v: k for k, v in m.items()}
    return remap(W, fl=lambda l: tuple(f(v) for v in l), fg=lambda g: tuple(f(v) for v in g), fname=f), (lambda g: tuple(back.get(v, v) for v in g))

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
    for k in V["O"]:
        V["O"][k]["K"].update({(l, g1): r for (l, g), r in list(V["O"][k]["K"].items()) if g == g0})
        for o, ue in V["O"][k].get("u_end", {}).items(): ue.update({(l, g1): u for (l, g), u in list(ue.items()) if g == g0})
    if V.get("after"):
        for e in V["after"]["K"]: V["after"]["K"][e].update({(l, g1): r for (l, g), r in list(V["after"]["K"][e].items()) if g == g0})
    if V.get("counts") is not None and "counts_sha" in V: V["score"] = C.loo_score(V, V["counts"], V.get("falsifiers", []))
    return V, (lambda g: (g[0].rstrip("'"),) if g[0].endswith("'") else g)

def verdict(W):
    try:
        C.refuse(W); SC.check(SC.to_pack_v02(W)); return "ok"
    except (Refused, SC.Refused) as e: return getattr(e, "name", None) or str(e).split(":")[0]
    except Exception as e: return f"raised {type(e).__name__}: {e}"

def summary(W, back):
    "the first act, its value, and the belief over the original Globals, after the plate's evidence"
    ew = C.episode_world(W, C.evidence(W)); v, a = REF.solve(ew["prior"], ew, ew["N"])
    pg = Counter()
    for g, p in C.post_global(W, C.evidence(W)).items(): pg[back(g)] += p
    return v, a, dict(pg)

def unnamed_global(W):
    """a value of the first Global component that P(Global) does not name: not a state (V2.3, V2.4; SURFACE v0 K10), so
    nothing changes (QUESTIONS.md Q11)"""
    if not W["globals"]: return None, None
    (c, vs), *rest = W["globals"]
    return remap(W, globals_=[(c, vs + [vs[0] + "~unnamed"])] + rest), (lambda g: g)

def unnamed_local(W):
    "a value of the first local component that no row of P(local | Global) names: not a state, so nothing changes"
    if not W["locals"]: return None, None
    (c, vs), *rest = W["locals"]
    return remap(W, locals_=[(c, vs + [vs[0] + "~unnamed"])] + rest), (lambda g: g)

TRANSFORMS = [("rename", rename), ("rename with hostile characters", hostile), ("pad a local", pad_local), ("pad a Global", pad_global), ("remove a one-valued local", unpad), ("split a Global into twins", twin),
              ("a Global value the prior does not name", unnamed_global), ("a local value the prior does not name", unnamed_local)]

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

# ---- kit v0.13: the text around names
CODING = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)", re.M)

def _stmt_lines(text):
    try: return sorted({st.lineno for st in ast.parse(text).body}), sorted({st.end_lineno for st in ast.parse(text).body})
    except (SyntaxError, ValueError, UnicodeError): return None, None

def text_transforms(text):
    """(label, text) pairs that change only the text around names: comments, blank lines, a byte-order mark. A pack holding
    anything a reader might take for a coding declaration is left out of the comment edits, since moving one line past
    another changes whether it is one: which comment is a coding declaration is QUESTIONS.md Q16, for SURFACE v0.3."""
    L = text.split("\n"); starts, ends = _stmt_lines(text)
    comment = lambda l: l.lstrip(" \t").startswith("#")
    if not CODING.search(text):
        yield "comments removed", "\n".join(l for l in L if not comment(l))
        yield "comments moved to the end", "\n".join([l for l in L if not comment(l)] + [l for l in L if comment(l)])
    if starts:
        yield "a comment line before every declaration", "\n".join(("# a comment\n" if i + 1 in starts else "") + l for i, l in enumerate(L))
        yield "a blank line before every declaration", "\n".join(("\n" if i + 1 in starts else "") + l for i, l in enumerate(L))
        yield "a comment after every declaration", "\n".join(l + ("  # a comment" if i + 1 in ends and not comment(l) else "") for i, l in enumerate(L))
    yield "a byte-order mark", "\ufeff" + text

def pack_verdict(text):
    here = os.path.dirname(os.path.abspath(__file__)); okd = os.path.join(here, "packs/ok")
    try: return ("ok", SC.check(text, {}, okd), SC.census(text, {}, okd))
    except SC.Refused as e: return e.name
    except Exception as e: return f"raised {type(e).__name__}"

def text_invariance():
    """the text around names changes no verdict, or changes every pack's to one refusal name: for each edit, either every
    pack keeps its World, census or refusal, or every edited pack is refused by the same name (QUESTIONS.md Q16: which
    name a byte-order mark gets is SURFACE v0.3's; that it gets one, whatever follows it, is not)"""
    import mutations as MU
    by, n = {}, 0
    for name, text in MU.corpus():
        before = pack_verdict(text)
        for label, t in text_transforms(text):
            n += 1; by.setdefault(label, []).append((name, before, pack_verdict(t)))
    fails = []
    for label, rows in by.items():
        if all(a == b for _, a, b in rows): continue
        after = {b if isinstance(b, str) else "a World" for _, _, b in rows}
        if len(after) == 1 and not (after & {"a World"}) and not any(x.startswith("raised") for x in after): continue
        changed = [(nm, a if isinstance(a, str) else "a World", b if isinstance(b, str) else "a World") for nm, a, b in rows if a != b]
        fails.append(f"'{label}' changes {len(changed)} verdicts to {sorted(after)[:4]}; the first: {changed[0]}")
    return n, fails

def main():
    fails, n = [], 0
    for label, W in worlds():
        base = summary(W, lambda g: g)
        for tname, T in TRANSFORMS:
            try:
                V, back = T(W)
                if V is None: continue
                n += 1; v = verdict(V)
                if v != "ok": fails.append(f"{label}: '{tname}' turns a lawful World into one refused {v}"); continue
                got = summary(V, back)
            except Exception as e: fails.append(f"{label}: '{tname}' makes the reference raise {type(e).__name__}: {e}"); continue
            if got[0] != base[0] or got[2] != base[2]: fails.append(f"{label}: '{tname}' changes the value or the belief ({base[0]} -> {got[0]})")
    for name, W in poisons():
        for tname, T in TRANSFORMS:
            try:
                V, _ = T(W)
                if V is None: continue
                if name == "PLATE" and V.get("counts_sha"): V["counts_sha"] = "0" * 64      # keep the broken digest broken
                n += 1; v = verdict(V)
            except Exception as e: v = f"raised {type(e).__name__}: {e}"
            if v != name: fails.append(f"a World refused {name}: '{tname}' makes it {v}")
    tn, tf = text_invariance(); n += tn; fails += tf
    kinds = {}
    for f in fails: kinds.setdefault(f.split("'")[1] if "'" in f else f[:40], []).append(f)
    for k, fs in kinds.items(): print(f"FAIL {len(fs)} x  {fs[0][:230]}")
    print(f"invariance: {n} transformed Worlds and packs; " + ("INVARIANCE PASSES" if not fails else f"INVARIANCE FAILS ({len(fails)})"))
    return not fails

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
