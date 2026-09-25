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
    names = ["declare", "run", "Door", "report", "Display", "refusals", "load_pack", "from_json", "to_json", "law"]
    check("L1 wald exposes " + ", ".join(names), all(hasattr(wald, n) for n in names), f"missing {[n for n in names if not hasattr(wald, n)]}")
    if not all(hasattr(wald, n) for n in names):
        return report(results)
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

def report(results):
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"library: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(); sys.exit(0 if main(a.impl, a.seed) else 1)
