"""
kit_surface.py - kit v0.3: judges an implementation of the signed SURFACE page (tag surface-v0).
Called by kit.py; alone:  python3 laws/kit_surface.py --impl PATH_TO_src [--seed INT]
The implementation provides wald.surface.check(text, data_dir) -> World spec (INTERFACE.md), raising wald.refusals.Refused(name),
and wald.surface.census(text, data_dir) -> {source: count of quantities}.
R3  every pack in packs/ok elaborates to exactly the World the reference checker builds, with the same census, and `declare` accepts it.
R2  every pack in packs/poison is refused by (one of) the name(s) on its first line.
R1  random Worlds from a seed the builder never sees, printed as packs, elaborate back to the same World, menu order included.
kit v0.13 (brief 009):
R9  vectors: a raw lone surrogate handed over as text is NOT_A_DECLARATION (V2.11; QUESTIONS.md Q17); a pack shipping 300
    records, whose Score runs to tens of thousands of digits, elaborates to the reference's World - without the host
    lifting Python's limit on integer conversion.
R10 the corpus mutated (laws/mutations.py; a sample the seed chooses): where the reference accepts a variant, the
    implementation accepts it as the same World with the same census; where the reference refuses one, the implementation
    refuses it - by any name, since a mutation may break several rules (SURFACE K7) - and it never raises anything else.
"""
import argparse, importlib, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_check as S, surface_check as R
KEYS = ("prior", "T", "O", "N", "d", "closed", "bottom", "sources", "components", "table_sources",
        # kit v0.13: a v0.2 World is compared whole - kit v0.12 compared only the keys above, which a v0.2 dict mostly lacks
        "locals", "globals", "prior_global", "prior_local", "after", "counts", "counts_sha", "score", "falsifiers",
        "dplus", "fraction", "rate", "ops")

def same(a, b):
    return all(a.get(k) == b.get(k) for k in KEYS) and list(a["T"]) == list(b["T"]) and list(a["O"]) == list(b["O"])

def run_all(impl, seed, n_worlds, n_mutations=3000):
    sys.path.insert(0, os.path.abspath(impl))
    surf = importlib.import_module("wald.surface"); refusals = importlib.import_module("wald.refusals"); world_m = importlib.import_module("wald.world")
    okd, pod = os.path.join(HERE, "packs/ok"), os.path.join(HERE, "packs/poison"); results = []
    def verdict(text):
        try: return "ACCEPTED", surf.check(text, data_dir=okd)
        except refusals.Refused as e: return e.name, None
        except Exception as e: return f"raised {type(e).__name__}: {e}", None
    for fn in sorted(f for f in os.listdir(okd) if f.endswith(".py")):
        text = open(os.path.join(okd, fn), encoding="utf-8", newline="").read(); want = R.check(text, {}, okd); name, got = verdict(text)
        good = name == "ACCEPTED" and same(got, want); note = name if name != "ACCEPTED" else ("" if good else "elaborates to a different World")
        if good:
            try: world_m.declare(got)
            except Exception as e: good, note = False, f"declare refuses it: {e}"
        if good and surf.census(text, data_dir=okd) != R.census(text, {}, okd): good, note = False, "census differs"
        results.append((f"R3 {fn}", good, note))
    for fn in sorted(os.listdir(pod)):
        text = open(os.path.join(pod, fn), encoding="utf-8", newline="").read(); want = {w.strip() for w in text.splitlines()[0].replace("# expect:", "").split("|")}
        name, _ = verdict(text); results.append((f"R2 {fn}", name in want, f"got {name}, wanted {sorted(want)}"))
    rng = random.Random(seed); bad = None
    for i in range(n_worlds):
        w = S.rand_world(rng); ren = {s: f"e{s[0]}z{s[1]}" for s in w["prior"]}
        w2 = {"prior": {ren[s]: p for s, p in w["prior"].items()}, "T": {t: {ren[s]: x for s, x in u.items()} for t, u in w["T"].items()},
              "O": {k: {"K": {ren[s]: r for s, r in a["K"].items()}, "price": a["price"], "once": a["once"], "ends": {o: {ren[s]: x for s, x in u.items()} for o, u in a["ends"].items()}} for k, a in w["O"].items()}}
        text = R.to_pack(w2, 2, 2); name, got = verdict(text)
        if name != "ACCEPTED" or any(got[k] != w2[k] for k in ("prior", "T", "O")) or list(got["T"]) != list(w2["T"]) or list(got["O"]) != list(w2["O"]): bad = bad or text
    results.append((f"R1 round trip on {n_worlds} random Worlds", bad is None, "" if bad is None else "first failing pack:\n" + bad))
    # R9 (kit v0.13)
    name, _ = verdict('world("\ud800", closed=True)\n')
    results.append(("R9 a raw lone surrogate handed over as text is NOT_A_DECLARATION (QUESTIONS.md Q17)", name == "NOT_A_DECLARATION", f"got {name}"))
    import counts_check as CC, sys as _sys
    from collections import Counter
    W = CC.reliability_world([S.F(9, 10), S.F(3, 5)], [S.F(1, 2), S.F(1, 2)], S.F(-2)); r9 = random.Random(1); recs = Counter()
    for _ in range(300):
        a_ = r9.choice(["a1", "a2"]); recs[((("ask", a_),), "say " + a_, a_ if r9.random() < 0.8 else {"a1": "a2", "a2": "a1"}[a_])] += 1
    W["counts"] = recs; W["counts_sha"] = CC.counts_sha(recs); W["score"] = CC.loo_score(W, recs)
    text = R.to_pack_v02(W); limit = _sys.get_int_max_str_digits(); name, got = verdict(text)
    results.append((f"R9 a Score of {len(R.decimal(W['score'].denominator))} digits reads, and Python's limit is still {limit}",
                    name == "ACCEPTED" and got.get("score") == W["score"] and _sys.get_int_max_str_digits() == limit, f"got {name}"))
    # R10 (kit v0.13)
    import mutations as MU
    pool = [(n, lbl, v) for n, t in MU.corpus() for lbl, v in MU.all_variants(n, t)]
    sample = random.Random(seed).sample(pool, min(n_mutations, len(pool))); worst = None; agree = 0
    for n, lbl, v in sample:
        try: want = R.check(v, {}, okd); wc = R.census(v, {}, okd)
        except R.Refused: want = None
        name, got = verdict(v)
        if want is None: good = name not in ("ACCEPTED",) and not name.startswith("raised")
        else: good = name == "ACCEPTED" and same(got, want) and surf.census(v, data_dir=okd) == wc
        agree += good
        if not good and worst is None: worst = f"{n} :: {lbl}: the reference {'refuses it' if want is None else 'accepts it'}, the implementation {name if name != 'ACCEPTED' else 'accepts it as ' + ('the same World' if same(got, want) else 'another World')}"
    results.append((f"R10 {len(sample)} mutations of the corpus: the reference's verdict, a World or a refusal, and no other exception", worst is None, f"{len(sample) - agree} differ; the first: {worst}"))
    return results

def main(impl, seed=1, n_worlds=150, n_mutations=3000):
    try: results = run_all(impl, seed, n_worlds, n_mutations)
    except Exception as e:
        import traceback; traceback.print_exc(); print("SURFACE KIT: could not run -", type(e).__name__, e); return False
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"surface: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

def standin(liar=False):
    """kit v0.13: the reference behind a stand-in `wald` package must pass this judge, and a reader that accepts every pack
    must fail it. Built in a temporary directory, as an implementation's source tree would be."""
    import tempfile, textwrap
    d = tempfile.mkdtemp(prefix="wald-standin-"); pkg = os.path.join(d, "wald"); os.makedirs(pkg)
    body = {"__init__.py": "", "refusals.py": "from surface_check import Refused\n", "world.py": "def declare(spec): return spec\n",
            "surface.py": textwrap.dedent(f"""
                import surface_check as R
                def check(text, data_dir="."):
                    {'return R.check(\'world("w", closed=True)\\nhorizon(1, source="elicited")\\ndepth(1, source="elicited")\\nspace({{"s": ["a"]}})\\nprior({{"a": 1}}, source="data")\\nutility({{"t": {{"a": 0}}}}, source="elicited")\\nprice({{}}, source="elicited")\\n\', {{}}, data_dir)' if liar else 'return R.check(text, {}, data_dir)'}
                def census(text, data_dir="."): return R.census(text, {{}}, data_dir)
                """)}
    for fn, text in body.items(): open(os.path.join(pkg, fn), "w").write(text)
    for m in [m for m in sys.modules if m == "wald" or m.startswith("wald.")]: del sys.modules[m]
    try: return main(d, 1, n_worlds=40, n_mutations=600)
    finally:
        for m in [m for m in sys.modules if m == "wald" or m.startswith("wald.")]: del sys.modules[m]
        sys.path[:] = [x for x in sys.path if x != os.path.abspath(d)]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl"); ap.add_argument("--seed", type=int, default=int(os.environ.get("KIT_SEED") or 1)); ap.add_argument("--standin", action="store_true")
    a = ap.parse_args()
    if a.standin:
        import io, contextlib
        good = standin()
        with contextlib.redirect_stdout(io.StringIO()): bad = standin(liar=True)
        print("stand-in: reference passes:", good, "| a reader that accepts every pack fails:", not bad)
        sys.exit(0 if good and not bad else 1)
    sys.exit(0 if main(a.impl, a.seed) else 1)
