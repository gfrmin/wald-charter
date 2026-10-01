"""
kit_seed.py - kit v0.14: the seed is spent before the implementation is in the process.
  python3 laws/kit_seed.py --standin
CI hands kit.py the seed as a file (wald's cage.yml), never through the environment. kit.py's prepare() reads the file,
deletes it, derives one seed per suite by a one-way hash, draws its own Worlds and drops the master seed - all before the
first import of the implementation. No process that runs implementation code has KIT_SEED in its environment: kit.py
refuses to run if it does, and the wire's tools/serve.py (the builder's code) gets PATH and PYTHONPATH and nothing else.
--standin proves it with a hunter: a stand-in implementation that looks for the seed everywhere a kernel could look
(/proc/self/environ, os.environ, argv, the seed file, every frame's locals, every container the collector knows), with
powers no linted kernel has. After prepare() it finds nothing, in the kit's process and in the wire's. On the old path
(KIT_SEED in the environment, the seed in a caller's locals, the server given the kit's environment) it finds the seed;
that is the poison, and it must be found.
The witness that forced this (wald, 2026-10-01): `pathlib.Path("/proc/self/environ").read_bytes()` in src/wald passed
the import lint and printed KIT_SEED; a tools/serve.py printing os.environ["KIT_SEED"] put it in the kit's FAIL line.
"""
import hashlib, os, secrets, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
SUITES = ("kit", "surface", "wordle", "wordle_big", "think", "wordle_think", "library", "counts")

def take(path):
    "Read the seed from the file CI wrote, and delete the file: nothing that runs later finds it there."
    with open(path, encoding="utf-8") as f: text = f.read().strip()
    os.unlink(path); return int(text)

def suite_seeds(master):
    "One seed per suite, by a one-way hash: no suite's seed, nor any RNG state built from it, gives back the master seed."
    return {s: int.from_bytes(hashlib.sha256(f"{master}:{s}".encode()).digest()[:8], "big") for s in SUITES}

HUNTER = r'''
import gc, hashlib, os, sys
_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_target, _path = open(os.path.join(_here, "target")).read().split()
def _hit(v): return hashlib.sha256(str(v).encode()).hexdigest() == _target
def _atoms(o):
    if isinstance(o, dict): return list(o.keys()) + list(o.values())
    if isinstance(o, (list, tuple, set, frozenset)): return list(o)
    d = getattr(o, "__dict__", None)
    return list(d.values()) if isinstance(d, dict) else []
def _small(v): return isinstance(v, int) and not isinstance(v, bool) or isinstance(v, str) and len(v) < 64
found = []
if any(_hit(e.split(b"=", 1)[-1].decode(errors="replace")) for e in open("/proc/self/environ", "rb").read().split(b"\0")):
    found.append("/proc/self/environ")
if any(_hit(v) for v in os.environ.values()): found.append("os.environ")
if any(_hit(v) or _hit(v.split("=", 1)[-1]) for v in sys.argv): found.append("argv")
if os.path.exists(_path): found.append("the seed file")
_f = sys._getframe()
while _f is not None:
    if any(_hit(v) for v in list(_f.f_locals.values()) if _small(v)): found.append("the locals of " + _f.f_code.co_name)
    _f = _f.f_back
if any(_hit(v) for o in gc.get_objects() for v in _atoms(o) if _small(v)): found.append("the heap")
print("HUNT " + ",".join(found), flush=True)
def make_agent(): return None
'''

def standin_impl(d, seed, path):
    "A stand-in src/ whose wald.kit_adapter hunts for `seed` on import; it is told only the seed's hash and the file's path."
    os.makedirs(os.path.join(d, "src", "wald"))
    open(os.path.join(d, "src", "wald", "__init__.py"), "w").close()
    with open(os.path.join(d, "src", "wald", "kit_adapter.py"), "w") as f: f.write(HUNTER)
    with open(os.path.join(d, "src", "target"), "w") as f: f.write(hashlib.sha256(str(seed).encode()).hexdigest() + " " + path)
    return os.path.join(d, "src")

def hunt(cmd, env):
    out = subprocess.run(cmd, env=env, capture_output=True, text=True)
    lines = [l for l in out.stdout.splitlines() if l.startswith("HUNT ")]
    if out.returncode != 0 or len(lines) != 2: return None, (out.stdout + out.stderr)[-600:]
    return [l[5:].split(",") if l[5:] else [] for l in lines], ""

def probe(mode, impl, path):
    "Run in a child: reach the import of the implementation the way kit.py does (or the old way), then run the wire's child."
    import importlib, kit_library
    if mode == "kit":
        import kit
        a, seeds, worlds = kit.prepare(["--impl", impl, "--seed-file", path, "--worlds", "3"])
        kit.load_agent(a.impl); env = kit_library.serve_env(impl)
    else:                                                            # the poison: kit v0.13's path
        seed = int(os.environ["KIT_SEED"])
        sys.path.insert(0, os.path.abspath(impl)); importlib.import_module("wald.kit_adapter")
        env = dict(os.environ, PYTHONPATH=os.path.abspath(impl))
    sys.stdout.flush()
    subprocess.run([sys.executable, "-c", "import wald.kit_adapter"], env=env, cwd=os.path.dirname(impl))

def standin():
    seed = secrets.randbits(70); results = []                        # not a constant: the probe loads this file
    for mode in ("kit", "old"):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "kit_seed"); impl = standin_impl(d, seed, path)
            with open(path, "w") as f: f.write(str(seed))
            env = {k: v for k, v in os.environ.items() if k != "KIT_SEED"}
            if mode == "old": env["KIT_SEED"] = str(seed)
            got, err = hunt([sys.executable, os.path.abspath(__file__), "--probe", mode, impl, path], env)
            if got is None: results.append((f"{mode}: the probe ran", False, err)); continue
            here, wire = got
            if mode == "kit":
                results.append(("S1 after prepare(), the implementation finds the seed nowhere in the kit's process", here == [], f"found it in {here}"))
                results.append(("S2 the wire's server, the builder's code, finds it nowhere in its own", wire == [], f"found it in {wire}"))
                results.append(("S3 the seed file is gone before the implementation is imported", os.path.exists(path) is False, "the file is still there"))
            else:
                need = {"/proc/self/environ", "os.environ", "the locals of probe"}
                results.append(("S4 poison: on kit v0.13's path the same hunter finds the seed (environment, a caller's locals)", need <= set(here), f"found only {here}"))
                results.append(("S5 poison: and the wire's server finds it in its environment", {"/proc/self/environ", "os.environ"} <= set(wire), f"found only {wire}"))
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"seed: {sum(g for _, g, _ in results)}/{len(results)} pass (the hunter finds nothing after prepare(), and finds the seed on the old path)")
    return all(g for _, g, _ in results)

if __name__ == "__main__":
    sys.path.insert(0, HERE)
    if sys.argv[1:2] == ["--probe"]: probe(*sys.argv[2:5])
    elif sys.argv[1:] == ["--standin"]: sys.exit(0 if standin() else 1)
    else: print(__doc__); sys.exit(2)
