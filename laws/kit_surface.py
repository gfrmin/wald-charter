"""
kit_surface.py - kit v0.3: judges an implementation of the signed SURFACE page (tag surface-v0).
Called by kit.py; alone:  python3 laws/kit_surface.py --impl PATH_TO_src [--seed INT]
The implementation provides wald.surface.check(text, data_dir) -> World spec (INTERFACE.md), raising wald.refusals.Refused(name),
and wald.surface.census(text, data_dir) -> {source: count of quantities}.
R3  every pack in packs/ok elaborates to exactly the World the reference checker builds, with the same census, and `declare` accepts it.
R2  every pack in packs/poison is refused by (one of) the name(s) on its first line.
R1  random Worlds from a seed the builder never sees, printed as packs, elaborate back to the same World, menu order included.
"""
import argparse, importlib, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_check as S, surface_check as R
KEYS = ("prior", "T", "O", "N", "d", "closed", "bottom", "sources", "components", "table_sources")

def same(a, b):
    return all(a.get(k) == b.get(k) for k in KEYS) and list(a["T"]) == list(b["T"]) and list(a["O"]) == list(b["O"])

def run_all(impl, seed, n_worlds):
    sys.path.insert(0, os.path.abspath(impl))
    surf = importlib.import_module("wald.surface"); refusals = importlib.import_module("wald.refusals"); world_m = importlib.import_module("wald.world")
    okd, pod = os.path.join(HERE, "packs/ok"), os.path.join(HERE, "packs/poison"); results = []
    def verdict(text):
        try: return "ACCEPTED", surf.check(text, data_dir=okd)
        except refusals.Refused as e: return e.name, None
        except Exception as e: return f"raised {type(e).__name__}: {e}", None
    for fn in sorted(f for f in os.listdir(okd) if f.endswith(".py")):
        text = open(os.path.join(okd, fn)).read(); want = R.check(text, {}, okd); name, got = verdict(text)
        good = name == "ACCEPTED" and same(got, want); note = name if name != "ACCEPTED" else ("" if good else "elaborates to a different World")
        if good:
            try: world_m.declare(got)
            except Exception as e: good, note = False, f"declare refuses it: {e}"
        if good and surf.census(text, data_dir=okd) != R.census(text, {}, okd): good, note = False, "census differs"
        results.append((f"R3 {fn}", good, note))
    for fn in sorted(os.listdir(pod)):
        text = open(os.path.join(pod, fn)).read(); want = {w.strip() for w in text.splitlines()[0].replace("# expect:", "").split("|")}
        name, _ = verdict(text); results.append((f"R2 {fn}", name in want, f"got {name}, wanted {sorted(want)}"))
    rng = random.Random(seed); bad = None
    for i in range(n_worlds):
        w = S.rand_world(rng); ren = {s: f"e{s[0]}z{s[1]}" for s in w["prior"]}
        w2 = {"prior": {ren[s]: p for s, p in w["prior"].items()}, "T": {t: {ren[s]: x for s, x in u.items()} for t, u in w["T"].items()},
              "O": {k: {"K": {ren[s]: r for s, r in a["K"].items()}, "price": a["price"], "once": a["once"], "ends": {o: {ren[s]: x for s, x in u.items()} for o, u in a["ends"].items()}} for k, a in w["O"].items()}}
        text = R.to_pack(w2, 2, 2); name, got = verdict(text)
        if name != "ACCEPTED" or any(got[k] != w2[k] for k in ("prior", "T", "O")) or list(got["T"]) != list(w2["T"]) or list(got["O"]) != list(w2["O"]): bad = bad or text
    results.append((f"R1 round trip on {n_worlds} random Worlds", bad is None, "" if bad is None else "first failing pack:\n" + bad))
    return results

def main(impl, seed=1, n_worlds=150):
    try: results = run_all(impl, seed, n_worlds)
    except Exception as e:
        import traceback; traceback.print_exc(); print("SURFACE KIT: could not run -", type(e).__name__, e); return False
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"surface: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--seed", type=int, default=int(os.environ.get("KIT_SEED") or 1))
    a = ap.parse_args(); sys.exit(0 if main(a.impl, a.seed) else 1)
