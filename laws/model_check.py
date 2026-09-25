"""
model_check.py - a gate check: every World the references build or read - the whole corpus, every generator's random
Worlds - has the shape model.py states; and model.py itself type-checks when a checker is installed.
"""
import glob, os, random, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import model as M, counts_check as C, surface_check as SC
from spec_check import Refused

def main():
    fails, n = [], 0
    for f in sorted(glob.glob(os.path.join(HERE, "packs/ok/*.py"))):
        t = open(f, encoding="utf-8", newline="").read()
        if not any(k in t for k in ("globals(", "after(", "counts(")): continue
        W = SC.check(t, {}, os.path.dirname(f)); n += 1
        try: M.check_world(W)
        except M.ShapeError as e: fails.append(f"{os.path.basename(f)}: {e}")
    rng = random.Random(3)
    for _ in range(60):
        W = C.rand_world(rng)
        try: C.refuse(W)
        except Refused: continue
        n += 1
        try:
            M.check_world(W)
            for r in C.rand_records(W, rng, 4): M.check_record(r)
        except M.ShapeError as e: fails.append(f"random World: {e}")
    for maker in (C.router_world, C.two_world, C.stakes_world, C.oscillating_world, C.railed_world, C.falsified_refit_world, C.echo_world, C.colour_world):
        W = maker() if maker is not C.router_world else maker(False); n += 1
        try: M.check_world(W)
        except M.ShapeError as e: fails.append(f"{maker.__name__}: {e}")
    tc = shutil.which("mypy") if os.environ.get("WALD_TYPECHECK") else None      # opt-in: the shapes are checked at run time regardless
    if tc:
        r = subprocess.run([tc, "--ignore-missing-imports", os.path.join(HERE, "model.py")], capture_output=True, text=True)
        if r.returncode != 0: fails.append("mypy --strict model.py: " + r.stdout.strip().splitlines()[-1])
    for f in fails[:10]: print("FAIL", f)
    print(f"model: {n} Worlds checked against model.py" + ("; mypy on model.py" if tc else " at run time (WALD_TYPECHECK=1 adds mypy)") + "; "
          + ("MODEL PASSES" if not fails else f"MODEL FAILS ({len(fails)})"))
    return not fails

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
