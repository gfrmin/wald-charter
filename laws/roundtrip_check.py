"""
roundtrip_check.py - a gate check (kit v0.13): what the reference plate writes, the reference reads back. For every World
the check runs on - the corpus's v0.2 Worlds, random Worlds with some cells at zero, and counts_check.PINNED - it plays
the reference plate (kit_counts._RefWald) for one and two episodes against a door that answers every outcome each
kernel names, zero-mass ones included, and then:
  - every record the plate writes, and its falsifying record if it ended falsified, is realisable in the declaration
    that wrote it: the plate's own mechanics could write it (C2.S13, V2.7; QUESTIONS.md Q15);
  - the Counts of a plate that did not end falsified ship into their own declaration: digest, realisability, positivity
    and Score all accepted (C2.S13, C2.S14, V2.13);
  - the Counts and falsifying record of a plate that did end falsified ship into a refit of that declaration with the same
    mechanics and every named outcome given mass - the declaration a falsified plate travels to (C2.J26). They cannot
    ship into the declaration that wrote them: no Global value there holds a falsifier with the Counts it followed, and
    C2.S13 refuses Counts and falsifying records no Global value holds together (SURFACE v0.2 attack session 2, 1.2).
  python3 laws/roundtrip_check.py
"""
import glob, os, random, sys, time
from collections import Counter
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import counts_check as C, surface_check as SC, kit_counts as KC
from spec_check import Refused

class _Need(Exception): pass

def named(W, act, end):
    "every outcome the door may report: every outcome the act's kernel names; for the After-act, those its kernel names under the end reached"
    if act in W["O"] and not (W.get("after") and act == W["after"].get("name", "after") and end is not None):
        return sorted({o for row in W["O"][act]["K"].values() for o in row}, key=repr)
    return sorted({o for row in W["after"]["K"][end].values() for o in row}, key=repr)

def plates(W, episodes):
    "(Counts written, falsifying record or None) for every run of the reference plate over every door answer"
    out = []
    def run(script):
        plate = KC._RefWald.plate(W); it = iter(script); seen = {"end": None, "last": None}
        after = W["after"].get("name", "after") if W.get("after") else None
        class Door(KC._RefWald.Door):
            def outcome(self, act):
                end = None
                if act == after and (seen["end"] is not None or seen["last"] is not None):
                    k, o = seen["last"] or (None, None)
                    end = seen["end"] if seen["end"] is not None else f"end:{k}={o}"
                try: o = next(it)
                except StopIteration: raise _Need((act, end))
                if end is None: seen["last"] = (act, o)
                else: seen["end"] = seen["last"] = None
                return o
            def fire(self, act): seen["end"] = act
        try:
            for _ in range(episodes):
                r = plate.run(Door())
                if "FALSIFIED" in str(r.status): break
            out.append((plate.counts(), plate.falsifier()))
        except _Need as e:
            act, end = e.args[0]
            for o in named(W, act, end): run(script + [o])
    run([])
    return out

def bare(W):
    "the declaration without what it ships"
    return {k: v for k, v in W.items() if k not in ("counts", "counts_sha", "score", "falsifiers")}

def refit(W, eps=F(1, 10)):
    "the same mechanics, every kernel mixed with the uniform law on the outcomes it names: every record it could write is possible"
    V = dict(W)
    mix = lambda K: {s: {o: (1 - eps) * row.get(o, F(0)) + eps / len(outs) for o in outs} for s, row in K.items()
                     for outs in [sorted({o for r in K.values() for o in r}, key=repr)]}
    V["O"] = {k: {**a, "K": mix(a["K"])} for k, a in W["O"].items()}
    if W.get("after"): V["after"] = {**W["after"], "K": {e: mix(K) for e, K in W["after"]["K"].items()}}
    return V

def ship(W, counts, falsifiers):
    V = bare(W); V["counts"] = counts; V["counts_sha"] = C.counts_sha(counts, falsifiers)
    if falsifiers: V["falsifiers"] = list(falsifiers)
    V["score"] = C.loo_score(V, counts, falsifiers) if C.expressible(V, counts, falsifiers) else F(1)
    return V

def verdict(V):
    try: C.refuse(V); return "accepted"
    except Refused as e: return f"refused {e}"
    except Exception as e: return f"raised {type(e).__name__}"

def sparse(rng):
    "a random World with a cell of one row at zero, so that some door answers falsify it"
    W = C.rand_world(rng)
    k = sorted(W["O"])[0]; s = sorted(W["O"][k]["K"])[0]; row = W["O"][k]["K"][s]
    o = sorted(row)[0]; rest = [x for x in row if x != o]
    W["O"][k]["K"][s] = {o: F(0), **{x: F(1, len(rest)) for x in rest}}
    return W

def worlds():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "packs/ok/*.py"))):
        t = open(f, encoding="utf-8", newline="").read()
        if any(k in t for k in ("globals(", "after(", "counts(")): out.append((os.path.basename(f), SC.check(t, {}, os.path.join(HERE, "packs/ok"))))
    rng = random.Random(13)
    while len(out) < 50:
        W = sparse(rng) if len(out) % 2 else C.rand_world(rng)
        try: C.refuse(W)
        except Refused: continue
        out.append((f"random-{len(out)}", W))
    out += [(label, maker()) for label, maker in C.PINNED.items()]
    return out

def main():
    t0 = time.time(); fails, n = [], 0
    for label, W in worlds():
        fbase = list(W.get("falsifiers", ()))
        for episodes in (1, 2):
            for counts, f in plates(W, episodes):
                n += 1
                bad = [r for r in counts if not C.realisable(W, r)]
                if bad: fails.append(("the plate writes a record its own declaration could not have written", f"{label}: {bad[0]}")); continue
                if f is not None and not C.realisable(W, f, True):
                    fails.append(("the plate writes a falsifier its own declaration could not have written", f"{label}: {f}")); continue
                allc = counts                       # the plate's Counts start from those the declaration ships
                if f is None: v = verdict(ship(W, allc, fbase)); where = "its own declaration"
                else: v = verdict(ship(refit(W), allc, fbase + [f])); where = "a refit with every named outcome possible"
                if v != "accepted": fails.append((f"a plate's Counts do not ship into {where}", f"{label}: {dict(counts)}, {f}: {v}"))
    kinds = {}
    for k, f in fails: kinds.setdefault(k, []).append(f)
    for k, fs in kinds.items(): print(f"FAIL {len(fs)} x {k}; the first: {fs[0][:220]}")
    print(f"roundtrip: {n} plates on {len(worlds())} Worlds in {time.time() - t0:.0f}s; " + ("ROUNDTRIP PASSES" if not fails else f"ROUNDTRIP FAILS ({len(fails)})"))
    return not fails

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
