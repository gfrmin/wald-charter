"""
kit_counts.py - kit v0.11: judges an implementation of CHARTER v0.2 (signed, tag charter-v0.2), what is learned between
episodes. `laws/counts_check.py` is the reference and the definition; INTERFACE.md's kit v0.11 section is the contract.
  python3 laws/kit_counts.py --impl PATH_TO_src [--seed S]        python3 laws/kit_counts.py --standin

K0  kit integrity: the reference passes its consequences, every poison dies, every pinned World of six attack sessions holds.
K1  the consequences through the adapter, on random Worlds and the pinned ones: locals never persist (FRESH), order
    invariance (C22), sufficiency (C23), no leakage (C24), the reference's acts episode by episode (E2), bounded (BOUND).
K2  refusals by name: GLOBAL, AFTER, PLATE (digest, a record no episode here can write, a multiset impossible under every
    Global value), UNSCORED (a Score that is not the leave-one-out one).
K3  S15's disclosure, class for class, on the Worlds the page names: the router, honest ignorance, the stakes, the cap
    (with the think act), and the three that list nothing (an echoing grader, a per-state bonus, a twin).
K4  E7's lines, line for line: the degenerate label, the unconverged posterior, a World that is right.
K5  the Score: the leave-one-out predictive probability, exactly.
K7  kit v0.12: the adapter's shapes are model.py's; its digest is V2.13's on the page's five vectors and on fuzzed names; its
    Score scores the falsifying records (V2.8), accepting the refit of attack session 5 at 363/10000 and refusing both of
    signed S14's readings UNSCORED; a full record with no after-report is no falsifier (V2.7, PLATE); a prefix falsifier
    is shippable (V2.7).
K8  kit v0.13 (brief 008's questions): a Global value the prior does not name is no state (Q11); a record whose ending end
    its draws never reach is refused PLATE (Q14); a prefix falsifier ending at an ending outcome ships (Q15); an ending
    outcome ends the episode - the public plate records end:act=outcome, and a zero-mass one falsifies at a prefix.
K9  kit v0.13: what the implementation's plate writes, it reads back: on the pinned Worlds, for every door answer, each
    record and falsifier is realisable in its own declaration, a plate's Counts ship into that declaration, and a
    falsified plate's Counts and falsifier ship into a refit with the same mechanics (laws/roundtrip_check.py's rule).
K6  the public plate: `wald.plate(world)`, on the World the adapter builds from the dict, played against a scripted door,
    carries Counts from episode to episode - appendix
    A's two episodes, its acts, its Counts - and ends WORLD_FALSIFIED on a report of probability zero, the falsifying
    record kept beside the Counts (J26).
"""
import argparse, importlib, os, random, sys
from collections import Counter
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import counts_check as C
from spec_check import REF, Refused

# ---------------------------------------------------------------- the adapter, seen as counts_check's implementations
class Impl(C.Reference):
    "the builder's adapter behind counts_check's implementation protocol; conversion only"
    name = "implementation"
    def __init__(self, adapter): self.a = adapter
    def prior(self, W, recs): return {C.skey(l, g): p for (l, g), p in self.a.prior(W, list(recs)).items()}
    def persist(self, recs): return self.a.persist(list(recs))
    def decide(self, b, w, n, used=frozenset()): return self.a.decide(b, w, n, frozenset(used))
    def declare(self, W): return self.a.declare(W)
    def disclose(self, W): return self.a.disclose(W)

def pinned_worlds():
    "the Worlds of the page's appendices and the six attack sessions, each with a plate of records it can write"
    A = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    out = [(A, [C.rec("a1", "a1", "say a1"), C.rec("a2", "a1", "say a2"), C.rec("a1", "a1", "say a1")]),
           (C.oscillating_world(), [((), "useA", "A1"), ((), "useB", "B0"), ((), "useA", "A0")]),
           (C.railed_world(), [((), "useA", "1"), ((), "useA", "0")]),
           (C.two_world(), [((("ask", "a1"), ("check", "a1")), "say a1", None)] * 3),
           (C.base_rate_world(F(0)), [((("ask", "a2"),), "say a2", None)] * 3),
           (C.falsified_refit_world(), [C.rec("a1", "a1", "say a1"), C.rec("a2", "a2", "say a2")]),
           (C.stakes_world(), []),
           (C.ending_ask_world(F(1, 5)), [((("ask", "drop"),), "end:ask=drop", "a1"), C.rec("a1", "a1", "say a1")]),     # kit v0.13
           (C.peek_world(), [((("peek", "go"), ("ask", "a1")), "say a1", "a1")])]
    lw = C.levels_world(); out.append((lw, []))
    return out

def refusal_cases():
    "(name, World) pairs the kernel must refuse, each by that name"
    cases = [("GLOBAL", C.paid_global_world())]
    Wa = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    del Wa["after"]["K"]["abstain"]                                              # an after-kernel that omits an end
    cases.append(("AFTER", Wa))
    def shipped(W, counts, sha=None, score=None, falsifiers=()):
        W = dict(W); W["counts"] = counts; W["counts_sha"] = sha or C.counts_sha(counts, falsifiers)
        if falsifiers: W["falsifiers"] = list(falsifiers)
        W["score"] = score if score is not None else (C.loo_score(W, counts, falsifiers) if C.expressible(W, counts, falsifiers) else F(1))
        return W
    A = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); one = Counter([C.rec("a1", "a1", "say a1")])
    cases.append(("PLATE", shipped(A, one, sha="0" * 64)))
    cases.append(("PLATE", shipped(A, Counter([((("ask", "a1"), ("ask", "a1")), "say a1", "a1")]))))       # two draws, N = 1
    Fb = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); lsb, gsb = C.vals(Fb["locals"]), C.vals(Fb["globals"])
    Fb["O"]["ask"]["K"] = {(l, g): {l[0]: F(1)} for l in lsb for g in gsb}
    cases.append(("PLATE", shipped(Fb, Counter([C.rec("a1", "a2", "say a1")]))))                           # impossible everywhere
    cases.append(("UNSCORED", shipped(A, one, score=F(1, 2))))
    return cases

def disclosure_cases():
    "(label, World) pairs whose disclosure must be the reference's, class for class"
    return [("the router, credence's prior", C.router_world(False, credence_prior=True)),
            ("honest ignorance (appendix H)", C.two_world()), ("the stakes (appendix I)", C.stakes_world()),
            ("the cap, with the think act (appendix K)", C.cap_world(F(9, 10))),
            ("an echoing grader: nothing", C.echo_world()), ("a per-state bonus: nothing", C.bonus_world()),
            ("twins: nothing", C.twin_world(F(1, 3), F(1, 6))), ("a colour no act feels: nothing", C.colour_world())]

def e7_cases():
    Wg = C.reliability_world([F(1, 2), F(9, 10)], [F(1, 2), F(1, 2)], F(-2))
    g1 = Counter({C.rec("a1", "a1", "say a1"): 99, C.rec("a2", "a2", "say a2"): 99, C.rec("a1", "a2", "say a1"): 1, C.rec("a2", "a1", "say a2"): 1})
    osc = Counter({((), "useA", "A1"): 16, ((), "useA", "A0"): 24, ((), "useB", "B1"): 16, ((), "useB", "B0"): 24})
    A = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    right = Counter({C.rec("a1", "a1", "say a1"): 90, C.rec("a1", "a2", "say a1"): 10, C.rec("a2", "a2", "say a2"): 90, C.rec("a2", "a1", "say a2"): 10})
    return [("the degenerate label (appendix C)", Wg, g1), ("the unconverged posterior (appendix E)", C.oscillating_world(), osc),
            ("a World that is right", A, right)]

def canon(classes): return sorted(sorted((tuple(g), p) for g, p in c.items()) for c in classes)

# ---------------------------------------------------------------- the checks
def main(impl, seed, adapter=None, wald=None, quiet=False):
    say = (lambda *a: None) if quiet else print
    results = []
    def check(tag, cond, note=""): results.append((tag, bool(cond), note))
    # K0
    rng = random.Random(20260923); ws = []
    for _ in range(30):
        W = C.rand_world(rng)
        try: C.refuse(W)
        except Refused: continue
        ws.append((W, C.rand_records(W, rng, rng.randint(3, 6))))
    ref_fails = C.run(C.REFI, ws, 1)
    if any(ref_fails.values()): say("KIT BROKEN: the v0.2 reference fails its own consequences", ref_fails); return False
    for p in C.POISONS:
        if not any(C.run(p, ws, 1).values()): say("KIT BROKEN: a v0.2 poison survives:", p.name); return False
    C.frozen()
    say(f"counts kit integrity: reference clean, {len(C.POISONS)} poisons killed, the pinned Worlds of six sessions hold")
    # the implementation
    if adapter is None:
        sys.path.insert(0, os.path.abspath(impl))
        a = importlib.import_module("wald.kit_adapter").make_agent()
        missing = [m for m in ("prior", "persist", "declare", "disclose", "e7", "score", "world", "digest") if not hasattr(a, m)]
        if missing: say(f"FAIL counts: the adapter lacks {missing} (INTERFACE.md, kit v0.11)"); return False
        adapter = a; wald = importlib.import_module("wald")
    I = Impl(adapter); rng = random.Random(seed)
    worlds = []
    for _ in range(40):
        W = C.rand_world(rng)
        try: C.refuse(W)
        except Refused: continue
        worlds.append((W, C.rand_records(W, rng, rng.randint(3, 7))))
    worlds += pinned_worlds()
    # K1
    for cname, chk in C.CHECKS:
        bad = [i for i, (W, recs) in enumerate(worlds) if not _safe(chk, I, W, recs, random.Random(seed + i))]
        check(f"K1 {cname} on {len(worlds)} Worlds ({len(pinned_worlds())} pinned)", not bad, f"fails on World(s) {bad[:5]}")
    # K2
    for name, W in refusal_cases():
        try: adapter.declare(W); check(f"K2 refused {name}", False, "accepted")
        except Exception as e:
            got = getattr(e, "name", None) or str(e).split(":")[0]
            check(f"K2 refused {name}", got == name, f"got {type(e).__name__} {got!r}")
    try: adapter.declare(C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2), verdict=False)); check("K2 A' is accepted: S15 refuses nothing", True)
    except Exception as e: check("K2 A' is accepted: S15 refuses nothing", False, f"refused {e}")
    # K3
    for label, W in disclosure_cases():
        got = _safe_call(adapter.disclose, W)
        check(f"K3 disclosure: {label}", got is not None and canon(got) == canon(C.unwashable(W)), f"got {got}")
    # K4
    for label, W, c in e7_cases():
        got = _safe_call(adapter.e7, W, c); want = C.diagnostic(W, c)
        check(f"K4 E7 lines: {label}", got == want, f"got {len(got) if got else got} lines")
    # K5
    A3 = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    c3 = Counter({C.rec("a1", "a1", "say a1"): 2, C.rec("a1", "a2", "say a1"): 1})
    check("K5 the Score is the leave-one-out predictive probability: 1125/100672", _safe_call(adapter.score, A3, c3) == F(1125, 100672))
    # K7
    _k7(adapter, check)
    # K8, K9 (kit v0.13)
    _k8(adapter, check)
    # K6
    if wald is not None: _public_plate(wald, adapter, check); _k8_plate(wald, adapter, check); _k9(wald, adapter, check)
    for tag, good, note in results:
        if not good: say(f"FAIL {tag}   {note}")
    say(f"counts: {sum(g for _, g, _ in results)}/{len(results)} pass")
    return all(g for _, g, _ in results)

def _k7(adapter, check):
    import model as M, encoding_check as EC, glob, re
    import surface_check as SC
    here = os.path.dirname(os.path.abspath(__file__))
    # shapes
    A = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    pr = _safe_call(adapter.prior, A, [C.rec("a1", "a1", "say a1")])
    ok = isinstance(pr, dict) and all(isinstance(s, tuple) and len(s) == 2 and isinstance(s[0], tuple) and isinstance(s[1], tuple) and isinstance(p, F) for s, p in pr.items())
    check("K7 the adapter's prior is keyed by model.py's states (local, Global) with exact Fractions", ok, f"got {str(pr)[:120]}")
    # the digest: the page's vectors, then fuzzed names
    cases = [(Counter([((("ask", "a1"),), "say a1", "a1")]), []), (Counter({((("ask", "a1"),), "abstain", None): 2}), []),
             (Counter([((("ask", "é"),), "say é", "é")]), []), (Counter([((("ask", "a1"),), "say a1", "a1")]), [((("ask", "a3"),), None, None)]),
             (Counter([((("ask", "a/b\t"),), "say a1", "a1")]), [])]
    page = os.path.join(here, "..", "SURFACE-v0.2.md"); vec = [d for _, d in EC.page_vectors(page)] if os.path.exists(page) else []
    got = [_safe_call(adapter.digest, c, f) for c, f in cases]
    check("K7 the digest of V2.13's five vectors", got == [C.counts_sha(c, f) for c, f in cases] and (not vec or got == vec), f"got {[str(g)[:12] for g in got]}")
    rng = random.Random(8); alphabet = list('ab"\\/\x7f\t\n=:') + ["é", "中", "😀"]; bad = 0
    for _ in range(200):
        nm = lambda: "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 3)))
        record = (((nm(), nm()),), nm(), rng.choice([None, nm()]))
        c = Counter({record: rng.randint(1, 10 ** rng.randint(0, 20))})
        bad += _safe_call(adapter.digest, c, []) != C.counts_sha(c, [])
    check("K7 the digest on 200 fuzzed record sets: quotes, backslashes, DEL, control, non-ASCII and astral names", bad == 0, f"{bad} differ")
    # the Score with a falsifying record, and the two falsifier rules
    for fn, want in (("refit_scored_falsifier.py", "accept"),):
        W = SC.check(open(os.path.join(here, "packs/ok", fn), encoding="utf-8", newline="").read(), {}, os.path.join(here, "packs/ok"))
        s_ = _safe_call(adapter.score, W, W["counts"], W.get("falsifiers", []))
        check(f"K7 the Score scores the falsifying records: {fn} at 363/10000", s_ == F(363, 10000) == W["score"], f"got {s_}")
    for fn, name in (("v02_s5_f4_1a_refit_s14_score.py", "UNSCORED"), ("v02_s5_f4_1a_refit_s14_score_ii.py", "UNSCORED"), ("v02_s5_f4_1b_full_record_falsifier.py", "PLATE")):
        t = open(os.path.join(here, "packs/poison", fn), encoding="utf-8", newline="").read()
        try:
            SC.check(t, {}, os.path.join(here, "packs/poison")); check(f"K7 reference refuses {fn}", False, "the reference accepts it")
        except Exception: pass
        W = _world_of(t)
        if W is None: continue
        try: adapter.declare(W); check(f"K7 refused {name}: {fn}", False, "accepted")
        except Exception as e: check(f"K7 refused {name}: {fn}", (getattr(e, "name", None) or str(e).split(":")[0]) == name, f"got {e}")
    Wp = SC.check(open(os.path.join(here, "packs/ok/prefix_falsifier.py"), encoding="utf-8", newline="").read(), {}, os.path.join(here, "packs/ok"))
    try: adapter.declare(Wp); check("K7 a prefix falsifier is shippable (V2.7)", True)
    except Exception as e: check("K7 a prefix falsifier is shippable (V2.7)", False, f"refused {e}")

def _shipped(W, counts, falsifiers=()):
    V = {k: v for k, v in W.items() if k not in ("counts", "counts_sha", "score", "falsifiers")}
    V["counts"] = Counter(counts); V["counts_sha"] = C.counts_sha(V["counts"], falsifiers)
    if falsifiers: V["falsifiers"] = list(falsifiers)
    V["score"] = C.loo_score(V, V["counts"], falsifiers) if C.expressible(V, V["counts"], falsifiers) else F(1)
    return V

def _declares(adapter, W):
    try: adapter.declare(W); return "accepted"
    except Exception as e: return getattr(e, "name", None) or (str(e).split(":")[0] if type(e).__name__ == "Refused" else f"{type(e).__name__}: {e}")

def _k8(adapter, check):
    A = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    U = dict(A, globals=[("rel", ["9/10", "3/5", "1/2"])]); recs = [C.rec("a1", "a1", "say a1")]
    got = _safe_call(adapter.prior, U, recs); want = {C.unkey(k): v for k, v in C.episode_world(U, Counter(recs))["prior"].items()}
    check("K8 a Global value the prior does not name is no state: accepted, and the prior is appendix A's (Q11)",
          _declares(adapter, U) == "accepted" and got == want, f"declare: {_declares(adapter, U)}; prior {str(got)[:80]}")
    P = C.peek_world()
    v = _declares(adapter, _shipped(P, {((), "end:peek=drop", "a1"): 1}))
    check("K8 a record whose ending end its draws never reach is refused PLATE (Q14)", v == "PLATE", f"got {v}")
    E = C.ending_ask_world(F(1, 5)); pre = ((("ask", "drop"),), None, None)
    v = _declares(adapter, _shipped(E, {((("ask", "a1"),), "say a1", "a1"): 1}, [pre]))
    check("K8 a prefix falsifier whose falsifying report is an ending outcome ships (Q15, V2.7)", v == "accepted", f"got {v}")

def _k8_plate(wald, adapter, check):
    try:
        pl = wald.plate(adapter.world(C.ending_ask_world(F(1, 5))))
        r = pl.run(_Door(wald, ["drop", "a1"]).make())
        rec_ = ((("ask", "drop"),), "end:ask=drop", "a1")
        check("K8 an ending outcome ends the episode: the plate records end:ask=drop and its after-report", dict(pl.counts()) == {rec_: 1} and pl.falsifier() is None,
              f"got {dict(pl.counts())}, {pl.falsifier()}, status {getattr(r, 'status', None)}")
        pz = wald.plate(adapter.world(C.ending_ask_world(F(0))))
        rz = pz.run(_Door(wald, ["drop"]).make())
        check("K8 a zero-mass ending outcome falsifies at a prefix: ((ask, drop),), no end, no after-report (J26, Q15)",
              "FALSIFIED" in str(rz.status) and pz.falsifier() == ((("ask", "drop"),), None, None) and dict(pz.counts()) == {},
              f"got {rz.status}, {pz.falsifier()}, {dict(pz.counts())}")
    except Exception as e:
        check("K8 the public plate at an ending outcome", False, f"{type(e).__name__}: {e}")

def _k9(wald, adapter, check):
    "the round trip through the implementation's own plate (laws/roundtrip_check.py's rule)"
    import roundtrip_check as RT
    class Need(Exception): pass
    bad, n = [], 0
    for label, maker in C.PINNED.items():
        W = maker()
        if "dplus" in W: continue
        after = W["after"].get("name", "after") if W.get("after") else None
        def run(script):
            nonlocal n
            pl = wald.plate(adapter.world(W)); it = iter(script); seen = {"end": None, "last": None}
            class D(wald.Door):
                def outcome(self, act):
                    end = None
                    if act == after and (seen["end"] is not None or seen["last"] is not None):
                        k, o = seen["last"] or (None, None); end = seen["end"] if seen["end"] is not None else f"end:{k}={o}"
                    try: o = next(it)
                    except StopIteration: raise Need((act, end))
                    if end is None: seen["last"] = (act, o)
                    return o
                def fire(self, act): seen["end"] = act
            try: pl.run(D())
            except Need as e:
                act, end = e.args[0]
                for o in RT.named(W, act, end): run(script + [o])
                return
            n += 1; counts, f = pl.counts(), pl.falsifier()
            if any(not C.realisable(W, r) for r in counts): bad.append(f"{label}: writes {dict(counts)}, which its declaration could not have written"); return
            if f is not None and not C.realisable(W, tuple(f), True): bad.append(f"{label}: writes the falsifier {f}, which its declaration could not have written"); return
            V = _shipped(W, counts) if f is None else _shipped(RT.refit(W), counts, list(W.get("falsifiers", ())) + [tuple(f)])
            v = _declares(adapter, V)
            if v != "accepted": bad.append(f"{label}: {dict(counts)}, {f} - {'its own declaration' if f is None else 'a refit'} refuses them {v}")
        try: run([])
        except Exception as e: bad.append(f"{label}: raised {type(e).__name__}: {e}")
    check(f"K9 what the implementation's plate writes it reads back: {n} plates on the pinned Worlds", not bad, bad[0] if bad else "")

def _world_of(text):
    "the World a poison pack would declare, the charter's refusal switched off, so the kernel's own refusal is judged"
    import surface_check as SC
    orig = C.refuse; C.refuse = lambda W: W
    try: return SC.check(text, {}, ".")
    except Exception: return None
    finally: C.refuse = orig

def _safe(chk, I, W, recs, rng):
    try: return chk(I, W, recs, rng)
    except Exception: return False

def _safe_call(f, *a):
    try: return f(*a)
    except Exception: return None

class _Door:
    "a scripted door for the public plate: answers every observational act and the After-act from a list, in order"
    def __init__(self, wald, outcomes):
        self.base = wald.Door; self.outs = list(outcomes); self.fired = []
    def make(self):
        outs, fired = self.outs, self.fired
        class D(self.base):
            def outcome(self, act): return outs.pop(0)
            def fire(self, act): fired.append(act)
        return D()

def _public_plate(wald, adapter, check):
    A = C.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2))
    try:
        plate = wald.plate(adapter.world(A))
        d1 = _Door(wald, ["a1", "a1"]); r1 = plate.run(d1.make())
        d2 = _Door(wald, ["a1", "a1"]); r2 = plate.run(d2.make())
        check("K6 appendix A, episode 1: ask, say a1; episode 2: ask, say a1", list(r1.acts) == ["ask", "say a1"] and list(r2.acts) == ["ask", "say a1"],
              f"got {list(r1.acts)}, {list(r2.acts)}")
        check("K6 the plate's Counts are its two records", dict(plate.counts()) == {C.rec("a1", "a1", "say a1"): 2}, f"got {dict(plate.counts())}")
        Wf = C.railed_world(); ls1 = C.vals(Wf["locals"]); gs1 = [("x",), ("y",)]
        pA = {("x",): F(7, 10), ("y",): F(3, 10)}
        Wf["prior_local"] = {g: {l: (pA[g] if l[0] == "1" else 1 - pA[g]) * (F(1) if l[1] == "1" else F(0)) for l in ls1} for g in gs1}
        pf = wald.plate(adapter.world(Wf))
        rf = pf.run(_Door(wald, ["0"]).make())
        check("K6 a report of probability zero ends the plate WORLD_FALSIFIED, Counts unchanged, the falsifier kept (J26)",
              "FALSIFIED" in str(rf.status) and dict(pf.counts()) == {} and pf.falsifier() == ((), "useB", "0"), f"got {rf.status}, {dict(pf.counts())}, {pf.falsifier()}")
    except Exception as e:
        check("K6 the public plate", False, f"{type(e).__name__}: {e}")

# ---------------------------------------------------------------- the stand-in: the reference as an adapter
class _StandIn:
    "counts_check's reference behind the adapter's methods, and a reference plate behind `wald.plate`"
    def prior(self, W, recs): return {C.unkey(s): p for s, p in C.episode_world(W, Counter(recs))["prior"].items()}
    def persist(self, recs): return Counter(recs)
    def decide(self, b, w, n, used=frozenset()): return REF.solve(b, w, min(w["d"], n), used)[1]
    def declare(self, W): return C.refuse(W)
    def disclose(self, W): return C.unwashable(W)
    def e7(self, W, counts): return C.diagnostic(W, counts)
    def score(self, W, counts): return C.loo_score(W, counts)
    def world(self, W): return C.refuse(W)
    def digest(self, counts, falsifiers=()): return C.counts_sha(counts, falsifiers)
    def score(self, W, counts, falsifiers=()): return C.loo_score(W, counts, falsifiers)

class _RefWald:
    "the reference plate (counts_check.Plate) behind `wald.plate`, and a Door base class for the scripted doors"
    class Door:
        def outcome(self, act): raise NotImplementedError
        def fire(self, act): raise NotImplementedError
    @staticmethod
    def plate(W): return C.Plate(W)

class _Liar(_StandIn):
    def disclose(self, W): return []

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl"); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--standin", action="store_true")
    a = ap.parse_args()
    if a.standin:
        good = main(None, 5, adapter=_StandIn(), wald=_RefWald)
        bad = main(None, 5, adapter=_Liar(), wald=_RefWald, quiet=True)
        print("stand-in: reference passes:", good, "| a kernel that hides the disclosure fails:", not bad)
        sys.exit(0 if good and not bad else 1)
    sys.exit(0 if main(a.impl, a.seed) else 1)
