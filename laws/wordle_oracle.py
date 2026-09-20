"""
wordle_oracle.py - a second, specialised oracle for ONE family of Worlds: Wordle with a uniform prior over the words, every word a
`once` guess at price 1 with the game's deterministic feedback, all-green ending at 0, and claims worth -1 if right and `loss` if wrong.
On that family a belief is uniform over a candidate set, so CHARTER section 2 reduces to arithmetic on sets. This file IS that reduction,
with J3's tie rule (terminal acts first, then guesses in declared order, a later entry only by strictly beating the incumbent).
It exists because the general oracle (spec_check.Ref) is too slow beyond ~40 words. kit_wordle_big.py first proves the two agree on the
40-word World, move by move, and only then trusts this one at 200 words and depth 2.
"""
from fractions import Fraction as F

def feedback(guess, answer):
    out = ["-"] * 5; left = {}
    for g, a in zip(guess, answer):
        if g != a: left[a] = left.get(a, 0) + 1
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a: out[i] = "g"
        elif left.get(g, 0) > 0: out[i] = "y"; left[g] -= 1
    return "".join(out)

class Oracle:
    """Exact integer arithmetic. With m = |C| write I_k(C) = m * V_k(C). Then
         I_0(C) = -1 + loss*(m-1)                                  (claim the first candidate in declared order)
         I_k(C) = max( I_0(C), max_g [ -m + sum over g's feedback classes c of C, all-green excepted, of I_{k-1}(c) ] )
       which is CHARTER section 2 multiplied through by m. A spent guess can never attain the max (it splits nothing and costs 1),
       so skipping spent guesses changes no value and no act, and the memo needs only (C, k)."""
    def __init__(self, words, loss):
        assert loss == int(loss)
        self.words, self.loss, self.n = list(words), int(loss), len(words)
        codes = {}; self.fb = [[codes.setdefault(feedback(g, a), len(codes)) for a in words] for g in words]
        self.green = codes.get("ggggg"); self.memo = {}
    def solve(self, C, k):
        "(I_k(C), act) with C a frozenset of word indices; act is ('claim', i) or ('guess', i)"
        key = (C, k)
        if key in self.memo: return self.memo[key]
        m = len(C); best, arg = -1 + self.loss * (m - 1), ("claim", min(C))
        if k > 0 and m > 1:
            for g in range(self.n):
                row = self.fb[g]; classes = {}
                for a in C: classes.setdefault(row[a], []).append(a)
                if len(classes) == 1 and self.green not in classes: continue          # splits nothing: strictly worse than stopping
                q = -m
                for o, c in classes.items():
                    if o != self.green: q += self.solve(frozenset(c), k - 1)[0]
                if q > best: best, arg = q, ("guess", g)
        elif k > 0 and m == 1:
            pass                                                                       # guessing the one candidate ties the claim; J3 keeps the claim
        self.memo[key] = (best, arg); return best, arg
    def play(self, answer, N, d):
        "the acts of one episode, as CHARTER section 2's loop plays it, in the pack's names"
        ai = self.words.index(answer); C, n, acts = frozenset(range(self.n)), N, []
        while True:
            kind, i = self.solve(C, min(d, n))[1]
            if kind == "claim": acts.append("claim " + self.words[i]); return acts
            acts.append(self.words[i]); o = self.fb[i][ai]
            if o == self.green: return acts
            C = frozenset(a for a in C if self.fb[i][a] == o); n -= 1
