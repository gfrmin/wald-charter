"""
surface_check.py - tests the SURFACE pages (SURFACE.md and SURFACE-v0.1.md), not any implementation.
Part 1  a reference checker: pack text -> World spec (INTERFACE.md), or Refused(name). Parses with `ast`; never executes a pack.
Part 2  the corpus: every pack under packs/ok must elaborate and give the frozen answer; every pack under
        packs/poison must be refused by the name on its first line (`# expect: NAME`).
Part 3  round trip: random Worlds printed as packs must elaborate back to the same World (the grammar can say every World).
Run:  python3 laws/surface_check.py        (exit code 0 = the surface page passes)
"""
import ast, hashlib, inspect, itertools, json, keyword, os, random, sys, textwrap
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_check as S

class Refused(Exception):
    def __init__(self, name, msg=""): super().__init__(f"{name}: {msg}"); self.name = name
TAGS = {"data", "elicited", "fitted"}
DECLS = ("world", "horizon", "depth", "space", "param", "prior", "utility", "price", "act", "think", "cost", "rate", "score")
ONCE_ONLY = ("world", "horizon", "depth", "space", "prior", "utility", "price")
META_ONCE = ("think", "cost", "rate", "score")          # SURFACE v0.1: optional, each at most once

class Checker:
    def __init__(self, text, hosts=None, data_dir="."):
        self.hosts, self.data_dir = hosts or {}, data_dir
        self.params, self.param_src, self.read, self.seen, self.census = {}, {}, set(), {}, {t: 0 for t in TAGS}
        self.host_prints = {}
        self.acts, self.kernel_src = {}, {}
        try: tree = ast.parse(text)
        except SyntaxError as e: raise Refused("SYNTAX", str(e))
        for st in tree.body:
            if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) and isinstance(st.value.func, ast.Name) and st.value.func.id in DECLS):
                raise Refused("NOT_A_DECLARATION", f"line {st.lineno}: a pack is a list of declarations and nothing else")
            name = st.value.func.id
            if (name in ONCE_ONLY or name in META_ONCE) and name in self.seen: raise Refused("DUPLICATE", name)
            self.seen[name] = True
            getattr(self, "d_" + name)(st.value)
    # ---- argument plumbing
    def args(self, call, pos, kw, required=()):
        if len(call.args) > len(pos) or any(isinstance(a, ast.Starred) for a in call.args): raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: arguments")
        out = dict(zip(pos, call.args))
        for k in call.keywords:
            if k.arg in out: raise Refused("DUPLICATE", f"line {call.lineno}: {k.arg} given twice")
            if k.arg is None or k.arg not in kw: raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: keyword {k.arg}")
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
                return F(n.value)
        if isinstance(n, ast.Name):
            if n.id not in self.params: raise Refused("UNKNOWN_NAME", f"line {n.lineno}: {n.id}")
            if tag and tag != "fitted" and self.param_src[n.id] == "fitted": raise Refused("TABLE_SOURCE", f"line {n.lineno}: a {tag!r} table reads the {self.param_src[n.id]!r} parameter {n.id!r}")
            self.read.add(n.id); return self.params[n.id]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub): return -self.num(n.operand, tag)
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a = self.num(n.left, tag); self._quiet = isinstance(n.op, ast.Div) and isinstance(n.right, ast.Constant)
            b = self.num(n.right, tag)
            if isinstance(n.op, ast.Div):
                if b == 0: raise Refused("DIVISION_BY_ZERO", f"line {n.lineno}")
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
        if depth == 0:
            if tag: self.census[tag] += 1
            return self.num(n, tag)
        if not isinstance(n, ast.Dict) or any(k is None for k in n.keys): raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: a table is a dict literal")
        out = {}
        for k, v in zip(n.keys, n.values):
            kk = self.key(k)
            if kk in out: raise Refused("DUPLICATE", f"line {k.lineno}: key {kk!r}")
            out[kk] = self.table(v, tag, depth - 1)
        return out
    # ---- the space
    def product(self):
        if "space" not in self.seen: raise Refused("MISSING", "space")
        return [c[0] if len(c) == 1 else c for c in itertools.product(*self.space.values())]
    def states(self):
        if "prior" not in self.seen: raise Refused("MISSING", "prior: tables over states come after the prior, which says what the states are")
        return list(self.prior)
    def comp(self, state, c):
        if "space" not in self.seen: raise Refused("MISSING", "space")
        if c not in self.space: raise Refused("UNKNOWN_NAME", f"component {c!r}")
        return state if len(self.space) == 1 else state[list(self.space).index(c)]
    def by_rows(self, c, rows, n):
        need = {self.comp(st, c) for st in self.states()}
        if set(rows) != need: raise Refused("TABLE_SHAPE", f"line {n.lineno}: by({c!r}) needs a row for exactly {sorted(need)}")
    def over(self, n, tag, depth):
        "a table over states: a dict keyed by state, or by(component, {value: ...})"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "by":
            a = self.args(n, ("component", "rows"), (), ("component", "rows")); c = self.plain(a["component"]); rows = self.table(a["rows"], tag, depth); self.by_rows(c, rows, n)
            try: return {s: rows[self.comp(s, c)] for s in self.states()}
            except KeyError as e: raise Refused("TABLE_SHAPE", f"line {n.lineno}: no row for {e}")
        return self.table(n, tag, depth)
    # ---- declarations
    def d_world(self, call):
        a = self.args(call, ("name",), ("closed", "bottom"), ("name",)); self.name = self.plain(a["name"])
        self.closed = self.plain(a["closed"]) if "closed" in a else False
        self.bottom = self.key(a["bottom"]) if "bottom" in a else None
    def d_horizon(self, call):
        a = self.args(call, ("n",), ("source",), ("n",)); self.N_src = self.tag(a, call); self.N = self.num(a["n"], self.N_src); self.census[self.N_src] += 1
    def d_depth(self, call):
        a = self.args(call, ("d",), ("source",), ("d",)); self.d_src = self.tag(a, call); self.d = self.num(a["d"], self.d_src); self.census[self.d_src] += 1
    def d_space(self, call):
        a = self.args(call, ("components",), (), ("components",)); n = a["components"]
        if not isinstance(n, ast.Dict) or not n.keys or any(k is None for k in n.keys): raise Refused("NOT_A_DECLARATION", 'space({"component": [names], ...})')
        self.space = {}
        for k, v in zip(n.keys, n.values):
            c, vals = self.plain(k), self.plain(v)
            if c in self.space: raise Refused("DUPLICATE", f"component {c!r}")
            if not isinstance(c, str) or not isinstance(vals, list) or not vals or not all(isinstance(x, str) for x in vals): raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: a component is a name and a list of names")
            if len(set(vals)) != len(vals): raise Refused("DUPLICATE", f"a value of {c!r}")
            self.space[c] = vals
    def d_param(self, call):
        a = self.args(call, ("name", "value"), ("source",), ("name", "value")); nm = self.plain(a["name"]); t = self.tag(a, call)
        if nm in self.params: raise Refused("DUPLICATE", nm)
        if not isinstance(nm, str) or not nm.isidentifier() or keyword.iskeyword(nm): raise Refused("BAD_NAME", f"{nm!r} cannot be read from a cell")
        self.params[nm] = self.num(a["value"], t); self.param_src[nm] = t; self.census[t] += 1
    def d_prior(self, call):
        if "space" not in self.seen: raise Refused("MISSING", "space: the prior comes after the space")
        a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call); self.prior_src = t
        if not isinstance(a["table"], ast.Dict): raise Refused("NOT_A_DECLARATION", "the prior is a dict keyed by state: it is what says which states exist")
        self.prior = self.table(a["table"], t, 1)
    def keys_once(self, node, what):
        ks = [self.key(k) for k in node.keys]
        if any(k is None for k in node.keys): raise Refused("NOT_A_DECLARATION", f"{what}: no ** in a dict")
        if len(set(ks)) != len(ks): raise Refused("DUPLICATE", f"{what}: a key is written twice")
        return ks
    def d_utility(self, call):
        self.states()
        a = self.args(call, ("terminal",), ("ending", "source"), ("terminal",)); t = self.tag(a, call); self.util_src = t
        if not isinstance(a["terminal"], ast.Dict): raise Refused("NOT_A_DECLARATION", "utility({act: table over states}, ...)")
        self.T = {k: self.over(v, t, 1) for k, v in zip(self.keys_once(a["terminal"], "utility"), a["terminal"].values)}
        self.ending = {}
        if "ending" in a:
            if not isinstance(a["ending"], ast.Dict): raise Refused("NOT_A_DECLARATION", "ending={act: {outcome: table over states}}")
            for k, v in zip(self.keys_once(a["ending"], "ending"), a["ending"].values):
                if not isinstance(v, ast.Dict): raise Refused("NOT_A_DECLARATION", "ending={act: {outcome: table over states}}")
                self.ending[k] = {o: self.over(u, t, 1) for o, u in zip(self.keys_once(v, f"ending of {k!r}"), v.values)}
    def d_price(self, call):
        a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call); self.price_src = t; self.prices = self.table(a["table"], t, 1)
    # ---- SURFACE v0.1: the think act
    def d_think(self, call):
        a = self.args(call, (), ("depth", "fraction", "source"), ("depth", "fraction")); t = self.tag(a, call)
        if t not in ("elicited", "fitted"): raise Refused("FRACTION", f"line {call.lineno}: a fraction is elicited or fitted, not {t!r}")
        self.dplus = self.num(a["depth"], t); self.fraction = self.num(a["fraction"], t); self.fraction_src = t; self.census[t] += 2
    def d_cost(self, call):
        if "prior" not in self.seen: raise Refused("MISSING", "prior: the cost table comes after the prior, whose states it counts")
        a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call)
        if t not in ("elicited", "fitted"): raise Refused("COST", f"line {call.lineno}: a cost is elicited or fitted, not {t!r}")
        if not isinstance(a["table"], ast.List): raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: cost is a list, one cell per live-state count, in order")
        cells = [self.num(e, t) for e in a["table"].elts]
        if len(cells) != len(self.prior): raise Refused("COST", f"line {call.lineno}: {len(cells)} cells for {len(self.prior)} states")
        self.ops = {i + 1: c for i, c in enumerate(cells)}; self.cost_src = t; self.census[t] += len(cells)
    def d_rate(self, call):
        a = self.args(call, ("r",), ("source",), ("r",)); t = self.tag(a, call)
        if t != "elicited": raise Refused("RATE", f"line {call.lineno}: the rate is the owner's, source elicited, not {t!r}")
        self.rate = self.num(a["r"], t); self.rate_src = t; self.census[t] += 1
    def d_score(self, call):
        a = self.args(call, ("value",), ("source",), ("value",)); t = self.tag(a, call)
        if t != "data": raise Refused("TABLE_SOURCE", f"line {call.lineno}: a score is measured, source data, not {t!r}")
        self.score = self.num(a["value"], t); self.census[t] += 1
    def d_act(self, call):
        self.states()
        a = self.args(call, ("name",), ("kernel", "once", "reads"), ("name", "kernel", "once", "reads")); nm = self.plain(a["name"])
        if nm in self.acts: raise Refused("DUPLICATE", nm)
        once = self.plain(a["once"])
        if not isinstance(once, bool): raise Refused("NOT_A_DECLARATION", "once=True or once=False (fresh)")
        tags = set(); self.named = set(); K = self.kernel(a["kernel"], tags); reads = self.plain(a["reads"])
        if not isinstance(reads, list) or not reads or not all(isinstance(r, str) for r in reads): raise Refused("NOT_A_DECLARATION", f"act {nm!r}: reads=[sources], at least one (CHARTER S2)")
        if isinstance(reads, list) and not self.named <= set(reads): raise Refused("UNDECLARED_READ", f"act {nm!r} names {sorted(self.named - set(reads))} in its kernel but not in reads")
        comps = list(self.space); idx = [i for i, c in enumerate(comps) if c in reads]; rows = {}
        for st, row in K.items():                      # the kernel may depend on no component the act does not say it reads
            proj = tuple((st if len(comps) == 1 else st[i]) for i in idx)
            if rows.setdefault(proj, row) != row: raise Refused("UNDECLARED_READ", f"act {nm!r} depends on a component missing from reads={reads}")
        self.kernel_src[nm] = sorted(tags); self.acts[nm] = {"K": K, "once": once, "reads": reads}
    def rows_ok(self, rows, where):
        for k, r in rows.items():
            if any(q < 0 for q in r.values()) or sum(r.values()) != 1: raise Refused("KERNEL_ROW", f"{where}: row {k!r} is not a distribution")
        return rows
    # ---- S4: kernels are built only from these
    def kernel(self, n, tags):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)): raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: a kernel is table, by, point, data, mixture, product or compose")
        f = n.func.id
        if f in ("table", "by"):
            if f == "table": a = self.args(n, ("rows",), ("source",), ("rows",)); t = self.tag(a, n); tags.add(t); return self.rows_ok(self.table(a["rows"], t, 2), "table")
            a = self.args(n, ("component", "rows"), ("source",), ("component", "rows")); t = self.tag(a, n); tags.add(t)
            c, rows = self.plain(a["component"]), self.rows_ok(self.table(a["rows"], t, 2), "by"); self.named.add(c); self.by_rows(c, rows, n)
            try: return {s: dict(rows[self.comp(s, c)]) for s in self.states()}
            except KeyError as e: raise Refused("TABLE_SHAPE", f"line {n.lineno}: no row for {e}")
        if f == "point":
            a = self.args(n, ("component",), (), ("component",)); c = self.plain(a["component"]); self.named.add(c); return {s: {self.comp(s, c): F(1)} for s in self.states()}
        if f == "data":
            a = self.args(n, ("file",), ("source", "sha256"), ("file", "sha256")); t = self.tag(a, n)
            if t == "elicited": raise Refused("TABLE_SOURCE", "an elicited number is written in the pack, where the owner can see it")
            tags.add(t); raw = open(os.path.join(self.data_dir, self.plain(a["file"])), "rb").read()
            if hashlib.sha256(raw).hexdigest() != self.plain(a["sha256"]): raise Refused("DATA_HASH", "the file is not the one the pack pinned")
            rows = json.loads(raw)
            keys = [json.dumps(r[0]) for r in rows]
            if len(set(keys)) != len(keys): raise Refused("DUPLICATE", "a state appears twice in the data file")
            K = {(tuple(s) if isinstance(s, list) else s): {o: F(q) for o, q in row.items()} for s, row in rows}
            self.census[t] += sum(len(r) for r in K.values()); return self.rows_ok(K, "data file")
        if f == "mixture":
            a = self.args(n, ("parts",), ("source",), ("parts",)); t = self.tag(a, n); tags.add(t)
            if not isinstance(a["parts"], ast.List): raise Refused("NOT_A_DECLARATION", "mixture([(weight, kernel), ...], source=...)")
            parts = []
            for e in a["parts"].elts:
                if not (isinstance(e, ast.Tuple) and len(e.elts) == 2): raise Refused("NOT_A_DECLARATION", "mixture([(weight, kernel), ...])")
                self.census[t] += 1; parts.append((self.num(e.elts[0], t), self.kernel(e.elts[1], tags)))
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
            A, G = self.kernel(a["first"], tags), self.rows_ok(self.table(a["then"], t, 2), "garbling"); out = {}
            for s, row in A.items():
                out[s] = {}
                for o, p in row.items():
                    if o not in G: raise Refused("TABLE_SHAPE", f"compose: no row for outcome {o!r}")
                    for o2, q in G[o].items(): out[s][o2] = out[s].get(o2, F(0)) + p * q
            return out
        raise Refused("NOT_A_DECLARATION", f"line {n.lineno}: {f} is not a kernel")
    # ---- the World spec of INTERFACE.md
    def spec(self):
        for need in ONCE_ONLY:
            if need not in self.seen: raise Refused("MISSING", need)
        O = {}
        for nm, a in self.acts.items():
            if nm not in self.prices: raise Refused("TABLE_SHAPE", f"no price for {nm!r}")
            O[nm] = {"K": a["K"], "price": self.prices[nm], "once": a["once"], "ends": self.ending.get(nm, {})}
        both = set(self.T) & set(O)
        if both: raise Refused("DUPLICATE", f"{sorted(both)} name both a terminal and an observational act")
        extra = (set(self.prices) - set(O)) | (set(self.ending) - set(O))
        if extra: raise Refused("TABLE_SHAPE", f"a price or an ending for no act: {sorted(extra)}")
        unread = sorted(set(self.params) - self.read)
        if unread: raise Refused("UNREAD_PARAMETER", ", ".join(unread))
        s = {"prior": self.prior, "T": self.T, "O": O, "N": int(self.N), "d": int(self.d),
             "table_sources": {"prior": self.prior_src, "utility": self.util_src, "price": self.price_src, "horizon": self.N_src, "depth": self.d_src, "kernels": dict(self.kernel_src)},
             "sources": {nm: a["reads"] for nm, a in self.acts.items()}, "components": list(self.space)}
        if self.N.denominator != 1 or self.d.denominator != 1: raise Refused("DEPTH", "horizon and depth are whole numbers")
        has = {k: k in self.seen for k in META_ONCE}
        if has["think"] or has["cost"] or has["rate"]:
            for need in ("think", "cost", "rate"):
                if not has[need]: raise Refused("MISSING", need)
            if self.dplus.denominator != 1: raise Refused("DEPTH_PLUS", "depth+ is a whole number")
            s.update({"dplus": int(self.dplus), "fraction": self.fraction, "rate": self.rate, "ops": self.ops})
            s["table_sources"].update({"fraction": self.fraction_src, "cost": self.cost_src, "rate": self.rate_src})
            fitted = "fitted" in (self.fraction_src, self.cost_src)
            if fitted and not has["score"]: raise Refused("UNSCORED", "a fitted fraction or cost carries its held-out score")
            if has["score"] and not fitted: raise Refused("MISSING", "the fitted table this score is for")
            if has["score"]: s["score"] = self.score
        elif has["score"]: raise Refused("MISSING", "think: a score with nothing to score")
        if self.closed: s["closed"] = True
        if self.bottom is not None: s["bottom"] = self.bottom
        if not set(self.prior) <= set(self.product()): raise Refused("TABLE_SHAPE", "the prior names a state outside the space")
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
    if "dplus" in s:                                                  # CHARTER v0.1
        if not (0 <= s["fraction"] <= 1): raise Refused("FRACTION")
        if set(s["ops"]) != set(range(1, len(omega) + 1)) or min(s["ops"].values()) < 0: raise Refused("COST")
        if s["rate"] < 0: raise Refused("RATE")
        if not (s["d"] == 1 and s["dplus"] == 2 and s["N"] >= 2): raise Refused("DEPTH_PLUS")
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
    L = ['world("w", closed=True)', f'horizon({N}, source="elicited")', f'depth({d}, source="elicited")', f'space({{"s": {list(w["prior"])!r}}})', f'prior({tbl(w["prior"])}, source="data")']
    ends = {k: a["ends"] for k, a in w["O"].items() if a["ends"]}
    e = ", ending={" + ", ".join(f"{k!r}: {{" + ", ".join(f"{o!r}: {tbl(u)}" for o, u in es.items()) + "}" for k, es in ends.items()) + "}" if ends else ""
    L.append("utility({" + ", ".join(f"{t!r}: {tbl(u)}" for t, u in w["T"].items()) + "}" + e + ', source="elicited")')
    L.append("price({" + ", ".join(f"{k!r}: {q(a['price'])}" for k, a in w["O"].items()) + '}, source="elicited")')
    for k, a in w["O"].items():
        rows = "{" + ", ".join(f"{st(s)}: {tbl(r)}" for s, r in a["K"].items()) + "}"
        L.append(f'act({k!r}, once={a["once"]}, kernel=table({rows}, source="data"), reads=["s"])')
    if "dplus" in w:
        L.append(f'think(depth={w["dplus"]}, fraction={q(w["fraction"])}, source="elicited")')
        L.append("cost([" + ", ".join(q(w["ops"][i]) for i in range(1, len(w["prior"]) + 1)) + '], source="elicited")')
        L.append(f'rate({q(w["rate"])}, source="elicited")')
    return "\n".join(L) + "\n"

HOSTS = {}

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__)); ok = True
    frozen = {"appendix.py": (F(-51, 50), "test"), "shared_draw.py": (F(0), "hold"), "wordle_mini.py": (F(-5, 3), "cat"), "noisy_test.py": (F(-319, 250), "test"),
              "two_sources.py": (F(-319, 250), "test"), "three_states.py": (F(3, 40), "k1"), "garbling_direction.py": (F(0), "hold"), "kernel_from_file.py": (F(-51, 50), "test"), "fitted_reads_data.py": (F(-51, 50), "test"), "prior_of_two_sources.py": (F(0), "hold"), "census_counts_cells.py": (F(-51, 50), "test"), "param_named_after_a_declaration.py": (F(-51, 50), "test")}
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
        text = open(os.path.join(here, "packs/poison", fn)).read(); want = {w.strip() for w in text.splitlines()[0].replace("# expect:", "").split("|")}
        try: check(text, HOSTS, os.path.join(here, "packs/ok")); got = "ACCEPTED"
        except Refused as e: got = e.name
        good = got in want; ok &= good
        print(f"  {'ok ' if good else 'BAD'} {fn:28s} {got}" + ("" if good else f"   (wanted {sorted(want)})"))
    rng = random.Random(2026); bad = 0
    for i in range(200):
        w = S.rand_world(rng); ren = {s: f"e{s[0]}z{s[1]}" for s in w["prior"]}
        w2 = {"prior": {ren[s]: p for s, p in w["prior"].items()}, "T": {t: {ren[s]: x for s, x in u.items()} for t, u in w["T"].items()},
              "O": {k: {"K": {ren[s]: r for s, r in a["K"].items()}, "price": a["price"], "once": a["once"], "ends": {o: {ren[s]: x for s, x in u.items()} for o, u in a["ends"].items()}} for k, a in w["O"].items()}}
        e = check(to_pack(w2, 2, 2))
        if any(e[k] != w2[k] for k in ("prior", "T", "O")) or list(e["T"]) != list(w2["T"]) or list(e["O"]) != list(w2["O"]): bad += 1
    print(f"round trip: {200 - bad}/200 random Worlds survive being printed as a pack and read back"); ok &= bad == 0
    import meta_check as M
    rng = random.Random(2027); bad = 0
    for i in range(100):
        w = M.rand_meta_world(rng); ren = {s: f"e{s[0]}z{s[1]}" for s in w["prior"]}
        w2 = {**w, "prior": {ren[s]: p for s, p in w["prior"].items()}, "T": {t: {ren[s]: x for s, x in u.items()} for t, u in w["T"].items()},
              "O": {k: {"K": {ren[s]: r for s, r in a["K"].items()}, "price": a["price"], "once": a["once"], "ends": {o: {ren[s]: x for s, x in u.items()} for o, u in a["ends"].items()}} for k, a in w["O"].items()}}
        e = check(to_pack(w2, w2["N"], w2["d"]))
        if any(e[k] != w2[k] for k in ("prior", "T", "O", "N", "d", "dplus", "fraction", "rate", "ops")): bad += 1
    print(f"round trip with a thought (R5): {100 - bad}/100 v0.1 Worlds survive"); ok &= bad == 0
    frozen_thoughts = {"appendix_think.py": ("think", "test"), "two_tests_think.py": ("think", "scan"), "think_struck_by_rate.py": ("struck_cap", "test"), "think_fitted_scored.py": ("think", "test")}
    for fn, want in frozen_thoughts.items():
        w = check(open(os.path.join(here, "packs/ok", fn)).read(), HOSTS, os.path.join(here, "packs/ok"))
        a_, how, paid = M.DPLUS.step(w["prior"], w, w["N"]); good = (how, a_) == want; ok &= good
        print(f"  {'ok ' if good else 'BAD'} {fn:26s} decide+ at the root: {how}, {a_}, paid {paid}")
    print("\nSURFACE PASSES" if ok else "\nSURFACE FAILS"); sys.exit(0 if ok else 1)
