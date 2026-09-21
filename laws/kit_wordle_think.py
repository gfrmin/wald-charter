"""
kit_wordle_think.py - kit v0.9: the think act on Wordle (CHARTER v0.1, SURFACE v0.1), judged on two lexicons.
  python3 laws/kit_wordle_think.py --impl PATH_TO_src [--seed INT] [--episodes 5]
T0  the meta oracle (wordle_meta_oracle.py) agrees with meta_check.DecidePlus -- act, bucket and cost at every node -- on a small
    Wordle World (the first 8 of the 40 words). Only then is it trusted at 124 and 200.
T1  packs/wordle200/adaptive.py and packs/twins/adaptive.py are lawful, ARE Wordle on words200.txt / twins124.txt (loss -7, horizon 5,
    depth 1, closed), declare depth_plus 2, fraction F, the fitted cost table COST[lexicon] cell by cell, rate R, and its score.
T2  on answers drawn from a seed the builder never sees, every act the kernel plays is the oracle's, every step lands in the oracle's
    bucket, and the thought charged is the oracle's.
T3  prints, for each lexicon, the five E3 curves along the kit's grid of r (the oracle's; exact), and the kernel's episodes at R.
The numbers below are the author's, from RESULTS-005c-prelim.md: the owner ruled F = 1/2 and the sweep; R is the author's proposal.
"""
import argparse, importlib, os, random, sys, time
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_check as S, surface_check as R_, meta_check as M
from wordle_oracle import feedback
from wordle_meta_oracle import MetaOracle
LOSS = -7; FRACTION = F(1, 2); RATE = F(1, 10**7); GRID = [F(0), F(1, 10**8), F(3, 10**8), F(1, 10**7), F(3, 10**7), F(1, 10**6)]
COST = {"words200": (F("11930007676619916058/36661206089336597"), F("-43860132154564000/1929537162596663"), F(41, 200)),
        "twins124": (F("99613375741023143/629231233233738"), F("22716401291570095/314615616616869"), F(149, 500))}
def ops_table(a, b, n): return {s: a * s * s + b * s ** 3 / n for s in range(1, n + 1)}

def wordle_world(words):
    n = len(words); ends = {"ggggg": {a: F(0) for a in words}}
    return {"prior": {w: F(1, n) for w in words}, "T": {"claim " + g: {a: F(-1) if a == g else F(LOSS) for a in words} for g in words},
            "O": {g: {"K": {a: {feedback(g, a): F(1)} for a in words}, "price": F(1), "once": True, "ends": ends} for g in words}}

def prove_small(rng, results):
    "T0 on 8 words: every node of every answer, at F and at a rate that makes the root thought bite"
    w8 = open(os.path.join(HERE, "wordle", "words.txt")).read().split()[:8]; n = len(w8)
    ops = ops_table(F(300), F(0), n); rate = F(1, 4000)          # root thought ~ 300*64 ops -> c ~ 4.8 utility; children cheap
    W = {**wordle_world(w8), "N": 5, "d": 1, "dplus": 2, "fraction": FRACTION, "rate": rate, "ops": ops}
    O = MetaOracle(w8, LOSS, FRACTION, ops, rate); good = True; nodes = 0
    for answer in w8:
        C, k, used, b = frozenset(range(n)), 5, frozenset(), W["prior"]
        while True:
            (kind, i), how, paid = O.step(C, k); ra, rhow, rpaid = M.DPLUS.step(b, W, k, used); nodes += 1
            mine = ("claim " + w8[i]) if kind == "claim" else w8[i]
            if (mine, how, paid) != (ra, rhow, rpaid): good = False; break
            if kind == "claim": break
            o = O.fb[i][w8.index(answer)]
            if o == O.green: break
            C = frozenset(x for x in C if O.fb[i][x] == o); b = S.REF.condition(b, W["O"][w8[i]]["K"], feedback(w8[i], answer)); used |= {w8[i]}; k -= 1
    va = F(O.value(O.adaptive()), n); vo = F(O.omniscient(), n)
    good &= va == M.value_net(M.DPLUS, W) and vo == M.omniscient_value(W)
    results.append(("T0 the meta oracle agrees with meta_check.DecidePlus on the 8-word World, every node, and on both values", good, f"{nodes} nodes"))
    return good

def run_all(impl, seed, episodes):
    results = []; rng = random.Random(seed)
    def check(tag, cond, note=""): results.append((tag, bool(cond), note))
    if not prove_small(rng, results): return results
    root = os.path.dirname(os.path.abspath(impl)); sys.path.insert(0, os.path.abspath(impl))
    surf = importlib.import_module("wald.surface"); world_m = importlib.import_module("wald.world"); E = importlib.import_module("wald.episode")
    class Game(E.Door):
        def __init__(self, answer): self.answer = answer
        def outcome(self, act): return feedback(act, self.answer)
        def fire(self, act): pass
    for lex, pack in (("words200", "wordle200"), ("twins124", "twins")):
        words = open(os.path.join(HERE, "wordle", f"{lex}.txt")).read().split(); n = len(words); a, b, score = COST[lex]; ops = ops_table(a, b, n)
        pdir = os.path.join(root, "packs", pack); text = open(os.path.join(pdir, "adaptive.py")).read()
        w = R_.check(text, {}, pdir); census = R_.census(text, {}, pdir); got = surf.check(text, data_dir=pdir)
        check(f"T1 {lex}: the implementation elaborates the pack to the reference's World", all(got.get(k) == w.get(k) for k in ("prior", "T", "O", "N", "d", "closed", "dplus", "fraction", "rate", "ops", "score")))
        shape = (list(w["prior"]) == words and all(p == F(1, n) for p in w["prior"].values()) and list(w["O"]) == words and list(w["T"]) == ["claim " + g for g in words]
                 and all(w["T"]["claim " + g] == {x: F(-1) if x == g else F(LOSS) for x in words} for g in words)
                 and all(w["O"][g]["price"] == 1 and w["O"][g]["once"] and w["O"][g]["ends"] == {"ggggg": {x: F(0) for x in words}} for g in words)
                 and w["N"] == 5 and w["d"] == 1 and w.get("closed") is True)
        wrong = [(g, x) for g in words for x in words if {o: p for o, p in w["O"][g]["K"][x].items() if p != 0} != {feedback(g, x): F(1)}]
        check(f"T1 {lex}: the pack is Wordle on the {n} words, loss {LOSS}, horizon 5, depth 1, closed", shape and not wrong, f"{len(wrong)} wrong feedback rows")
        meta = (w.get("dplus") == 2 and w.get("fraction") == FRACTION and w.get("rate") == RATE and w.get("ops") == ops
                and w.get("score") == {"cost": score} and w["table_sources"].get("fraction") == "elicited" and w["table_sources"].get("cost") == "fitted")
        check(f"T1 {lex}: depth_plus 2, fraction {FRACTION}, rate {RATE}, the fitted cost table cell for cell with its score {score}", meta,
              f"got dplus {w.get('dplus')}, f {w.get('fraction')}, r {w.get('rate')}, score {w.get('score')}, cost source {w['table_sources'].get('cost')}")
        O = MetaOracle(words, LOSS, FRACTION, ops, RATE); world = world_m.declare(got); t0 = time.time(); att = 0
        for answer in rng.sample(words, episodes):
            r = E.run(world, Game(answer)); acts, hows, paid, k, right = O.episode(answer); att += k
            steps = {h: hows.count(h) for h in ("struck_n", "struck_cap", "refused", "think")}
            check(f"T2 {lex}, answer {answer!r}: the oracle's acts {acts}", list(r.acts) == acts, f"played {list(r.acts)}")
            check(f"T2 {lex}, answer {answer!r}: the oracle's buckets {steps} and thought {paid}", dict(r.steps) == steps and r.thought == paid, f"got {dict(r.steps)}, thought {r.thought}")
        print(f"{lex} adaptive at r={float(RATE):.0e}: {episodes} sampled answers, {att / max(episodes, 1):.2f} attempts on average; the kernel took {time.time() - t0:.1f} s")
        print(f"{lex} E3 curves (oracle, exact; utility per episode):  {'r':>8} {'fixed1':>9} {'always2':>9} {'adaptive':>9} {'omnisc':>9}")
        base = O
        for r in GRID:
            Or = MetaOracle(words, LOSS, FRACTION, ops, r); Or.fb = base.fb; Or.memo = base.memo; cv = Or.curves()
            print(f"{'':43s}{float(r):8.0e} {float(cv['fixed d=1']):9.4f} {float(cv['always d=2']):9.4f} {float(cv['adaptive']):9.4f} {float(cv['omniscient']):9.4f}")
    return results

def main(impl, seed=1, episodes=5):
    try: results = run_all(impl, seed, episodes)
    except Exception as e:
        import traceback; traceback.print_exc(); print("WORDLE-THINK KIT: could not run -", type(e).__name__, e); return False
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"wordle-think: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--seed", type=int, default=int(os.environ.get("KIT_SEED") or 1)); ap.add_argument("--episodes", type=int, default=5)
    a = ap.parse_args(); sys.exit(0 if main(a.impl, a.seed, a.episodes) else 1)
