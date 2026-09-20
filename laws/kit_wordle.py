"""
kit_wordle.py - kit v0.5: judges the first domain pack, packs/wordle/pack.py in the builder's repository.
  python3 laws/kit_wordle.py --impl PATH_TO_src [--seed INT] [--episodes 6]
W1  the pack is lawful (reference checker) and the implementation elaborates it to the same World.
W2  the pack IS Wordle on laws/wordle/words.txt: the states are the words, the prior is uniform, every word is a `once` guess at
    price 1, each guess's kernel is the game's feedback (computed here, independently), all-green ends the episode at 0.
    The terminal acts are the claims "claim <word>": -1 if right, the same loss below -6 if wrong. Five guesses and a claim make
    Wordle's six attempts, so the horizon is 5. The World is closed and nothing is `fitted`.
    (A World whose only terminal act is "give up" is degenerate at depth 1: one look ahead sees a 1-in-n hit and then the loss,
    so the agent gives up at once. The oracle and the kernel agree on that. Stopping has to be worth something: hence claims.)
W3  on answers drawn from a seed the builder never sees, every act the kernel plays is the oracle's decide_min(d,n) at that belief,
    and every episode ends all-green within the horizon.
"""
import argparse, importlib, os, random, sys
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_check as S, surface_check as R

def feedback(guess, answer):
    "Wordle's rule, duplicate letters included: greens first, then yellows while unmatched copies of the letter remain."
    out = ["-"] * 5; left = {}
    for g, a in zip(guess, answer):
        if g != a: left[a] = left.get(a, 0) + 1
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a: out[i] = "g"
        elif left.get(g, 0) > 0: out[i] = "y"; left[g] -= 1
    return "".join(out)

def run_all(impl, seed, episodes):
    root = os.path.dirname(os.path.abspath(impl)); pdir = os.path.join(root, "packs", "wordle"); results = []
    def check(tag, cond, note=""): results.append((tag, bool(cond), note))
    text = open(os.path.join(pdir, "pack.py")).read(); words = open(os.path.join(HERE, "wordle", "words.txt")).read().split()
    w = R.check(text, {}, pdir); census = R.census(text, {}, pdir)
    sys.path.insert(0, os.path.abspath(impl))
    surf = importlib.import_module("wald.surface"); world_m = importlib.import_module("wald.world"); E = importlib.import_module("wald.episode")
    got = surf.check(text, data_dir=pdir)
    check("W1 the implementation elaborates the pack to the reference's World", all(got.get(k) == w.get(k) for k in ("prior", "T", "O", "N", "d", "closed")))
    n = len(words)
    check("W2 the states are the words", list(w["prior"]) == words and len(set(words)) == n, f"{len(w['prior'])} states")
    check("W2 the prior is uniform", all(p == F(1, n) for p in w["prior"].values()))
    losses = {u for g in words for a, u in w["T"].get("claim " + g, {}).items() if a != g}
    check("W2 the terminal acts are the claims, in the list's order: -1 if right, one loss below -6 if wrong",
          list(w["T"]) == ["claim " + g for g in words] and all(w["T"]["claim " + g][g] == -1 for g in words) and len(losses) == 1 and max(losses) < -6, f"losses {sorted(losses)[:3]}")
    check("W2 every word is a guess, in the list's order", list(w["O"]) == words)
    bad = [g for g in words if g in w["O"] and (w["O"][g]["price"] != 1 or not w["O"][g]["once"] or w["O"][g]["ends"] != {"ggggg": {a: F(0) for a in words}})]
    check("W2 every guess is `once`, costs 1, and all-green ends the episode at 0", not bad, str(bad[:3]))
    wrong = [(g, a) for g in words if g in w["O"] for a in words if {o: p for o, p in w["O"][g]["K"][a].items() if p != 0} != {feedback(g, a): F(1)}]
    check("W2 every kernel row is the game's feedback", not wrong, f"{len(wrong)} wrong, first {wrong[:2]}")
    check("W2 horizon 5, closed, nothing fitted", w["N"] == 5 and w.get("closed") is True and census["fitted"] == 0, f"N={w['N']} census={census}")
    world = world_m.declare(got); d = w["d"]
    class Game(E.Door):
        def __init__(self, answer): self.answer = answer
        def outcome(self, act): return feedback(act, self.answer)
        def fire(self, act): pass
    rng = random.Random(seed); total = 0
    for answer in rng.sample(words, episodes):
        r = E.run(world, Game(answer)); b = dict(w["prior"]); used = frozenset(); left = w["N"]; good = True; note = ""
        for a in r.acts:
            want = S.REF.decide(b, w, min(d, left), used)
            if a != want: good, note = False, f"answer {answer}: played {a!r} where the oracle plays {want!r}"; break
            if a in w["T"]: break
            o = feedback(a, answer)
            if o == "ggggg": break
            b = S.REF.condition(b, w["O"][a]["K"], o); used = used | {a}; left -= 1
        good = good and ((r.status == "ENDED" and r.acts[-1] == answer) or (r.status == "TERMINAL" and r.acts[-1] == "claim " + answer))
        total += len(r.acts); check(f"W3 answer {answer!r}: the oracle's act at every step, solved in {len(r.acts)}", good, note or f"status {r.status}, acts {r.acts}")
    print(f"wordle: depth {d}; {episodes} sampled answers solved in {total / episodes:.2f} attempts on average; census {census}")
    return results

def main(impl, seed=1, episodes=6):
    try: results = run_all(impl, seed, episodes)
    except Exception as e:
        import traceback; traceback.print_exc(); print("WORDLE KIT: could not run -", type(e).__name__, e); return False
    for tag, good, note in results:
        if not good: print(f"FAIL {tag}   {note}")
    print(f"wordle: {sum(g for _, g, _ in results)}/{len(results)} pass"); return all(g for _, g, _ in results)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--impl", required=True); ap.add_argument("--seed", type=int, default=int(os.environ.get("KIT_SEED") or 1)); ap.add_argument("--episodes", type=int, default=6)
    a = ap.parse_args(); sys.exit(0 if main(a.impl, a.seed, a.episodes) else 1)
