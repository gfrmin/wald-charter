"""
surface_check.py - tests the SURFACE page (SURFACE.md), not any implementation.
Part 1  a reference checker: pack text -> World spec (INTERFACE.md), or Refused(name). Parses with `ast`; never executes a pack.
Part 2  the corpus: every pack under packs/ok must elaborate and give the frozen answer; every pack under
        packs/poison must be refused by the name on its first line (`# expect: NAME`).
Part 3  round trip: random Worlds printed as packs must elaborate back to the same World (the grammar can say every World).
Run:  python3 laws/surface_check.py        (exit code 0 = the surface page passes)
"""
import ast, itertools, json, os, random, sys
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_check as S

class Refused(Exception):
    def __init__(self, name, msg=""): super().__init__(f"{name}: {msg}"); self.name = name
TAGS = {"data", "elicited", "fitted"}
DECLS = ("world", "clock", "space", "param", "prior", "utility", "price", "act")
ONCE_ONLY = ("world", "clock", "space", "prior", "utility", "price")

class Checker:
    def __init__(self, text, hosts=None, data_dir="."):
        self.hosts, self.data_dir = hosts or {}, data_dir
        self.params, self.read, self.seen, self.census = {}, set(), {}, {t: 0 for t in TAGS}
        self.acts, self.kernel_src = {}, {}
        try: tree = ast.parse(text)
        except SyntaxError as e: raise Refused("SYNTAX", str(e))
        for st in tree.body:
            if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) and isinstance(st.value.func, ast.Name) and st.value.func.id in DECLS):
                raise Refused("NOT_A_DECLARATION", f"line {st.lineno}: a pack is a list of declarations and nothing else")
            name = st.value.func.id
            if name in ONCE_ONLY and name in self.seen: raise Refused("DUPLICATE", name)
            self.seen[name] = True
            getattr(self, "d_" + name)(st.value)
    # ---- argument plumbing
    def args(self, call, pos, kw, required=()):
        if len(call.args) > len(pos) or any(isinstance(a, ast.Starred) for a in call.args): raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: arguments")
        out = dict(zip(pos, call.args))
        for k in call.keywords:
            if k.arg is None or k.arg not in kw or k.arg in out: raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: keyword {k.arg}")
            out[k.arg] = k.value
        for r in required:
            if r not in out: raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: missing {r}")
        return out
    def plain(self, n):
        "a literal with no numeral in it: strings, booleans, and lists, tuples and dicts of them"
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (str, bool)): return n.value
            if isinstance(n.value, (int, float)): raise Refused("UNHOUSED_NUMERAL", f"line {n.lineno}: {n.value!r} is not inside a table")
        if isinstance(n, ast.List): return [self.plain(e) for e in n.elts]
        if isinstance(n, ast.Tuple): return tuple(self.plain(e) for e in n.elts)
        raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: not a literal")
    def num(self, n, tag):
        "a table cell: integers, a/b, unary minus, parameters, and + - * / among them. Exact, or refused."
        if isinstance(n, ast.Constant):
            if isinstance(n.value, bool): raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: a boolean is not a number")
            if isinstance(n.value, float): raise Refused("FLOAT", f"line {n.lineno}: {n.value!r} is not exact; write a ratio of integers")
            if isinstance(n.value, int):
                if tag: self.census[tag] += 1
                return F(n.value)
        if isinstance(n, ast.Name):
            if n.id not in self.params: raise Refused("UNKNOWN_NAME", f"line {n.lineno}: {n.id}")
            self.read.add(n.id); return self.params[n.id]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub): return -self.num(n.operand, tag)
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = self.num(n.left, tag), self.num(n.right, None if isinstance(n.op, ast.Div) and isinstance(n.right, ast.Constant) else tag)
            if isinstance(n.op, ast.Div):
                if b == 0: raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: division by zero")
                return a / b
            return a + b if isinstance(n.op, ast.Add) else a - b if isinstance(n.op, ast.Sub) else a * b
        raise Refused("NOT_A_DECLARATION", f"line {getattr(n, 'lineno', '?')}: not a number a table can hold")
    def tag(self, a, call):
        if "source" not in a: raise Refused("TABLE_SOURCE", f"line {call.lineno}: every table names its source")
        t = self.plain(a["source"])
        if t not in TAGS: raise Refused("TABLE_SOURCE", f"line {call.lineno}: {t!r}")
        return t
    def key(self, n):
        k = self.plain(n)
        if not isinstance(k, (str, tuple)): raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: a key is a name or a tuple of names")
        return k
    def table(self, n, tag, depth):
        "nested dict literal, `depth` levels of keys above the numbers"
        if depth == 0: return self.num(n, tag)
        if not isinstance(n, ast.Dict) or any(k is None for k in n.keys): raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: a table is a dict literal")
        out = {}
        for k, v in zip(n.keys, n.values):
            kk = self.key(k)
            if kk in out: raise Refused("DUPLICATE", f"line {k.lineno}: key {kk!r}")
            out[kk] = self.table(v, tag, depth - 1)
        return out
    # ---- the space
    def states(self): return [c[0] if len(c) == 1 else c for c in itertools.product(*self.space.values())]
    def comp(self, state, c):
        if c not in self.space: raise Refused("UNKNOWN_NAME", f"component {c!r}")
        return state if len(self.space) == 1 else state[list(self.space).index(c)]
    def over(self, n, tag, depth):
        "a table over states: a dict keyed by state, or by(component, {value: ...})"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "by":
            a = self.args(n, ("component", "rows"), (), ("component", "rows")); c = self.plain(a["component"]); rows = self.table(a["rows"], tag, depth)
            try: return {s: rows[self.comp(s, c)] for s in self.states()}
            except KeyError as e: raise Refused("TABLE_SHAPE", f"line {n.lineno}: no row for {e}")
        return self.table(n, tag, depth)
    # ---- declarations
    def d_world(self, call):
        a = self.args(call, ("name",), ("closed", "bottom"), ("name",)); self.name = self.plain(a["name"])
        self.closed = self.plain(a["closed"]) if "closed" in a else False
        self.bottom = self.key(a["bottom"]) if "bottom" in a else None
    def d_clock(self, call):
        a = self.args(call, (), ("horizon", "depth", "source"), ("horizon", "depth")); t = self.tag(a, call)
        self.N, self.d = self.num(a["horizon"], t), self.num(a["depth"], t)
        if self.N.denominator != 1 or self.d.denominator != 1: raise Refused("DEPTH", "horizon and depth are whole numbers")
        self.clock_src = t
    def d_space(self, call):
        if call.args or not call.keywords: raise Refused("NOT_A_DECLARATION", "space(component=[values], ...)")
        self.space = {}
        for k in call.keywords:
            vals = self.plain(k.value)
            if k.arg is None or not isinstance(vals, list) or not vals or not all(isinstance(v, str) for v in vals) or len(set(vals)) != len(vals):
                raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: a component is a list of distinct names")
            self.space[k.arg] = vals
    def d_param(self, call):
        a = self.args(call, ("name", "value"), ("source",), ("name", "value")); nm = self.plain(a["name"]); t = self.tag(a, call)
        if nm in self.params or nm in DECLS: raise Refused("DUPLICATE", nm)
        self.params[nm] = self.num(a["value"], t)
    def d_prior(self, call):
        a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call); self.prior_src = t
        self.prior = self.over(a["table"], t, 1)
    def d_utility(self, call):
        a = self.args(call, ("terminal",), ("ending", "source"), ("terminal",)); t = self.tag(a, call); self.util_src = t
        if not isinstance(a["terminal"], ast.Dict): raise Refused("NOT_A_DECLARATION", "utility({act: table over states}, ...)")
        self.T = {self.key(k): self.over(v, t, 1) for k, v in zip(a["terminal"].keys, a["terminal"].values)}
        self.ending = {}
        if "ending" in a:
            if not isinstance(a["ending"], ast.Dict): raise Refused("NOT_A_DECLARATION", "ending={act: {outcome: table over states}}")
            for k, v in zip(a["ending"].keys, a["ending"].values):
                if not isinstance(v, ast.Dict): raise Refused("NOT_A_DECLARATION", "ending={act: {outcome: table over states}}")
                self.ending[self.key(k)] = {self.key(o): self.over(u, t, 1) for o, u in zip(v.keys, v.values)}
    def d_price(self, call):
        a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call); self.price_src = t; self.prices = self.table(a["table"], t, 1)
    def d_act(self, call):
        a = self.args(call, ("name",), ("kernel", "once", "reads"), ("name", "kernel", "once")); nm = self.plain(a["name"])
        if nm in self.acts: raise Refused("DUPLICATE", nm)
        once = self.plain(a["once"])
        if not isinstance(once, bool): raise Refused("NOT_A_DECLARATION", "once=True or once=False (fresh)")
        tags = set(); K = self.kernel(a["kernel"], tags)
        if len(tags) > 1: raise Refused("TABLE_SOURCE", f"act {nm!r}: the tables of one kernel share one source, found {sorted(tags)}")
        self.kernel_src[nm] = tags.pop() if tags else "data"
        self.acts[nm] = {"K": K, "once": once, "reads": self.plain(a["reads"]) if "reads" in a else None}
    # ---- S4: kernels are built only from these
    def kernel(self, n, tags):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)): raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: a kernel is table, by, point, host, data, mixture, product or compose")
        f = n.func.id
        if f in ("table", "by"):
            if f == "table": a = self.args(n, ("rows",), ("source",), ("rows",)); t = self.tag(a, n); tags.add(t); return self.table(a["rows"], t, 2)
            a = self.args(n, ("component", "rows"), ("source",), ("component", "rows")); t = self.tag(a, n); tags.add(t)
            c, rows = self.plain(a["component"]), self.table(a["rows"], t, 2)
            try: return {s: dict(rows[self.comp(s, c)]) for s in self.states()}
            except KeyError as e: raise Refused("TABLE_SHAPE", f"line {n.lineno}: no row for {e}")
        if f == "point":
            a = self.args(n, ("component",), (), ("component",)); c = self.plain(a["component"]); return {s: {self.comp(s, c): F(1)} for s in self.states()}
        if f == "host":
            a = self.args(n, ("name",), (), ("name",)); h = self.plain(a["name"])
            if h not in self.hosts: raise Refused("UNKNOWN_HOST", h)
            return {s: {self.hosts[h](s): F(1)} for s in self.states()}
        if f == "data":
            a = self.args(n, ("file",), ("source",), ("file",)); t = self.tag(a, n)
            if t == "elicited": raise Refused("TABLE_SOURCE", "an elicited number is written in the pack, where the owner can see it")
            tags.add(t); rows = json.load(open(os.path.join(self.data_dir, self.plain(a["file"]))))
            K = {(tuple(s) if isinstance(s, list) else s): {o: F(q) for o, q in row.items()} for s, row in rows}
            self.census[t] += sum(len(r) for r in K.values()); return K
        if f == "mixture":
            a = self.args(n, ("parts",), ("source",), ("parts",)); t = self.tag(a, n); tags.add(t)
            if not isinstance(a["parts"], ast.List): raise Refused("NOT_A_DECLARATION", "mixture([(weight, kernel), ...], source=...)")
            parts = []
            for e in a["parts"].elts:
                if not (isinstance(e, ast.Tuple) and len(e.elts) == 2): raise Refused("NOT_A_DECLARATION", "mixture([(weight, kernel), ...])")
                parts.append((self.num(e.elts[0], t), self.kernel(e.elts[1], tags)))
            if sum(w for w, _ in parts) != 1 or any(w < 0 for w, _ in parts): raise Refused("KERNEL_ROW", "mixture weights are non-negative and sum to 1")
            out = {s: {} for s in self.states()}
            for w, K in parts:
                for s in out:
                    for o, q in K.get(s, {}).items(): out[s][o] = out[s].get(o, F(0)) + w * q
            return out
        if f == "product":
            a = self.args(n, ("left", "right"), (), ("left", "right")); A, B = self.kernel(a["left"], tags), self.kernel(a["right"], tags)
            return {s: {(o1, o2): p * q for o1, p in A.get(s, {}).items() for o2, q in B.get(s, {}).items()} for s in self.states()}
        if f == "compose":
            a = self.args(n, ("first", "then"), ("source",), ("first", "then")); t = self.tag(a, n); tags.add(t)
            A, G = self.kernel(a["first"], tags), self.table(a["then"], t, 2); out = {}
            for s, row in A.items():
                out[s] = {}
                for o, p in row.items():
                    if o not in G: raise Refused("TABLE_SHAPE", f"compose: no row for outcome {o!r}")
                    if sum(G[o].values()) != 1: raise Refused("KERNEL_ROW", f"compose: row {o!r}")
                    for o2, q in G[o].items(): out[s][o2] = out[s].get(o2, F(0)) + p * q
            return out
        raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: {f} is not a kernel")
    # ---- the World spec of INTERFACE.md
    def spec(self):
        for need in ONCE_ONLY:
            if need not in self.seen: raise Refused("MISSING", need)
        unread = sorted(set(self.params) - self.read)
        if unread: raise Refused("UNREAD_PARAMETER", ", ".join(unread))
        O = {}
        for nm, a in self.acts.items():
            if nm not in self.prices: raise Refused("TABLE_SHAPE", f"no price for {nm!r}")
            O[nm] = {"K": a["K"], "price": self.prices[nm], "once": a["once"], "ends": self.ending.get(nm, {})}
        extra = (set(self.prices) - set(O)) | (set(self.ending) - set(O))
        if extra: raise Refused("TABLE_SHAPE", f"a price or an ending for no act: {sorted(extra)}")
        s = {"prior": self.prior, "T": self.T, "O": O, "N": int(self.N), "d": int(self.d),
             "table_sources": {"prior": self.prior_src, "utility": self.util_src, "price": self.price_src, "horizon": self.clock_src, "depth": self.clock_src, "kernels": dict(self.kernel_src)},
             "sources": {nm: a["reads"] for nm, a in self.acts.items() if a["reads"] is not None}, "components": list(self.space)}
        if self.closed: s["closed"] = True
        if self.bottom is not None: s["bottom"] = self.bottom
        validate(s, set(self.states())); return s

def validate(s, omega):
    "the World-level refusals of INTERFACE.md, by name"
    if not s["T"]: raise Refused("EMPTY_T")
    if set(s["prior"]) != omega: raise Refused("TABLE_SHAPE", "the prior is not total over the space")
    if any(p <= 0 for p in s["prior"].values()) or sum(s["prior"].values()) != 1: raise Refused("PRIOR")
    for t, u in s["T"].items():
        if set(u) != omega: raise Refused("TABLE_SHAPE", f"utility of {t!r}")
    for k, a in s["O"].items():
        if set(a["K"]) != omega: raise Refused("TABLE_SHAPE", f"kernel of {k!r}")
        if any(sum(r.values()) != 1 or any(q < 0 for q in r.values()) for r in a["K"].values()): raise Refused("KERNEL_ROW", k)
        if a["price"] < 0: raise Refused("PRICE", k)
        outs = {o for r in a["K"].values() for o in r}
        for o, u in a["ends"].items():
            if o not in outs or set(u) != omega: raise Refused("TABLE_SHAPE", f"ending {o!r} of {k!r}")
    if not (1 <= s["d"] <= s["N"]): raise Refused("DEPTH")
    if not s.get("closed"):
        b = s.get("bottom")
        if b not in omega or any(r.get(o, 0) <= 0 for a in s["O"].values() for r in [a["K"][b]] for o in {o for rr in a["K"].values() for o in rr}): raise Refused("ZERO_EVIDENCE")
    seen = {}
    for k, srcs in s["sources"].items():
        for src in srcs:
            if src in s["components"]: continue
            if src in seen or not s["O"][k]["once"]: raise Refused("SHARED_SOURCE", src)
            seen[src] = k

def check(text, hosts=None, data_dir="."): return Checker(text, hosts, data_dir).spec()
def census(text, hosts=None, data_dir="."): c = Checker(text, hosts, data_dir); c.spec(); return c.census

# ---------------------------------------------------------------- Part 3 helper: print a World as a pack
def q(x): return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"
def to_pack(w, N, d):
    st = lambda s: repr(s); tbl = lambda m: "{" + ", ".join(f"{st(k)}: {q(v)}" for k, v in m.items()) + "}"
    L = ['world("w", closed=True)', f'clock(horizon={N}, depth={d}, source="elicited")', f'space(s={list(w["prior"])!r})', f'prior({tbl(w["prior"])}, source="data")']
    ends = {k: a["ends"] for k, a in w["O"].items() if a["ends"]}
    e = ", ending={" + ", ".join(f"{k!r}: {{" + ", ".join(f"{o!r}: {tbl(u)}" for o, u in es.items()) + "}" for k, es in ends.items()) + "}" if ends else ""
    L.append("utility({" + ", ".join(f"{t!r}: {tbl(u)}" for t, u in w["T"].items()) + "}" + e + ', source="elicited")')
    L.append("price({" + ", ".join(f"{k!r}: {q(a['price'])}" for k, a in w["O"].items()) + '}, source="elicited")')
    for k, a in w["O"].items():
        rows = "{" + ", ".join(f"{st(s)}: {tbl(r)}" for s, r in a["K"].items()) + "}"
        L.append(f'act({k!r}, once={a["once"]}, kernel=table({rows}, source="data"))')
    return "\n".join(L) + "\n"

def wordle_feedback(guess):
    def f(answer): return "".join("g" if a == b else ("y" if b in answer else "-") for a, b in zip(answer, guess))
    return f
HOSTS = {"fb_" + g: wordle_feedback(g) for g in ("cat", "cot", "dog")}

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__)); ok = True
    frozen = {"appendix.py": (F(-51, 50), "test"), "shared_draw.py": (F(0), "hold"), "wordle_mini.py": None, "noisy_test.py": None}
    print("lawful packs:")
    for fn in sorted(os.listdir(os.path.join(here, "packs/ok"))):
        if not fn.endswith(".py"): continue
        try:
            w = check(open(os.path.join(here, "packs/ok", fn)).read(), HOSTS, os.path.join(here, "packs/ok")); got = S.REF.solve(w["prior"], w, w["N"])
            c = census(open(os.path.join(here, "packs/ok", fn)).read(), HOSTS, os.path.join(here, "packs/ok"))
            good = frozen.get(fn) in (None, got); ok &= good
            print(f"  {'ok ' if good else 'BAD'} {fn:22s} V_N, act = {got[0]}, {got[1]}   numerals by source: {c}")
        except Refused as e: ok = False; print(f"  BAD {fn}: refused {e}")
    print("poison packs:")
    for fn in sorted(os.listdir(os.path.join(here, "packs/poison"))):
        text = open(os.path.join(here, "packs/poison", fn)).read(); want = text.splitlines()[0].replace("# expect:", "").strip()
        try: check(text, HOSTS, os.path.join(here, "packs/ok")); got = "ACCEPTED"
        except Refused as e: got = e.name
        good = got == want; ok &= good
        print(f"  {'ok ' if good else 'BAD'} {fn:28s} {got}" + ("" if good else f"   (wanted {want})"))
    rng = random.Random(2026); bad = 0
    for i in range(200):
        w = S.rand_world(rng); ren = {s: f"e{s[0]}z{s[1]}" for s in w["prior"]}
        w2 = {"prior": {ren[s]: p for s, p in w["prior"].items()}, "T": {t: {ren[s]: x for s, x in u.items()} for t, u in w["T"].items()},
              "O": {k: {"K": {ren[s]: r for s, r in a["K"].items()}, "price": a["price"], "once": a["once"], "ends": {o: {ren[s]: x for s, x in u.items()} for o, u in a["ends"].items()}} for k, a in w["O"].items()}}
        e = check(to_pack(w2, 2, 2))
        if any(e[k] != w2[k] for k in ("prior", "T", "O")) or list(e["T"]) != list(w2["T"]) or list(e["O"]) != list(w2["O"]): bad += 1
    print(f"round trip: {200 - bad}/200 random Worlds survive being printed as a pack and read back"); ok &= bad == 0
    print("\nSURFACE PASSES" if ok else "\nSURFACE FAILS"); sys.exit(0 if ok else 1)
