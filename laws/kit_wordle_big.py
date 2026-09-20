"""
kit_wordle_big.py - kit v0.6: exact fast paths (CHARTER E2), judged on Wordle at 200 words.
  python3 laws/kit_wordle_big.py --impl PATH_TO_src [--seed INT] [--episodes 5]
B0  the specialised oracle (wordle_oracle.py) agrees with the general oracle, move by move, on the 40-word World. Only then is it trusted.
B1  packs/wordle200/d1.py and d2.py are lawful, ARE Wordle on laws/wordle/words200.txt (every feedback row, claims, loss -7, horizon 5,
    closed, nothing fitted) and differ only in their declared depth: 1 and 2.
B2  on answers drawn from a seed the builder never sees, at each depth, every act the kernel plays is the oracle's. Exact means exact:
    a fast path that changes one act fails here.
It prints, for the sampled answers, the mean attempts at each depth: the price of the floor, measured.
"""
import argparse, importlib, os, random, sys, time
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_check as S, surface_check as R
from wordle_oracle import Oracle, feedback
LOSS = -7

def world40(words):
    n = len(words); ends = {"ggggg": {a: F(0) for a in words}}
    return {"prior": {w: F(1, n) for w in words}, "T": {"claim " + g: {a: F(-1) if a == g else F(LOSS) for a in words} for g in words},
            "O": {g: {"K": {a: {feedback(g, a): F(1)} for a in words}, "price": F(1), "once": True, "ends": ends} for g in words}}

def run_all(impl, seed, episodes):
    results = []; rng = random.Random(seed)
    def check(tag, cond, note=""): results.append((tag, bool(cond), note))
    w40 = open(os.path.join(HERE, "wordle", "words.txt")).read().split(); W = world40(w40); orc = Oracle(w40, LOSS); good = True
    for answer in rng.sample(w40, 2):
        b = dict(W["prior"]); used = frozenset(); n = 5
        for a in orc.play(answer, 5, 1):
            if S.REF.decide(b, W, min(1, n), used) != a: good = False
            if a.startswith("claim ") or feedback(a, answer) == "ggggg": break
            b = S.REF.condition(b, W["O"][a]["K"], feedback(a, answer)); used |= {a}; n -= 1
    check("B0 the specialised oracle agrees with the general oracle on the 40-word World", good)
    if not good: return results
    words = open(os.path.join(HERE, "wordle", "words200.txt")).read().split(); n = len(words)
    root = os.path.dirname(os.path.abspath(impl)); pdir = os.path.join(root, "packs", "wordle200")
    sys.path.insert(0, os.path.abspath(impl))
    surf = importlib.import_module("wald.surface"); world_m = importlib.import_module("wald.world"); E = importlib.import_module("wald.episode")
    class Game(E.Door):
        def __init__(self, answer): self.answer = answer
        def outcome(self, act): return feedback(act, self.answer)
        def fire(self, act): pass
    big = Oracle(words, LOSS); answers = rng.sample(words, episodes); specs = {}
    for d in (1, 2):
        text = open(os.path.join(pdir, f"d{d}.py")).read(); w = R.check(text, {}, pdir); specs[d] = w; census = R.census(text, {}, pdir)
        got = surf.check(text, data_dir=pdir)
        check(f"B1 d{d}: the implementation elaborates the pack to the reference's World", all(got.get(k) == w.get(k) for k in ("prior", "T", "O", "N", "d", "closed")))
        ok2 = (list(w["prior"]) == words and all(p == F(1, n) for p in w["prior"].values()) and list(w["O"]) == words and list(w["T"]) == ["claim " + g for g in words]
               and all(w["T"]["claim " + g] == {a: F(-1) if a == g else F(LOSS) for a in words} for g in words)
               and all(w["O"][g]["price"] == 1 and w["O"][g]["once"] and w["O"][g]["ends"] == {"ggggg": {a: F(0) for a in words}} for g in words)
               and w["N"] == 5 and w["d"] == d and w.get("closed") is True and census["fitted"] == 0)
        wrong = [(g, a) for g in words for a in words if {o: p for o, p in w["O"][g]["K"][a].items() if p != 0} != {feedback(g, a): F(1)}]
        check(f"B1 d{d}: the pack is Wordle on the 200 words, loss {LOSS}, horizon 5, depth {d}, closed, nothing fitted", ok2 and not wrong, f"{len(wrong)} wrong feedback rows")
        world = world_m.declare(got); t0 = time.time(); total = 0
        for answer in answers:
            r = E.run(world, Game(answer)); want = big.play(answer, 5, d); total += len(want)
            check(f"B2 d{d}, answer {answer!r}: the oracle's acts {want}", list(r.acts) == want, f"played {list(r.acts)}")
        print(f"wordle200 d={d}: {episodes} sampled answers, {total / max(episodes, 1):.2f} attempts on average; the kernel took {time.time() - t0:.1f} s")
    same = {k: specs[1][k] == specs[2][k] for k in ("prior", "T", "O", "N")}
    check("B1 the two packs differ only in their depth", all(same.values()), str(same))
    return results

def main(impl, seed=1, episodes=5):
    try: results = run_all(impl, seed, episodes)
    except Exception as e:
        import traceback; traceback.print_exc(); print("WORDLE-200 KIT: could not run -", type(e).__name__, e); return False
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"wordle200: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--seed", type=int, default=int(os.environ.get("KIT_SEED") or 1)); ap.add_argument("--episodes", type=int, default=5)
    a = ap.parse_args(); sys.exit(0 if main(a.impl, a.seed, a.episodes) else 1)
