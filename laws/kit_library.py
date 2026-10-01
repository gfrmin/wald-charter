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
L6  kit v0.14 (gfrmin/wald#14): what a host may ask of a plate without playing an episode. `Plate.prior()` is the sealed
    belief its next episode starts from; `report(belief, world, over=[...])` its marginal on the named components;
    `Plate.values()` V_0, E[u] per terminal, Q_n and Q_n - V_0 per act, V_n and decide_n, as a Display; and every verb
    refuses by raising.
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

def serve_env(impl):
    "kit v0.14: tools/serve.py is the builder's code; it gets a PATH and the implementation, and nothing of the kit's environment."
    return {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": os.path.abspath(impl)}

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
    # L6: what a host may ask of a plate (kit v0.14)
    _l6(wald, check, seed)
    # L4: the wire
    root = os.path.dirname(os.path.abspath(impl)); serve = os.path.join(root, "tools", "serve.py")
    if not os.path.exists(serve):
        check("L4 tools/serve.py exists", False, "no tools/serve.py")
        return report(results)
    p = subprocess.Popen([sys.executable, serve], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=serve_env(impl), cwd=root)
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
        # Q6 (brief 006), pinned at kit v0.14: a decimal where a rational is meant is FLOAT; everything else the wire
        # can get wrong is WIRE, the wire's refusal in general - an unknown key refused, never ignored
        for fault, want, mutate in _wire_faults():
            send({"op": "declare", "spec": mutate(wire_spec(M.vector_A()))}); e = recv()
            check(f"L4 a wire spec with {fault} is refused {want} (Q6)", e.get("refused") == want, f"got {e}")
        p.stdin.write("{not json\n"); p.stdin.flush(); e = recv()
        check("L4 a line that is not JSON is refused WIRE, not a crash (Q6)", e.get("refused") == "WIRE" and p.poll() is None, f"got {e}")
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

def _wire_faults():
    "Q6's reading, kit v0.14: (the fault, its name, a change to a wire spec)"
    def at(f):
        def g(s): s = json.loads(json.dumps(s)); f(s); return s
        return g
    first = lambda s: next(iter(s["prior"]))
    return [("a JSON float for a rational", "FLOAT", at(lambda s: s["prior"].__setitem__(first(s), 0.2))),
            ("a decimal string for a rational", "FLOAT", at(lambda s: s["prior"].__setitem__(first(s), "0.2"))),
            ("an exponent string for a rational", "FLOAT", at(lambda s: s["prior"].__setitem__(first(s), "1e-3"))),
            ("an unknown key (dplsu)", "WIRE", at(lambda s: s.__setitem__("dplsu", 2))),
            ("a count written as a string", "WIRE", at(lambda s: s.__setitem__("N", "2"))),
            ("a missing key (T)", "WIRE", at(lambda s: s.pop("T")))]

def drawn(wald, W, rng):
    """a wald.Door that draws a state from W's prior, then every report from that state's kernel rows, the After-act's
    included: whatever it reports, the World gave positive mass, so no plate it plays is falsified"""
    sts = [(l, g) for g, pg in W["prior_global"].items() for l, pl in W["prior_local"][g].items() if pg * pl > 0]
    def pick(row):
        os_ = [o for o, p in row.items() if p > 0]; return rng.choices(os_, [row[o] for o in os_])[0]
    class D(wald.Door):
        def __init__(self):
            self.st = rng.choices(sts, [W["prior_global"][g] * W["prior_local"][g][l] for l, g in sts])[0]; self.end = None
        def outcome(self, act):
            if W.get("after") and act == W["after"].get("name", "after"): return pick(W["after"]["K"][self.end][self.st])
            o = pick(W["O"][act]["K"][self.st])
            if o in W["O"][act].get("ends", ()): self.end = f"end:{act}={o}"
            return o
        def fire(self, act): self.end = act
    return D

def _l6(wald, check, seed):
    """kit v0.14 (gfrmin/wald#14): what a host may ask of a plate without playing an episode - the belief its next episode
    starts from, sealed; any marginal of a belief as a Display; the decision quantities there as a Display - and that
    every verb refuses by raising"""
    import counts_check as C, random
    from collections import Counter
    okd = os.path.join(HERE, "packs", "ok"); rng = random.Random(seed)
    def inert(d):
        if not isinstance(d, wald.Display): return False
        try: d == d
        except TypeError: return True
        return False
    def refusal(f):
        try: f()
        except wald.refusals.Refused as e: return e.name
        except Exception as e: return type(e).__name__
        return "returned"
    try:
        w = S.appendix(F(1, 2), True); w["N"], w["d"] = 1, 1
        p = wald.plate(wald.declare(wald.from_json(json.dumps(wire_spec(w))))); v = p.values()
        check("L6 CHARTER v0's appendix on a plate: values() is a Display reading V_0 -8/5, Q_1(test) -51/50, Q_1 - V_0 29/50, decide_1 test",
              inert(v) and str(v) == C.render_values(C.values(w)), f"got {str(v)[:200]!r}")
        bad = wire_spec(M.vector_A()); bad["T"] = {}
        check("L6 declare raises Refused, as load_pack does: one convention (EMPTY_T)", refusal(lambda: wald.declare(wald.from_json(json.dumps(bad)))) == "EMPTY_T", "")
        poison = os.path.join(HERE, "packs", "poison", "08_unread_parameter.py")
        if os.path.exists(poison):
            check("L6 load_pack raises Refused (UNREAD_PARAMETER)", refusal(lambda: wald.load_pack(open(poison, encoding="utf-8", newline="").read(), okd)) == "UNREAD_PARAMETER", "")
    except Exception as e:
        check("L6 the appendix's values on a plate", False, f"{type(e).__name__}: {str(e)[:200]}")
    # Q6 in process: from_json refuses as the wire does
    for fault, want, mutate in _wire_faults():
        check(f"L6 from_json of a spec with {fault} raises Refused {want} (Q6)", refusal(lambda: wald.declare(wald.from_json(json.dumps(mutate(wire_spec(M.vector_A())))))) == want, "")
    check("L6 from_json of text that is not JSON, or not an object, raises Refused WIRE (Q6)",
          refusal(lambda: wald.from_json("{not json")) == "WIRE" == refusal(lambda: wald.from_json("[1, 2]")), "")
    # Q9's second half (brief 007), pinned at kit v0.14: falsifier() is this plate's own falsifying record; the ones its
    # declaration shipped are the declaration's, in the evidence of every prior, and are not returned
    try:
        text = open(os.path.join(okd, "refit_scored_falsifier.py"), encoding="utf-8", newline="").read()
        Wf = R.check(text, {}, okd); kp = wald.plate(wald.declare(wald.load_pack(text, okd)))
        bref = C.Plate(Wf).prior(); names = [c for c, _ in Wf["globals"]]
        check("L6 a plate shipped a falsifying record: falsifier() is None until the plate itself is falsified (Q9)",
              Wf.get("falsifiers") and kp.falsifier() is None, f"got {kp.falsifier()!r}")
        check("L6 ... and its prior conditions on the shipped falsifying record (J26)",
              str(wald.report(kp.prior(), wald.declare(wald.load_pack(text, okd)), over=names)) == C.render_marginal(C.marginal(Wf, bref, names)), "")
    except Exception as e:
        check("L6 a plate shipped a falsifying record (Q9)", False, f"{type(e).__name__}: {str(e)[:200]}")
    cases = [("router", C.router_world(True)), ("reliability", C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)))]
    cases += [(f"random {i}", C.rand_world(rng)) for i in range(4)] + [(f"deep {i}", C.deep_world(rng)) for i in range(3)]
    for label, W0 in cases:
        if len(cases) > 60: check("L6 a deep World where depth matters is drawn within 50 tries", False, ""); break
        try:
            bare = R.to_pack_v02(W0); W = R.check(bare, {}, okd); D = drawn(wald, W, rng)
            ref = C.Plate(W)
            for _ in range(rng.randint(3, 12)): ref.run(D())
            recs = ref.counts()
            text = shipped_text(bare, recs, [], C.counts_sha(recs), C.q(C.loo_score(W, recs)))
            Ws = R.check(text, {}, okd); world = wald.declare(wald.load_pack(text, okd))
            ref, kp = C.Plate(Ws), wald.plate(world)
            if label.startswith("deep"):     # depth must matter at the prior judged, or a kernel that computes Q_1 passes
                w_ = C.episode_world(Ws, ref.c + Counter(ref.shipped)); b_ = w_["prior"]
                if all(S.REF.q(b_, w_, k, 2) == S.REF.q(b_, w_, k, 1) for k in w_["O"]): cases.append((label, C.deep_world(rng))); continue
            r = kp.run(D()); ref.c[r.record] += 1        # the plate's own record, beside the shipped ones
            b = kp.prior(); bref = ref.prior(); names = [c for c, _ in Ws["locals"] + Ws["globals"]]
            check(f"L6 {label}: prior() is a sealed belief - no public attribute, not a Display - that report renders",
                  not [a for a in dir(b) if not a.startswith("_")] and not isinstance(b, wald.Display) and inert(wald.report(b, world)), f"{type(b).__name__}")
            G = [c for c, _ in Ws["globals"]]
            if G:
                d = wald.report(b, world, over=G)
                check(f"L6 {label}: report(prior, over=Globals) is P(Global | Counts), the shipped and the plate's own",
                      inert(d) and str(d) == C.render_marginal(C.marginal(Ws, bref, G)), f"got {str(d)[:160]!r}")
            for over in [[c] for c in names] + [names[::-1]]:
                d = wald.report(b, world, over=over)
                check(f"L6 {label}: report(prior, over={over}) is that marginal, values in the order over names them",
                      inert(d) and str(d) == C.render_marginal(C.marginal(Ws, bref, over)), f"got {str(d)[:160]!r}")
            check(f"L6 {label}: report over a name that is no component, or one twice, is refused UNKNOWN_NAME",
                  refusal(lambda: wald.report(b, world, over=["no such component"])) == "UNKNOWN_NAME" == refusal(lambda: wald.report(b, world, over=names[:1] * 2)), "")
            v = kp.values()
            check(f"L6 {label}: values() is a Display of n, V_0, E[u] per terminal, Q_n and Q_n - V_0 per act, V_n and decide_n",
                  inert(v) and str(v) == ref.values(), f"got {str(v)[:200]!r}\nwant {ref.values()[:200]!r}")
        except Exception as e:
            check(f"L6 {label}: a plate's prior, marginals and values", False, f"{type(e).__name__}: {str(e)[:200]}")
    try:
        W = R.check(R.to_pack_v02(C.reliability_world([F(1)], [F(1)], F(-2))), {}, okd); world = wald.declare(wald.load_pack(R.to_pack_v02(C.reliability_world([F(1)], [F(1)], F(-2))), okd))
        kp = wald.plate(world)
        class Liar(wald.Door):
            def __init__(self): self.said = None
            def outcome(self, act):
                if act == "ask": self.said = "a1"; return "a1"
                return "a2" if self.said == "a1" else "a1"
            def fire(self, act): pass
        r = kp.run(Liar())
        if str(r.status).endswith("WORLD_FALSIFIED"):
            check("L6 a falsified plate has no next prior and no values: prior() and values() raise WorldFalsified, as run does",
                  refusal(kp.prior) == refusal(kp.values) == "WorldFalsified", f"{refusal(kp.prior)}, {refusal(kp.values)}")
        else: check("L6 the falsifying vector falsifies", False, f"status {r.status}, acts {r.acts}")
    except Exception as e:
        check("L6 a falsified plate", False, f"{type(e).__name__}: {str(e)[:200]}")

def report(results):
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"library: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(); sys.exit(0 if main(a.impl, a.seed) else 1)
