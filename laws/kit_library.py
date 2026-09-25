"""
kit_library.py - kit v0.10: wald as a library other programs consume (brief 006), judged from outside the package.
  python3 laws/kit_library.py --impl PATH_TO_src [--seed INT]
L1  `import wald` exposes declare, run, Door, report, Display, refusals, load_pack, from_json, to_json, law; `wald.law`
    names the signed tags and the kit this package conforms to, and they equal the lock the cage judges under.
L2  `wald.from_json` reads the wire spec (INTERFACE's dict with every rational written "p/q"), `wald.declare` accepts it,
    and `wald.run` against a scripted Door reproduces CHARTER v0.1's Appendix A and B episodes: acts, prices, thought,
    S7 buckets, and a final belief that `to_json` prints as rationals.
L3  `wald.load_pack(text, data_dir)` elaborates a pack exactly as the reference checker does.
L4  the wire: `tools/serve.py` spoken to over stdin/stdout in JSON lines (API.md); the kit is the door at the other end
    and the result it receives equals the in-process one, refusals arrive by name, and an unknown op is a refusal not a
    crash.
L5  kit v0.13 (brief 009): a host shipping Counts needs no kit. `wald.digest(counts, falsifiers)` is V2.13's digest;
    `wald.score(world, counts, falsifiers)` is V2.8's Score written as a pack writes it, "p/q", however many digits;
    `wald.e7(world, counts)` is E7's lines as a Display. A pack written from these alone - the refit of attack session 5,
    and appendix A shipping 300 records, whose Score has tens of thousands of digits - loads and declares.
Every rational on the wire is a string "p/q"; every message one JSON object per line.
"""
import argparse, importlib, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction as F
import spec_check as S, surface_check as R, meta_check as M

HERE = os.path.dirname(os.path.abspath(__file__))

def rq(x): return str(F(x))

def wire_spec(w, sources=None):
    "an INTERFACE World dict as the wire writes it: rationals as 'p/q', table_sources given"
    def enc(v):
        if isinstance(v, F): return rq(v)
        if isinstance(v, dict): return {str(k): enc(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)): return [enc(x) for x in v]
        return v
    spec = enc({k: v for k, v in w.items()})
    spec["closed"] = True
    spec["table_sources"] = sources or {"prior": "data", "utility": "elicited", "price": "elicited", "horizon": "elicited",
                                        "depth": "elicited", "kernels": {k: ["data"] for k in w["O"]}}
    if "dplus" in w:
        spec["table_sources"].update({"dplus": "elicited", "fraction": "elicited", "cost": "elicited", "rate": "elicited"})
    return spec

def scripted(wald, outcomes):
    "a wald.Door that answers each observational act from a script, in order"
    class D(wald.Door):
        def __init__(self): self.fired = []; self.i = 0
        def outcome(self, act): o = outcomes[self.i]; self.i += 1; return o
        def fire(self, act): self.fired.append(act)
    return D()

def lock_tags(impl):
    lock = os.path.join(os.path.dirname(os.path.abspath(impl)), "cage", "charter.lock")
    tags = {}
    if os.path.exists(lock):
        for line in open(lock):
            if line.startswith("TAG="): tags["kit"] = line.strip().split("=", 1)[1]
    return tags

def main(impl, seed=1):
    results = []
    def check(tag, cond, note=""): results.append((tag, bool(cond), note))
    sys.path.insert(0, os.path.abspath(impl))
    try:
        wald = importlib.import_module("wald")
    except Exception as e:
        print("FAIL L1: import wald:", type(e).__name__, e); return False
    import types
    names = ["declare", "run", "Door", "report", "Display", "refusals", "load_pack", "from_json", "to_json", "law", "plate"]
    check("L1 wald exposes " + ", ".join(names), all(hasattr(wald, n) for n in names), f"missing {[n for n in names if not hasattr(wald, n)]}")
    if not all(hasattr(wald, n) for n in names):
        return report(results)
    # kit v0.13: three functions, callable - not submodules that happen to be imported by then (kit v0.13 found `wald.digest` so)
    fns = ["digest", "score", "e7"]; lack = [n for n in fns if not callable(getattr(wald, n, None)) or isinstance(getattr(wald, n, None), types.ModuleType)]
    check("L1 wald exposes the functions digest, score, e7 (kit v0.13)", not lack, f"not functions of wald: {lack}")
    law = wald.law
    check("L1 wald.law names the newest signed pages, charter-v0.2 and surface-v0.2, and the kit tag of the lock (brief 007, Q7)", law.get("charter") == "charter-v0.2" and law.get("surface") == "surface-v0.2" and law.get("kit") == lock_tags(impl).get("kit"), f"got {law}, lock {lock_tags(impl)}")
    # L2: appendix A and B through the wire spec and a scripted door
    for name, w, script, want in (("A", M.vector_A(), ["+"], ("test", "treat")), ("B", M.vector_B(), ["y", "+"], ("scan", "test", "treat"))):
        spec = wald.from_json(json.dumps(wire_spec(w)))
        world = wald.declare(spec)
        door = scripted(wald, script)
        r = wald.run(world, door)
        ref_w = w; b = ref_w["prior"]; a, how, paid = M.DPLUS.step(b, ref_w, ref_w["N"])
        check(f"L2 appendix {name}: acts {want}", tuple(r.acts) == want, f"got {tuple(r.acts)}")
        check(f"L2 appendix {name}: thought {paid} and bucket {how} at the root", r.thought == paid and r.steps.get("think") == 1, f"thought {r.thought}, steps {dict(r.steps)}")
        final = json.loads(wald.to_json(r, world))
        check(f"L2 appendix {name}: to_json prints paid as p/q and the belief only as report's Display", final.get("paid") == rq(r.paid) and final.get("final") == str(wald.report(r.final, world)) and isinstance(final.get("final"), str), f"got {str(final)[:160]}")
    # L3: a pack through load_pack
    okd = os.path.join(HERE, "packs", "ok"); text = open(os.path.join(okd, "appendix_think.py")).read()
    got = wald.load_pack(text, okd); ref = R.check(text, {}, okd)
    check("L3 load_pack elaborates appendix_think.py as the reference does", all(got.get(k) == ref.get(k) for k in ("prior", "T", "O", "N", "d", "dplus", "fraction", "rate", "ops")), "differs")
    # L5: a host shipping Counts needs no kit (kit v0.13)
    if not lack: _l5(wald, check)
    else: check("L5 a host shipping Counts needs no kit", False, "wald.digest, wald.score and wald.e7 are not all functions")
    # L4: the wire
    root = os.path.dirname(os.path.abspath(impl)); serve = os.path.join(root, "tools", "serve.py")
    if not os.path.exists(serve):
        check("L4 tools/serve.py exists", False, "no tools/serve.py")
        return report(results)
    env = dict(os.environ, PYTHONPATH=os.path.abspath(impl))
    p = subprocess.Popen([sys.executable, serve], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=root)
    def send(obj): p.stdin.write(json.dumps(obj) + "\n"); p.stdin.flush()
    def recv():
        line = p.stdout.readline()
        if not line: raise RuntimeError("server closed: " + p.stderr.read()[-400:])
        return json.loads(line)
    try:
        send({"op": "hello"}); h = recv()
        check("L4 hello answers with wald.law", h.get("law") == law, f"got {h}")
        send({"op": "declare", "spec": wire_spec(M.vector_B())}); d = recv()
        check("L4 declare returns a world id", d.get("ok") is True and "world" in d, f"got {d}")
        wid = d.get("world")
        send({"op": "run", "world": wid}); script = iter(["y", "+"]); fired = []; msg = recv(); n = 0
        while "result" not in msg and n < 20:
            n += 1
            if "observe" in msg: send({"outcome": next(script), "id": msg.get("id")})
            elif "fire" in msg: fired.append(msg["fire"]); send({"fired": True, "id": msg.get("id")})
            msg = recv()
        res = msg.get("result", {})
        check("L4 run over the wire plays appendix B: scan, test, treat", res.get("acts") == ["scan", "test", "treat"] and fired == ["treat"], f"got {res.get('acts')}, fired {fired}")
        check("L4 the wire's result carries thought, steps, operations and the belief as a Display string", res.get("thought") == "1/5" and res.get("steps", {}).get("think") == 1 and isinstance(res.get("operations"), list) and isinstance(res.get("final"), str), f"got {str(res)[:200]}")
        bad = wire_spec(M.variants(M.vector_A(), fraction=F(3, 2))); send({"op": "declare", "spec": bad}); e = recv()
        check("L4 a refused spec comes back by name", e.get("refused") == "FRACTION", f"got {e}")
        send({"op": "nonsense"}); u = recv()
        check("L4 an unknown op is refused, not a crash", "refused" in u and p.poll() is None, f"got {u}")
        send({"op": "bye"})
    except Exception as ex:
        check("L4 the wire", False, f"{type(ex).__name__}: {ex}")
    finally:
        try: p.stdin.close(); p.wait(timeout=5)
        except Exception: p.kill()
    return report(results)

def shipped_text(bare, counts, falsifiers, sha, score):
    "a pack that ships Counts, written from a bare pack and the host's own values - the digest and Score as text"
    rows = ", ".join("[" + repr([list(x) for x in o]) + f", {t!r}, {a!r}, {n}]" for (o, t, a), n in counts.items())
    L = [bare.rstrip("\n"), f'counts([{rows}], sha256={sha!r}, source="data")']
    if falsifiers: L.append("falsifiers([" + ", ".join("[" + repr([list(x) for x in o]) + f", {t!r}, {a!r}]" for o, t, a in falsifiers) + "])")
    L.append(f'score({score}, of="counts", source="data")')
    return "\n".join(L) + "\n"

def _l5(wald, check):
    import counts_check as C, encoding_check as EC, random
    from collections import Counter
    okd = os.path.join(HERE, "packs", "ok")
    try:
        # the digest: V2.13's five vectors
        cases = [(Counter([((("ask", "a1"),), "say a1", "a1")]), []), (Counter({((("ask", "a1"),), "abstain", None): 2}), []),
                 (Counter([((("ask", "é"),), "say é", "é")]), []), (Counter([((("ask", "a1"),), "say a1", "a1")]), [((("ask", "a3"),), None, None)]),
                 (Counter([((("ask", "a/b\t"),), "say a1", "a1")]), [])]
        vec = [d for _, d in EC.page_vectors(os.path.join(HERE, "..", "SURFACE-v0.2.md"))]
        got = [wald.digest(c, f) for c, f in cases]
        check("L5 wald.digest gives V2.13's five vectors", got == vec, f"got {[str(g)[:12] for g in got]}")
        # the Score, and a pack written from the host's values alone: the refit of attack session 5
        full = open(os.path.join(okd, "refit_scored_falsifier.py"), encoding="utf-8", newline="").read()
        bare = "\n".join(l for l in full.split("\n") if not l.startswith(("counts(", "falsifiers(", "score(")))
        ref = R.check(full, {}, okd); world = wald.declare(wald.load_pack(bare, okd))
        sc = wald.score(world, ref["counts"], ref["falsifiers"])
        check("L5 wald.score gives the refit's Score as a pack writes it: 363/10000", sc == "363/10000", f"got {sc!r}")
        text = shipped_text(bare, ref["counts"], ref["falsifiers"], wald.digest(ref["counts"], ref["falsifiers"]), sc)
        w2 = wald.load_pack(text, okd); wald.declare(w2)
        check("L5 the refit, written from wald.digest and wald.score alone, loads and declares", w2.get("score") == F(363, 10000), f"score {w2.get('score')}")
        # a Score of tens of thousands of digits
        A = open(os.path.join(okd, "appendix_a.py"), encoding="utf-8", newline="").read(); worldA = wald.declare(wald.load_pack(A, okd))
        rng = random.Random(1); recs = Counter()
        for _ in range(300):
            a_ = rng.choice(["a1", "a2"]); recs[((("ask", a_),), "say " + a_, a_ if rng.random() < 0.8 else {"a1": "a2", "a2": "a1"}[a_])] += 1
        want = R.q(C.loo_score(R.check(A, {}, okd), recs)); limit = sys.get_int_max_str_digits()
        sc = wald.score(worldA, recs, ())
        check(f"L5 wald.score writes a Score of {len(want.split('/')[1])} digits exactly", sc == want, f"got {len(str(sc))} characters")
        w3 = wald.load_pack(shipped_text(A, recs, [], wald.digest(recs, []), sc), okd); wald.declare(w3)
        check("L5 that pack loads and declares, and Python's limit on integer conversion is untouched", sys.get_int_max_str_digits() == limit and R.q(w3["score"]) == want, "")
        # E7 as a Display
        G = C.reliability_world([F(1, 2), F(9, 10)], [F(1, 2), F(1, 2)], F(-2))
        g1 = Counter({C.rec("a1", "a1", "say a1"): 99, C.rec("a2", "a2", "say a2"): 99, C.rec("a1", "a2", "say a1"): 1, C.rec("a2", "a1", "say a2"): 1})
        worldG = wald.declare(wald.load_pack(R.to_pack_v02(G), okd)); d = wald.e7(worldG, g1)
        inert = isinstance(d, wald.Display)
        try: d == d; inert = False
        except TypeError: pass
        text_ = str(d); lines = C.diagnostic(G, g1)
        check("L5 wald.e7 is a Display - inert, S1 - whose text holds every line of E7 as an exact rational (the degenerate label)",
              inert and all(R.q(v) in text_ for v in lines.values()), f"inert {inert}; {text_[:120]!r}")
    except Exception as e:
        check("L5 a host shipping Counts needs no kit", False, f"{type(e).__name__}: {str(e)[:200]}")

def report(results):
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"library: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(); sys.exit(0 if main(a.impl, a.seed) else 1)
