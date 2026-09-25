"""
realise_check.py - a gate check (kit v0.13): C2.S13's "could have written every record itself" is v0's episode loop,
not a list of conditions. For every World the check runs on - the corpus's v0.2 Worlds, random Worlds, and the pinned
Worlds of counts_check.PINNED - it enumerates what the loop can write whatever its policy and whatever the door reports:
every design of counts_check.designs, every outcome each kernel names (zero-mass ones included: the door may report
them, and that is how a World is falsified), an ending outcome ending the draws and becoming the end (counts_check._walk's
rule), a terminal otherwise, and an after-report, over the After-act's outcomes under that end, exactly when one is
declared. A falsifying record (V2.7) is any non-empty prefix of those draws - its last draw the report that falsified,
an ending outcome included (QUESTIONS.md Q15) - or a full record with an after-report.

Then `counts_check.realisable` must say yes to exactly these: to every record and falsifier the loop writes, and to none
of their perturbations the loop cannot write - a draw removed, doubled or swapped, the end or the after-report
replaced, an outcome no kernel names (QUESTIONS.md Q14).
  python3 laws/realise_check.py
"""
import glob, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import counts_check as C, surface_check as SC
from spec_check import Refused

def loop(W):
    "(records, falsifiers): everything v0's loop can write in this declaration"
    named = {k: sorted({o for row in a["K"].values() for o in row}, key=repr) for k, a in W["O"].items()}
    after = W.get("after")
    reports = lambda end: sorted({o for row in after["K"][end].values() for o in row}, key=repr) if after else [None]
    recs, fals = set(), set()
    def finish(draws, end):
        for oa in reports(end):
            recs.add((draws, end, oa))
            if oa is not None: fals.add((draws, end, oa))
    for design in C.designs(W):
        def go(i, draws):
            if i == len(design):
                for t in W["T"]: finish(draws, t)
                return
            k = design[i]
            for o in named[k]:
                d = draws + ((k, o),); fals.add((d, None, None))
                if o in W["O"][k].get("ends", ()): finish(d, f"end:{k}={o}")
                else: go(i + 1, d)
        go(0, ())
    return recs, fals

def perturb(r, W):
    "records near a written one: most of them no episode of W can write"
    draws, end, oa = r
    ends = sorted(C.ends_of(W)) + [None]
    outs = sorted({o for K in W["after"]["K"].values() for row in K.values() for o in row}) + [None] if W.get("after") else [None, "x"]
    for i in range(len(draws)):
        yield (draws[:i] + draws[i + 1:], end, oa)
        yield (draws[:i + 1] + draws[i:], end, oa)
        if i + 1 < len(draws): yield (draws[:i] + (draws[i + 1], draws[i]) + draws[i + 2:], end, oa)
        yield (draws[:i] + ((draws[i][0], "no such outcome"),) + draws[i + 1:], end, oa)
    for e in ends: yield (draws, e, oa)
    for o in outs: yield (draws, end, o)
    for k in sorted(W["O"]): yield (draws + ((k, sorted({o for row in W["O"][k]["K"].values() for o in row}, key=repr)[0]),), end, oa)

def worlds():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "packs/ok/*.py"))):
        t = open(f, encoding="utf-8", newline="").read()
        if any(k in t for k in ("globals(", "after(", "counts(")): out.append((os.path.basename(f), SC.check(t, {}, os.path.join(HERE, "packs/ok"))))
    rng = random.Random(9)
    while len(out) < 60:
        W = C.rand_world(rng)
        try: C.refuse(W)
        except Refused: continue
        out.append((f"random-{len(out)}", W))
    out += [(label, maker()) for label, maker in C.PINNED.items()]
    return out

def why(W, r, falsifier, want):
    "a name for the kind of disagreement, so the failures group by cause"
    draws, end, oa = r
    named = {k: {o for row in a["K"].values() for o in row} for k, a in W["O"].items()}
    ending = lambda d: d[1] in W["O"].get(d[0], {}).get("ends", ())
    if any(k in named and o not in named[k] for k, o in draws): return "an outcome no kernel names"
    if isinstance(end, str) and end.startswith("end:") and (not draws or end != f"end:{draws[-1][0]}={draws[-1][1]}"): return "an ending end its draws do not reach (Q14)"
    if falsifier and end is None and draws and ending(draws[-1]): return "a prefix whose falsifying report is an ending outcome (Q15)"
    if W.get("after") and oa is not None and end in W["after"]["K"] and oa not in {o for row in W["after"]["K"][end].values() for o in row}: return "an after-report the After-act never names"
    return "other"

def main():
    t0 = time.time(); fails, n = [], 0
    for label, W in worlds():
        recs, fals = loop(W)
        for falsifier, written in ((False, recs), (True, fals)):
            cands = set(written) | {p for r in written for p in perturb(r, W)}
            for r in cands:
                n += 1; want = r in written
                try: got = C.realisable(W, r, falsifier)
                except Exception as e: got = f"raised {type(e).__name__}"
                if got != want:
                    kind = "falsifier" if falsifier else "record"
                    fails.append((why(W, r, falsifier, want), f"{label}: the {kind} {r} - the loop {'writes' if want else 'cannot write'} it, realisable says {got}"))
    kinds = {}
    for k, f in fails: kinds.setdefault(k, []).append(f)
    for k, fs in kinds.items(): print(f"FAIL {len(fs)} x {k}; the first: {fs[0][:200]}")
    print(f"realise: {n} records and falsifiers on {len(worlds())} Worlds in {time.time() - t0:.0f}s; "
          + ("REALISE PASSES" if not fails else f"REALISE FAILS ({len(fails)})"))
    return not fails

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
