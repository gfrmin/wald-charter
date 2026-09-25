"""
gate.py - every mechanical check, in one command. An attack session, a review or a signing happens only after it passes.
  python3 laws/gate.py
Reviews and attacks are the last resort for finding problems: what a machine can find, this finds first.
"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = [
    ("the charter's reference (CHARTER v0.2)", ["counts_check.py"]),
    ("the charter's reference, a second seed", ["counts_check.py", "--seed", "7", "--worlds", "60"]),
    ("the surface's reference and corpus (SURFACE v0 to v0.2)", ["surface_check.py"]),
    ("the v0.1 reference (the think act)", ["meta_check.py"]),
    ("SURFACE v0.2 traceability: rules stated once, every rule tested", ["page_check.py", os.path.join(HERE, "..", "SURFACE-v0.2.md")]),
    ("invariance under re-spelling", ["invariance_check.py"]),
    ("V2.13 by a second encoder", ["encoding_check.py"]),
    ("the kit's counts judge, stand-in", ["kit_counts.py", "--standin"]),
]
def main():
    ok = True
    for label, cmd in CHECKS:
        t = time.time(); r = subprocess.run([sys.executable] + cmd, cwd=HERE, capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        good = r.returncode == 0; ok &= good
        print(f"{'pass' if good else 'FAIL'}  {label:62s} {time.time() - t:5.1f}s  {last[:90]}")
        if not good: print("\n".join("      " + l for l in (r.stdout + r.stderr).strip().splitlines()[-8:]))
    print("GATE PASSES" if ok else "GATE FAILS"); return ok
if __name__ == "__main__":
    sys.exit(0 if main() else 1)
