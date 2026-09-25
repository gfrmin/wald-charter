"""
model_check.py - a gate check: every World the references build or read - the whole corpus, every generator's random
Worlds, the pinned Worlds, and (kit v0.13) every World the reference accepts from a mutation of the corpus - has the
shape model.py states and, since kit v0.13, its values: rows that are distributions, tables keyed by exactly Omega,
prices at least 0, a catch-all that gives every outcome mass (model.check_values). And a row written twice, under two
spellings of one key, is refused rather than silently merged (QUESTIONS.md Q10e). model.py itself type-checks when a
checker is installed.
"""
import glob, os, random, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import model as M, counts_check as C, surface_check as SC, mutations as MU
from spec_check import Refused

OK = os.path.join(HERE, "packs", "ok")
V02 = ("globals(", "after(", "counts(", "falsifiers(", 'of="counts"')

def full(W, what, fails):
    try: M.check_world(W); M.check_values(W)
    except M.ShapeError as e: fails.append(f"{what}: {e}")

def main():
    t0 = time.time(); fails, n = [], 0
    for f in sorted(glob.glob(os.path.join(OK, "*.py"))):
        t = open(f, encoding="utf-8", newline="").read()
        if not any(k in t for k in V02): continue
        W = SC.check(t, {}, OK); n += 1; full(W, os.path.basename(f), fails)
    rng = random.Random(3)
    for _ in range(60):
        W = C.rand_world(rng)
        try: C.refuse(W)
        except Refused: continue
        n += 1; full(W, "random World", fails)
        try:
            for r in C.rand_records(W, rng, 4): M.check_record(r)
        except M.ShapeError as e: fails.append(f"random record: {e}")
    for label, maker in C.PINNED.items():
        W = maker(); n += 1; full(W, f"the pinned World '{label}'", fails)
    # kit v0.13: the values of every World the reference accepts from a mutated v0.2 pack, and every key written twice refused
    accepted = twice = 0
    for name, text in MU.corpus():
        if any(k in text for k in V02):
            for label, v in MU.all_variants(name, text):
                try: W = SC.check(v, {}, OK)
                except Exception: continue
                if "locals" not in W: continue
                accepted += 1; full(W, f"{name} :: {label}, which the reference accepts", fails)
        for label, v in MU.spellings(text, MU.states_of(text) if name.startswith("ok/") else ()):
            twice += 1
            try: SC.check(v, {}, OK); fails.append(f"{name} :: {label}: a key written twice, and the reference accepts it (Q10e)")
            except Exception: pass
    tc = shutil.which("mypy") if os.environ.get("WALD_TYPECHECK") else None      # opt-in: the shapes are checked at run time regardless
    if tc:
        r = subprocess.run([tc, "--ignore-missing-imports", os.path.join(HERE, "model.py")], capture_output=True, text=True)
        if r.returncode != 0: fails.append("mypy --strict model.py: " + r.stdout.strip().splitlines()[-1])
    kinds = {}
    for f in fails: kinds.setdefault(f.split(": ", 1)[-1].split(" (")[0][:80] if " :: " in f else f[:80], []).append(f)
    for k, fs in list(kinds.items())[:24]: print(f"FAIL {len(fs)} x  {fs[0][:220]}")
    print(f"model: {n} Worlds, {accepted} accepted mutations and {twice} keys written twice checked against model.py in {time.time() - t0:.0f}s"
          + ("; mypy on model.py" if tc else " at run time (WALD_TYPECHECK=1 adds mypy)") + "; "
          + ("MODEL PASSES" if not fails else f"MODEL FAILS ({len(fails)})"))
    return not fails

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
