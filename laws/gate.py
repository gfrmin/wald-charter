"""
gate.py - every mechanical check, in one command. An attack session, a review or a signing happens only after it passes.
  python3 laws/gate.py
Reviews and attacks are the last resort for finding problems: what a machine can find, this finds first. The checks are
independent, so they run at once; each prints its own line, in the order below.
"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = [
    ("the charter's reference (CHARTER v0.2)", ["counts_check.py"]),
    ("the charter's reference, a second seed", ["counts_check.py", "--seed", "7", "--worlds", "60"]),
    ("the surface's reference and corpus (SURFACE v0 to v0.2)", ["surface_check.py"]),
    ("the v0.1 reference (the think act)", ["meta_check.py"]),
    ("SURFACE v0.2 traceability: rules stated once, every rule tested", ["page_check.py", os.path.join(HERE, "..", "SURFACE-v0.2.md")]),
    ("invariance: re-spelling, unnamed values, the text around names", ["invariance_check.py"]),
    ("V2.13 by a second encoder", ["encoding_check.py"]),
    ("every World has model.py's shapes and values", ["model_check.py"]),
    ("every mutation of the corpus: a World or a named refusal", ["mutation_check.py"]),
    ("realisability is v0's loop", ["realise_check.py"]),
    ("what the reference plate writes, the reference reads back", ["roundtrip_check.py"]),
    ("the kit's counts judge, stand-in", ["kit_counts.py", "--standin"]),
]
def main():
    t = time.time()
    procs = [(label, subprocess.Popen([sys.executable] + cmd, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)) for label, cmd in CHECKS]
    ok = True
    for label, p in procs:
        out, err = p.communicate()
        last = (out.strip().splitlines() or ["(no output)"])[-1]
        good = p.returncode == 0; ok &= good
        print(f"{'pass' if good else 'FAIL'}  {label:62s} {last[:100]}")
        if not good: print("\n".join("      " + l for l in (out + err).strip().splitlines()[-8:]))
    print(f"{'GATE PASSES' if ok else 'GATE FAILS'} ({len(CHECKS)} checks, {time.time() - t:.0f}s)"); return ok
if __name__ == "__main__":
    sys.exit(0 if main() else 1)
