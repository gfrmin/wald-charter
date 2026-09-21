"""
wordle_meta_oracle.py - the think act (CHARTER v0.1) on the Wordle family of Worlds, in exact integer arithmetic.

Extends laws/wordle_oracle.py: same World (uniform prior over the words, `once` guesses at price 1, all-green ends at 0,
claims -1 right / `loss` wrong, horizon 5), now with d = 1, d+ = 2, a Fraction f, a Cost table ops(s) and a Rate r.

On this family CHARTER v0.1 section 2 reduces to:
    best(w)  = 0 for every w (guessing the answer ends all-green at 0), min price = 1, so cap(C) = max(V_0(C), -1)
    ghat     = cap - V_1(C)                 (0 at n <= 1 or when no guess is left)
    c        = r * ops(|C|)
    Q(theta) = V_1 + f*ghat - c;  bought iff ghat > c and f*ghat > c
With m = |C| and I_k = m*V_k the same in integers: cap_I = max(I_0, -m), ghat_I = cap_I - I_1, and the test is
    ghat_I > m*c   and   f*ghat_I > m*c.

The E3 curves: policy value under the declared model (uniform over answers, exact) for fixed d = 1, fixed d = 2 paying c at
every step with n > 1 and a guess left, adaptive (this page), and the omniscient meta-policy (buys theta exactly where it
raises the value of its own continuation net of c; a DP over (C, n)).  The best fixed depth in hindsight is max of the two.

kit use: prove agreement with spec_check.Ref + meta_check.DecidePlus on the 40 words first (--prove), then trust it at 200.
"""
from fractions import Fraction as F
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wordle_oracle import Oracle, feedback

class MetaOracle(Oracle):
    def __init__(self, words, loss, f, ops, r, N=5):
        super().__init__(words, loss)
        self.f, self.ops, self.r, self.N = F(f), {int(k): F(v) for k, v in ops.items()}, F(r), N
        self.vmemo = {}
    # ---- decide+ at a node (C, n)
    def step(self, C, n):
        "(act, how, paid) with act ('claim', i) or ('guess', i); how in S7's buckets"
        m = len(C)
        I1, a1 = self.solve(C, min(1, n))
        if n <= 1:                                  # a guess is always left (once acts, N = 5 < |words|): struck_n is n <= d only
            return a1, "struck_n", F(0)
        cap_I = max(-1 + self.loss * (m - 1), -m)
        ghat_I = cap_I - I1                        # = m * ghat
        c = self.r * self.ops[m]
        if ghat_I <= m * c: return a1, "struck_cap", F(0)
        if self.f * ghat_I > m * c: return self.solve(C, min(2, n))[1], "think", c
        return a1, "refused", F(0)
    # ---- policy value under the model, exact: mean over answers in C of what the policy earns from (C, n)
    def value(self, policy, C=None, n=None):
        "policy(C, n) -> (act, paid).  Returns m * expected utility from this node (integer-scaled like I)."
        C = frozenset(range(self.n)) if C is None else C; n = self.N if n is None else n
        key = (policy.__name__, C, n)
        if key in self.vmemo: return self.vmemo[key]
        m = len(C); (kind, i), paid = policy(C, n)
        if kind == "claim":
            v = -1 * (1 if i in C else 0) + self.loss * (m - (1 if i in C else 0)) - paid * m
        else:
            row = self.fb[i]; classes = {}
            for a in C: classes.setdefault(row[a], []).append(a)
            v = -m - paid * m
            for o, c in classes.items():
                if o != self.green: v += self.value(policy, frozenset(c), n - 1)
        self.vmemo[key] = v; return v
    def fixed(self, d):
        def pol(C, n): return self.solve(C, min(d, n))[1], F(0)
        pol.__name__ = f"fixed{d}"; return pol
    def always_deep(self):
        def pol(C, n):
            if n <= 1: return self.solve(C, min(1, n))[1], F(0)
            return self.solve(C, min(2, n))[1], self.r * self.ops[len(C)]      # E3: pays at every step with n > d and a guess left
        pol.__name__ = "always2"; return pol
    def adaptive(self):
        def pol(C, n): a, how, paid = self.step(C, n); return a, paid
        pol.__name__ = f"adaptive_f{self.f}_r{self.r}"; return pol
    def omniscient(self, C=None, n=None):
        "m * value of the meta-policy that buys theta exactly where it raises its own continuation net of c"
        C = frozenset(range(self.n)) if C is None else C; n = self.N if n is None else n
        key = ("omni", C, n)
        if key in self.vmemo: return self.vmemo[key]
        m = len(C)
        def cont(act, paid):
            kind, i = act
            if kind == "claim": return -1 * (1 if i in C else 0) + self.loss * (m - (1 if i in C else 0)) - paid * m
            row = self.fb[i]; classes = {}
            for a in C: classes.setdefault(row[a], []).append(a)
            v = -m - paid * m
            for o, c in classes.items():
                if o != self.green: v += self.omniscient(frozenset(c), n - 1)
            return v
        shallow = cont(self.solve(C, min(1, n))[1], F(0))
        if n <= 1 or m == 1: best = shallow
        else: best = max(shallow, cont(self.solve(C, min(2, n))[1], self.r * self.ops[m]))
        self.vmemo[key] = best; return best
    def curves(self):
        "the five E3 numbers at this (f, r), as expected utility per episode (exact rationals)"
        m = self.n
        v1 = F(self.value(self.fixed(1)), m); v2 = F(self.value(self.always_deep()), m)
        va = F(self.value(self.adaptive()), m); vo = F(self.omniscient(), m)
        return {"fixed d=1": v1, "always d=2": v2, "best fixed": max(v1, v2), "adaptive": va, "omniscient": vo}
    def episode(self, answer):
        "acts, buckets, thought cost, attempts for one answer under the adaptive policy"
        ai = self.words.index(answer); C, n, acts, hows, paid = frozenset(range(self.n)), self.N, [], [], F(0)
        while True:
            (kind, i), how, c = self.step(C, n); hows.append(how); paid += c
            if kind == "claim": acts.append("claim " + self.words[i]); return acts, hows, paid, len(acts), i == ai
            acts.append(self.words[i]); o = self.fb[i][ai]
            if o == self.green: return acts, hows, paid, len(acts), True
            C = frozenset(a for a in C if self.fb[i][a] == o); n -= 1

if __name__ == "__main__":
    import argparse, random
    ap = argparse.ArgumentParser(); ap.add_argument("--words", default="wordle/words.txt"); ap.add_argument("--loss", type=int, default=-7)
    ap.add_argument("--f", default="1/2"); ap.add_argument("--r", default="0"); ap.add_argument("--ops", default="quad:1:0", help="quad:a:b means ops(s)=a*s*s+b*s")
    ap.add_argument("--prove", type=int, default=0, help="agree with spec_check.Ref + meta_check.DecidePlus on this many answers (slow)")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__)); words = open(os.path.join(here, a.words)).read().split()
    _, qa, qb = a.ops.split(":"); ops = {s: F(qa) * s * s + F(qb) * s for s in range(1, len(words) + 1)}
    O = MetaOracle(words, a.loss, F(a.f), ops, F(a.r))
    if a.prove:
        import spec_check as S, meta_check as M
        ends = {"ggggg": {w: F(0) for w in words}}
        w = {"prior": {x: F(1, len(words)) for x in words}, "T": {"claim " + x: {y: F(-1 if x == y else a.loss) for y in words} for x in words},
             "O": {g: {"K": {x: {feedback(g, x): F(1)} for x in words}, "price": F(1), "once": True, "ends": ends} for g in words},
             "N": 5, "d": 1, "dplus": 2, "fraction": F(a.f), "rate": F(a.r), "ops": ops}
        mism = 0; nodes = 0
        for ans in words[:a.prove]:
            C, n, used, b = frozenset(range(len(words))), 5, frozenset(), w["prior"]
            while True:
                (kind, i), how, paid = O.step(C, n); ra, rhow, rpaid = M.DPLUS.step(b, w, n, used); nodes += 1
                mine = ("claim " + words[i]) if kind == "claim" else words[i]
                if (mine, how, paid) != (ra, rhow, rpaid): mism += 1; print("MISMATCH", ans, n, (mine, how, paid), (ra, rhow, rpaid)); break
                if kind == "claim": break
                o = O.fb[i][words.index(ans)]
                if o == O.green: break
                C = frozenset(x for x in C if O.fb[i][x] == o); b = S.REF.condition(b, w["O"][words[i]]["K"], feedback(words[i], ans)); used = used | {words[i]}; n -= 1
        print(f"prove: {nodes} nodes on {a.prove} answers, {mism} mismatches with meta_check.DecidePlus")
    cv = O.curves()
    print(f"{len(words)} words, loss {a.loss}, f = {a.f}, r = {a.r}, ops = {a.ops}")
    for k, v in cv.items(): print(f"  {k:12s} {v!s:>14s}  = {float(v):.4f}")
    hows = {}; thought = F(0); attempts = 0; wrong = 0
    for wd in words:
        acts, hs, paid, att, right = O.episode(wd); thought += paid; attempts += att; wrong += not right
        for h in hs: hows[h] = hows.get(h, 0) + 1
    print(f"  adaptive episodes: mean attempts {attempts / len(words):.3f}, wrong claims {wrong}, mean thought paid {float(thought / len(words)):.4f}, steps {hows}")
