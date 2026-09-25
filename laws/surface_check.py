"""
surface_check.py - tests the SURFACE pages (SURFACE.md and SURFACE-v0.1.md), not any implementation.
Part 1  a reference checker: pack text -> World spec (INTERFACE.md), or Refused(name). Parses with `ast`; never executes a pack.
Part 2  the corpus: every pack under packs/ok must elaborate and give the frozen answer; every pack under
        packs/poison must be refused by the name on its first line (`# expect: NAME`).
Part 3  round trip: random Worlds printed as packs must elaborate back to the same World (the grammar can say every World).
Run:  python3 laws/surface_check.py        (exit code 0 = the surface page passes)
"""
import ast, re, hashlib, inspect, itertools, json, keyword, os, random, sys, textwrap
from fractions import Fraction as F
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_check as S

CHUNK = 4000                                   # below Python's default int_max_str_digits (4300)

def long_int(digits):
    "a decimal digit string of any length as an int, CHUNK digits at a time: no interpreter-wide limit is lifted"
    n = 0
    for i in range(0, len(digits), CHUNK): c = digits[i:i + CHUNK]; n = n * 10 ** len(c) + int(c)
    return n

def decimal(n):
    "an int of any size as decimal digits, CHUNK at a time"
    if n < 0: return "-" + decimal(-n)
    if n < 10 ** CHUNK: return str(n)
    q_, r = divmod(n, 10 ** CHUNK); return decimal(q_) + str(r).rjust(CHUNK, "0")

def parse(text):
    """ast.parse, reading an integer literal longer than Python's default limit on integer conversion without lifting
    it (kit v0.13, brief 009: a real Score runs to tens of thousands of digits - the arena's 144 records gave about 35,700).
    Each such literal is swapped for a fresh name before parsing and read back CHUNK digits at a time. Returns the tree,
    {name: digits}, and the text as parsed, whose positions the tree's nodes give."""
    import io, tokenize
    try: toks = [t for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type == tokenize.NUMBER and len(t.string) > CHUNK]
    except (tokenize.TokenError, SyntaxError, IndentationError): toks = []
    longs = {}
    if toks:
        lines = text.split("\n"); starts = [0]
        for line in lines: starts.append(starts[-1] + len(line) + 1)
        for t in reversed(toks):
            if not t.string.isdigit(): continue
            i = len(longs)
            while f"_long{i}_" in text: i += 1000
            nm = f"_long{i}_"; longs[nm] = t.string
            a = starts[t.start[0] - 1] + t.start[1]; b = starts[t.end[0] - 1] + t.end[1]
            text = text[:a] + nm + text[b:]
    return ast.parse(text), longs, text

class Refused(Exception):
    def __init__(self, name, msg=""): super().__init__(f"{name}: {msg}"); self.name = name
TAGS = {"data", "elicited", "fitted"}
DECLS = ("world", "horizon", "depth", "space", "param", "prior", "utility", "price", "act", "depth_plus", "think", "cost", "rate", "score",
         "globals", "local_prior", "after", "counts", "falsifiers")                                  # SURFACE v0.2
ONCE_ONLY = ("world", "horizon", "depth", "space", "prior", "utility", "price")
META_ONCE = ("depth_plus", "think", "cost", "rate")     # SURFACE v0.1: optional, each at most once; score at most once per table
V02_ONCE = ("globals", "local_prior", "after", "counts", "falsifiers")  # SURFACE v0.2: optional, each at most once

class Checker:
    def __init__(self, text, hosts=None, data_dir="."):
        self.hosts, self.data_dir = hosts or {}, data_dir
        self.params, self.param_src, self.param_prov, self.read, self.seen, self.census = {}, {}, {}, set(), {}, {t: 0 for t in TAGS}
        self.host_prints = {}
        self.acts, self.kernel_src = {}, {}
        try: tree, self.longs, self.src = parse(text)
        except SyntaxError as e: raise Refused("SYNTAX", str(e))
        for st in tree.body:
            if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) and isinstance(st.value.func, ast.Name) and st.value.func.id in DECLS):
                raise Refused("NOT_A_DECLARATION", f"line {st.lineno}: a pack is a list of declarations and nothing else")
            name = st.value.func.id
            if (name in ONCE_ONLY or name in META_ONCE or name in V02_ONCE) and name in self.seen: raise Refused("DUPLICATE", ("[V2.0] " if name in V02_ONCE else "") + name)
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
        if isinstance(n, ast.Name) and n.id in self.longs: raise Refused("UNHOUSED_NUMERAL", f"line {n.lineno}: a number is not inside a table")
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
        if isinstance(n, ast.Name) and n.id in self.longs: return F(long_int(self.longs[n.id]))
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
        if "globals" in self.seen and self.locals_ and "local_prior" not in self.seen: raise Refused("MISSING", "[V2.3] local_prior: with Globals, the states are what P(Global) and P(local | Global) together give")
        if not set(self.prior) <= set(self.product()): raise Refused("TABLE_SHAPE", "the prior names a state outside the space")   # before a table reads one (kit v0.13)
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
            if getattr(self, "_paying", False) and c in getattr(self, "globals_", ()):   # CHARTER v0.2 S11 is one of form
                raise Refused("GLOBAL", f"[V2.10] line {n.lineno}: a utility written over the Global component {c!r}")
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
        # SURFACE v0.1 K16: a parameter's provenance is its own source and every source of every parameter its cell reads
        prov = {t}
        for node in ast.walk(a["value"]):
            if isinstance(node, ast.Name) and node.id in self.params: prov |= self.param_prov[node.id]
        self.param_prov[nm] = prov
    def d_prior(self, call):
        if "space" not in self.seen: raise Refused("MISSING", "space: the prior comes after the space")
        if "globals" in self.seen:                                   # SURFACE v0.2: the prior is P(Global)
            a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call); self.prior_src = t
            if not isinstance(a["table"], ast.Dict): raise Refused("NOT_A_DECLARATION", "[V2.2] the prior is a dict keyed by Global value")
            self.prior_g = self.table(a["table"], t, 1)
            want = set(self.gvalues())
            if set(self.prior_g) - want: raise Refused("TABLE_SHAPE", f"[V2.2] the prior names a Global value outside the space: {sorted(set(self.prior_g) - want)}")
            if any(p <= 0 for p in self.prior_g.values()) or sum(self.prior_g.values()) != 1: raise Refused("PRIOR", "[V2.2] P(Global) is strictly positive and sums to 1")
            if not self.locals_:                                 # all Global: the joint is the prior, one local value ()
                self.prior_l = {g: {(): F(1)} for g in self.prior_g}
                self.prior = {g: p for g, p in self.prior_g.items() if p > 0}
            return
        a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call); self.prior_src = t
        if not isinstance(a["table"], ast.Dict): raise Refused("NOT_A_DECLARATION", "the prior is a dict keyed by state: it is what says which states exist")
        self.prior = self.table(a["table"], t, 1)
    def keys_once(self, node, what):
        ks = [self.key(k) for k in node.keys]
        if any(k is None for k in node.keys): raise Refused("NOT_A_DECLARATION", f"{what}: no ** in a dict")
        if len(set(ks)) != len(ks): raise Refused("DUPLICATE", f"{what}: a key is written twice")
        return ks
    def d_utility(self, call):
        self._paying = True
        try: return self._d_utility(call)
        finally: self._paying = False
    def _d_utility(self, call):
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
    def owned(self, n, tag, allowed, name):
        """a meta-table cell: v0's cell rule, and every parameter it reads descends only from sources the table
        admits (attack s1 1a: a `data` param behind an `elicited` Rate label; s2 1.1: the same through a second
        param).  The fitted fence is num()'s."""
        for node in ast.walk(n):
            if isinstance(node, ast.Name) and node.id in self.params and not self.param_prov[node.id] <= allowed:
                raise Refused(name, f"line {n.lineno}: reads {node.id!r}, whose provenance is {sorted(self.param_prov[node.id])}; this table admits {sorted(allowed)}")
        return self.num(n, tag)
    def d_depth_plus(self, call):
        a = self.args(call, ("d",), ("source",), ("d",)); t = self.tag(a, call)
        if t != "elicited": raise Refused("TABLE_SOURCE", f"line {call.lineno}: depth+ is the owner's (J11), source elicited, not {t!r}")
        self.dplus = self.owned(a["d"], t, {"elicited"}, "TABLE_SOURCE"); self.dplus_src = t; self.census[t] += 1
    def d_think(self, call):
        a = self.args(call, (), ("fraction", "source"), ("fraction",)); t = self.tag(a, call)
        if t not in ("elicited", "fitted"): raise Refused("FRACTION", f"line {call.lineno}: a fraction is elicited or fitted, not {t!r}")
        self.fraction = self.owned(a["fraction"], t, {"elicited", "fitted"}, "FRACTION"); self.fraction_src = t; self.census[t] += 1
    def d_cost(self, call):
        if "prior" not in self.seen: raise Refused("MISSING", "prior: the cost table comes after the prior, whose states it counts")
        a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call)
        if t not in ("elicited", "fitted"): raise Refused("COST", f"line {call.lineno}: a cost is elicited or fitted, not {t!r}")
        if not isinstance(a["table"], ast.List): raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: cost is a list, one cell per live-state count, in order")
        cells = [self.owned(e, t, {"elicited", "fitted"}, "COST") for e in a["table"].elts]
        n = len(self.states())                                   # V2.4: with Globals, the joint's support (QUESTIONS.md Q17)
        if len(cells) != n: raise Refused("COST", f"line {call.lineno}: {len(cells)} cells for {n} states")
        self.ops = {i + 1: c for i, c in enumerate(cells)}; self.cost_src = t; self.census[t] += len(cells)
    def d_rate(self, call):
        a = self.args(call, ("r",), ("source",), ("r",)); t = self.tag(a, call)
        if t != "elicited": raise Refused("RATE", f"line {call.lineno}: the rate is the owner's, source elicited, not {t!r}")
        self.rate = self.owned(a["r"], t, {"elicited"}, "RATE"); self.rate_src = t; self.census[t] += 1
    def d_score(self, call):
        a = self.args(call, ("value",), ("of", "source"), ("value", "of")); t = self.tag(a, call); of = self.plain(a["of"])
        if t != "data": raise Refused("TABLE_SOURCE", f"line {call.lineno}: a score is measured, source data, not {t!r}")
        if of == "counts":                                            # SURFACE v0.2: the Score of shipped Counts
            if hasattr(self, "counts_score"): raise Refused("DUPLICATE", "[V2.8] score of 'counts'")
            self.counts_score = self.owned(a["value"], t, {"data"}, "TABLE_SOURCE"); self.census[t] += 1; return
        if of not in ("fraction", "cost"): raise Refused("NOT_A_DECLARATION", f"line {call.lineno}: a score is of the fraction, the cost or the counts")
        if not hasattr(self, "scores"): self.scores = {}
        if of in self.scores: raise Refused("DUPLICATE", f"score of {of!r}")
        self.scores[of] = self.owned(a["value"], t, {"data"}, "TABLE_SOURCE"); self.census[t] += 1
    # ---- SURFACE v0.2: what is learned between episodes
    def gvalues(self):
        vs = [self.space[c] for c in self.globals_]
        return [x[0] if len(self.globals_) == 1 else x for x in itertools.product(*vs)]
    def lvalues(self):
        if not self.locals_: return [()]
        vs = [self.space[c] for c in self.locals_]
        return [x[0] if len(self.locals_) == 1 else x for x in itertools.product(*vs)]
    def split(self, state):
        "a state of the space into (local tuple, Global tuple)"
        st = state if isinstance(state, tuple) else (state,)
        names = list(self.space)
        return tuple(st[names.index(c)] for c in self.locals_), tuple(st[names.index(c)] for c in self.globals_)
    def join(self, l, g):
        names = list(self.space); d = dict(zip(self.locals_, l)); d.update(zip(self.globals_, g))
        st = tuple(d[c] for c in names)
        return st[0] if len(st) == 1 else st
    def d_globals(self, call):
        if "space" not in self.seen: raise Refused("MISSING", "[V2.1] space: the Globals are components of the space")
        if "prior" in self.seen: raise Refused("MISSING", "[V2.1] globals: which components persist is said before the prior")
        a = self.args(call, ("components",), (), ("components",)); names = self.plain(a["components"])
        if not isinstance(names, list) or not names or not all(isinstance(c, str) for c in names): raise Refused("NOT_A_DECLARATION", '[V2.1] globals(["component", ...])')
        if len(set(names)) != len(names): raise Refused("DUPLICATE", "[V2.1] a Global component named twice")
        for c in names:
            if c not in self.space: raise Refused("UNKNOWN_NAME", f"[V2.1] component {c!r}")
        self.globals_ = [c for c in self.space if c in names]; self.locals_ = [c for c in self.space if c not in names]
        # K19 as re-ruled (session 2, 2.2): a World may be all Global - a monitor; its one local value is ()
    def d_local_prior(self, call):
        if "globals" not in self.seen: raise Refused("MISSING", "[V2.3] globals: P(local | Global) needs the Globals")
        if not self.locals_: raise Refused("NOT_A_DECLARATION", "[V2.3] a World whose every component is Global has no local to give a law")
        if "prior" not in self.seen: raise Refused("MISSING", "[V2.3] prior: P(local | Global) comes after P(Global)")
        a = self.args(call, ("table",), ("source",), ("table",)); t = self.tag(a, call); self.local_prior_src = t
        rows = self.table(a["table"], t, 2)
        if set(rows) != set(self.prior_g): raise Refused("TABLE_SHAPE", "[V2.3] local_prior needs a row for exactly the Global values the prior names")
        lv = set(self.lvalues())
        for g, row in rows.items():
            if set(row) - lv: raise Refused("TABLE_SHAPE", f"[V2.3] local_prior row {g!r} names a local value outside the space")
            if any(p < 0 for p in row.values()) or sum(row.values()) != 1: raise Refused("PRIOR", f"[V2.3] local_prior row {g!r}: cells never negative, summing to 1")
        self.prior_l = rows
        # the joint: every table over states is keyed by the states it gives positive prior
        self.prior = {}
        for g, pg in self.prior_g.items():
            for l, pl in rows[g].items():
                if pg * pl > 0: self.prior[self.join(l if isinstance(l, tuple) else (l,), g if isinstance(g, tuple) else (g,))] = pg * pl
    def d_after(self, call):
        if "space" not in self.seen: raise Refused("MISSING", "[V2.5] space: the After-act reads components of the space (QUESTIONS.md Q17)")
        a = self.args(call, ("name",), ("kernel", "reads"), ("name", "kernel", "reads")); nm = self.plain(a["name"]); kn = a["kernel"]
        reads = self.plain(a["reads"])
        if not isinstance(nm, str): raise Refused("NOT_A_DECLARATION", "[V2.5] after(name, kernel=table(...), reads=[...])")
        if not (isinstance(reads, list) and all(isinstance(c, str) for c in reads)): raise Refused("NOT_A_DECLARATION", "[V2.5] an After-act's reads is a list of components")
        for c in reads:
            if c not in self.space: raise Refused("UNKNOWN_NAME", f"[V2.5] component {c!r}")
        if not (isinstance(kn, ast.Call) and isinstance(kn.func, ast.Name) and kn.func.id == "table"): raise Refused("NOT_A_DECLARATION", "[V2.5] an After-act's kernel is table({end: {state: {outcome: p}}}, source=...)")
        ka = self.args(kn, ("rows",), ("source",), ("rows",)); t = self.tag(ka, kn)
        K = self.table(ka["rows"], t, 3)
        for end, rows in K.items():                       # SURFACE v0 section 4: every row checked where it is written (QUESTIONS.md Q10a)
            for st, row in rows.items():
                if any(q < 0 for q in row.values()) or sum(row.values()) != 1: raise Refused("KERNEL_ROW", f"[V2.5] the After-act's kernel at {end!r}, {st!r} is not a distribution")
        comps = list(self.space); idx = [i for i, c in enumerate(comps) if c in reads]
        for end, rows in K.items():                       # the reads rule, as for an act (session 1, 4.2)
            seen = {}
            for st, row in rows.items():
                proj = tuple((st if len(comps) == 1 else st[i]) for i in idx)
                if seen.setdefault(proj, row) != row: raise Refused("UNDECLARED_READ", f"[V2.5] After-act {nm!r} depends on a component missing from reads={reads}")
        self.after = {"name": nm, "K": K, "src": t}
    def record(self, node, lineno, falsifier=False):
        "a record [[[act, outcome], ...], end, after]: names, and None for an absent end (a falsifier only) or after-report"
        bad = Refused("NOT_A_DECLARATION", f"[V2.6] line {lineno}: a record is [[[act, outcome], ...], end, after-outcome or None]")
        if not (isinstance(node, ast.List) and len(node.elts) == 3): raise bad
        draws = self.plain(node.elts[0])
        none = lambda n: isinstance(n, ast.Constant) and n.value is None
        end = None if none(node.elts[1]) else self.plain(node.elts[1])
        after = None if none(node.elts[2]) else self.plain(node.elts[2])
        if not (isinstance(draws, list) and all(isinstance(x, list) and len(x) == 2 and all(isinstance(y, str) for y in x) for x in draws)): raise bad
        if not (isinstance(end, str) or (falsifier and end is None)) or not (after is None or isinstance(after, str)): raise bad
        return (tuple(tuple(x) for x in draws), end, after)
    def d_counts(self, call):
        a = self.args(call, ("rows",), ("sha256", "source"), ("rows", "sha256")); t = self.tag(a, call)
        if t != "data": raise Refused("TABLE_SOURCE", f"[V2.6] line {call.lineno}: Counts are facts, source data, not {t!r}")
        if not isinstance(a["rows"], ast.List): raise Refused("NOT_A_DECLARATION", "[V2.6] counts([[draws, end, after, n], ...], sha256=...)")
        out = Counter()
        for row in a["rows"].elts:
            if not (isinstance(row, ast.List) and len(row.elts) == 4): raise Refused("NOT_A_DECLARATION", f"[V2.6] line {row.lineno}: a Counts row is [draws, end, after, n]")
            n = row.elts[3]
            if isinstance(n, ast.Constant) and isinstance(n.value, float): raise Refused("FLOAT", f"[V2.6] line {n.lineno}")
            seg = self.longs[n.id] if isinstance(n, ast.Name) and n.id in self.longs else ast.get_source_segment(self.src, n)
            if seg is None or not re.fullmatch(r"[1-9][0-9]*", seg): raise Refused("NOT_A_DECLARATION", f"[V2.6] line {row.lineno}: a multiplicity is written as decimal digits, not {seg!r}")
            mult = long_int(seg)
            rec_ = self.record(ast.List(elts=row.elts[:3], ctx=ast.Load(), lineno=row.lineno), row.lineno)
            if rec_ in out: raise Refused("DUPLICATE", f"[V2.6] line {row.lineno}: a record written twice")
            out[rec_] = mult; self.census[t] += 1
        sha = self.plain(a["sha256"])
        if not isinstance(sha, str): raise Refused("NOT_A_DECLARATION", "[V2.6] sha256 is the digest's hex, a name")
        self.counts_ = out; self.counts_sha_ = sha
    def d_falsifiers(self, call):
        a = self.args(call, ("records",), (), ("records",))
        if not isinstance(a["records"], ast.List): raise Refused("NOT_A_DECLARATION", "[V2.7] falsifiers([[draws, end, after], ...])")
        out = [self.record(e, call.lineno, falsifier=True) for e in a["records"].elts]
        if len(set(out)) != len(out): raise Refused("DUPLICATE", "[V2.7] a falsifying record written twice")
        self.falsifiers_ = out
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
            if rows.setdefault(proj, row) != row: raise Refused("UNDECLARED_READ", f"[V0.reads] act {nm!r} depends on a component missing from reads={reads}")
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
        if "globals" in self.seen: return self.spec_v02()
        if "local_prior" in self.seen: raise Refused("MISSING", "[V2.3] globals: local_prior is for a World that declares Globals")
        if hasattr(self, "counts_score") and "counts" not in self.seen: raise Refused("MISSING", "[V2.8] counts: a score of counts with no Counts (QUESTIONS.md Q12)")
        if any(g in self.seen for g in ("after", "counts", "falsifiers")):          # session 1, 2.1: no Global needed
            self.globals_, self.locals_ = [], list(self.space)
            self.prior_g = {(): F(1)}; self.prior_l = {(): dict(self.prior)}
            return self.spec_v02()
        return self.spec_v01()
    def spec_v02(self):
        "SURFACE v0.2: build the joint World, validate it as v0 does, then project it and apply CHARTER v0.2's refusals"
        import counts_check as CC
        if self.globals_ and self.locals_ and "local_prior" not in self.seen: raise Refused("MISSING", "[V2.3] local_prior")
        for need in ONCE_ONLY:                                    # before any table is read (QUESTIONS.md Q17)
            if need not in self.seen: raise Refused("MISSING", need)
        if "falsifiers" in self.seen and "counts" not in self.seen: raise Refused("MISSING", "[V2.7] counts: falsifying records travel with the Counts they ended")
        if getattr(self, "after", None):
            if self.after["name"] not in self.prices: raise Refused("MISSING", f"[V2.5] a price for the After-act {self.after['name']!r}")
            if self.prices[self.after["name"]] < 0: raise Refused("PRICE", f"[V2.5] the After-act's price is a price, at least 0 (QUESTIONS.md Q10c)")
            aprice = self.prices.pop(self.after["name"])
        s = self.spec_v01()
        if getattr(self, "after", None): self.prices[self.after["name"]] = aprice
        if self.globals_ and s.get("bottom") is not None: raise Refused("NOT_A_DECLARATION", "[V2.14] a catch-all state beside Globals is not sayable in v0.2 (K25)")
        for t in self.T:
            if isinstance(t, str) and t.startswith("end:"): raise Refused("NOT_A_DECLARATION", f"[V2.6] the terminal {t!r}: names beginning 'end:' are reserved for ending ends")
        tup = lambda x: x if isinstance(x, tuple) else (x,)
        W = {"locals": [(c, list(self.space[c])) for c in self.locals_], "globals": [(c, list(self.space[c])) for c in self.globals_],
             "prior_global": {tup(g): p for g, p in self.prior_g.items()},
             "prior_local": {tup(g): {tup(l): p for l, p in row.items() if p > 0} for g, row in self.prior_l.items()} if self.globals_ else {(): {tup(st): p for st, p in self.prior.items() if p > 0}},
             "T": {t: {self.split(st): u for st, u in r.items()} for t, r in s["T"].items()},
             "O": {k: {"K": {self.split(st): row for st, row in a["K"].items()}, "price": a["price"], "once": a["once"],
                       **({"ends": set(a["ends"]), "u_end": {o: {self.split(st): u for st, u in us.items()} for o, us in a["ends"].items()}} if a["ends"] else {})}
                   for k, a in s["O"].items()},
             "N": s["N"], "d": s["d"]}
        for key in ("closed", "bottom", "dplus", "fraction", "rate", "ops"):
            if key in s: W[key] = s[key]
        if getattr(self, "after", None):
            om = set(self.states()); K = {}
            for end, rows in self.after["K"].items():
                if set(rows) - om: raise Refused("TABLE_SHAPE", f"[V2.4] the After-act's rows at {end!r} name {sorted(set(rows) - om, key=repr)[0]!r}, which is not a state (QUESTIONS.md Q10b)")
                e = end if isinstance(end, str) else f"end:{end[0]}={end[1]}" if isinstance(end, tuple) and len(end) == 2 else end
                if e in K: raise Refused("DUPLICATE", f"[V2.5] two rows of the After-act's kernel name the end {e!r} (QUESTIONS.md Q10e)")
                K[e] = {self.split(st): row for st, row in rows.items()}
            W["after"] = {"K": K, "price": self.prices[self.after["name"]], "name": self.after["name"]}
        if "counts" in self.seen:
            W["counts"] = self.counts_; W["counts_sha"] = self.counts_sha_
            if hasattr(self, "counts_score"): W["score"] = self.counts_score
            if hasattr(self, "falsifiers_"): W["falsifiers"] = self.falsifiers_
        elif hasattr(self, "counts_score"): raise Refused("MISSING", "[V2.8] counts: a score of counts with no Counts")
        try: return CC.refuse(W)
        except S.Refused as e: raise Refused(str(e), f"[{getattr(e, 'rule', 'C2')}] CHARTER v0.2: {e}")
    def spec_v01(self):
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
        has = {k: k in self.seen for k in META_ONCE}; scores = getattr(self, "scores", {})
        if any(has.values()) or scores:
            for need in META_ONCE:
                if not has[need]: raise Refused("MISSING", need)
            if self.dplus.denominator != 1: raise Refused("DEPTH_PLUS", "depth+ is a whole number")
            s.update({"dplus": int(self.dplus), "fraction": self.fraction, "rate": self.rate, "ops": self.ops})
            s["table_sources"].update({"dplus": self.dplus_src, "fraction": self.fraction_src, "cost": self.cost_src, "rate": self.rate_src})
            fitted = {t for t, src in (("fraction", self.fraction_src), ("cost", self.cost_src)) if src == "fitted"}
            if fitted - set(scores): raise Refused("UNSCORED", f"a fitted {sorted(fitted - set(scores))} carries its held-out score")
            if set(scores) - fitted: raise Refused("MISSING", f"the fitted table this score is for: {sorted(set(scores) - fitted)}")
            if scores: s["score"] = dict(scores)
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

def _plain_text(text):
    "SURFACE v0.2 (draft 3): a pack is UTF-8 text; a coding declaration naming anything else, or a lone surrogate, is refused"
    import re
    for line in text.splitlines()[:2]:
        m = re.match(r"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)", line)
        if m and m.group(1).lower().replace("_", "-") not in ("utf-8", "utf8"): raise Refused("NOT_A_DECLARATION", f"[V2.11] a pack is UTF-8, not {m.group(1)}")
    if "\r" in text: raise Refused("NOT_A_DECLARATION", "[V2.11] a pack's lines end in LF; it holds no CR, so a name is the same to every reader (session 3, 3.1)")
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in text): raise Refused("NOT_A_DECLARATION", "[V2.11] a pack is UTF-8 text, and no UTF-8 text holds a surrogate code point (QUESTIONS.md Q17)")
    import io, tokenize
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.NAME and not tok.string.isascii():
                raise Refused("NOT_A_DECLARATION", f"[V2.11] line {tok.start[0]}: an identifier is ASCII; {tok.string!r} would be folded to another name")
    except (tokenize.TokenError, SyntaxError, IndentationError): pass
    try: tree = parse(text)[0]
    except SyntaxError: return
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and any(0xD800 <= ord(ch) <= 0xDFFF for ch in node.value):
            raise Refused("NOT_A_DECLARATION", f"[V2.11] line {node.lineno}: a name holds a lone surrogate, which no text can")

def check(text, hosts=None, data_dir="."): _plain_text(text); return Checker(text, hosts, data_dir).spec()
def census(text, hosts=None, data_dir="."): _plain_text(text); c = Checker(text, hosts, data_dir); c.spec(); return c.census

# ---------------------------------------------------------------- Part 3 helper: print a World as a pack
def q(x): return decimal(x.numerator) if x.denominator == 1 else f"{decimal(x.numerator)}/{decimal(x.denominator)}"
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
        L.append(f'depth_plus({w["dplus"]}, source="elicited")')
        L.append(f'think(fraction={q(w["fraction"])}, source="elicited")')
        L.append("cost([" + ", ".join(q(w["ops"][i]) for i in range(1, len(w["prior"]) + 1)) + '], source="elicited")')
        L.append(f'rate({q(w["rate"])}, source="elicited")')
    return "\n".join(L) + "\n"

def to_pack_v02(W):
    "SURFACE v0.2: print a counts_check World as a pack (R7)"
    lc = [c for c, _ in W["locals"]]; gc = [c for c, _ in W["globals"]]; comps = dict(W["locals"]); comps.update(dict(W["globals"]))
    one = lambda t: t[0] if len(t) == 1 else t
    def st(l, g): return one(tuple(l) + tuple(g))
    tbl = lambda m: "{" + ", ".join(f"{k!r}: {q(v)}" for k, v in m.items()) + "}"
    L = ['world("w", closed=True)', f'horizon({W["N"]}, source="elicited")', f'depth({W["d"]}, source="elicited")',
         "space({" + ", ".join(f"{c!r}: {comps[c]!r}" for c in lc + gc) + "})"]
    if gc:
        L += [f"globals({gc!r})", "prior({" + ", ".join(f"{one(g)!r}: {q(p)}" for g, p in W["prior_global"].items()) + '}, source="elicited")']
    else:                                                      # no Global: v0's prior over states (K21: an After-act needs none)
        L.append("prior({" + ", ".join(f"{one(l)!r}: {q(p)}" for l, p in W["prior_local"][()].items()) + '}, source="elicited")')
    if lc and gc: L.append("local_prior({" + ", ".join(f"{one(g)!r}: " + "{" + ", ".join(f"{one(l)!r}: {q(p)}" for l, p in row.items()) + "}" for g, row in W["prior_local"].items()) + '}, source="elicited")')
    over = lambda m: "{" + ", ".join(f"{st(l, g)!r}: {q(v)}" for (l, g), v in m.items()) + "}"
    ending = {k: a["u_end"] for k, a in W["O"].items() if a.get("ends")}          # kit v0.13: a World with ending outcomes prints
    e = (", ending={" + ", ".join(f"{k!r}: {{" + ", ".join(f"{o!r}: {over(u)}" for o, u in ue.items()) + "}" for k, ue in ending.items()) + "}") if ending else ""
    L.append("utility({" + ", ".join(f"{t!r}: {over(u)}" for t, u in W["T"].items()) + "}" + e + ', source="elicited")')
    prices = {k: a["price"] for k, a in W["O"].items()}
    if W.get("after"): prices[W["after"].get("name", "after")] = W["after"]["price"]
    L.append("price({" + ", ".join(f"{k!r}: {q(v)}" for k, v in prices.items()) + '}, source="elicited")')
    for k, a in W["O"].items():
        rows = "{" + ", ".join(f"{st(l, g)!r}: {tbl(r)}" for (l, g), r in a["K"].items()) + "}"
        L.append(f'act({k!r}, once={a["once"]}, kernel=table({rows}, source="elicited"), reads={lc + gc!r})')
    if W.get("after"):
        ends = {f"end:{k}={o}": (k, o) for k, a in W["O"].items() for o in a.get("ends", ())}      # V2.5: an ending end is (act, outcome)
        rows = "{" + ", ".join(f"{ends.get(e, e)!r}: " + "{" + ", ".join(f"{st(l, g)!r}: {tbl(r)}" for (l, g), r in K.items()) + "}" for e, K in W["after"]["K"].items()) + "}"
        L.append(f'after({W["after"].get("name", "after")!r}, kernel=table({rows}, source="elicited"), reads={lc + gc!r})')
    if W.get("counts") is not None and "counts_sha" in W:
        rows = ", ".join("[" + repr([list(x) for x in obs]) + f", {t!r}, {oa!r}, {n}]" for (obs, t, oa), n in W["counts"].items())
        L.append(f'counts([{rows}], sha256={W["counts_sha"]!r}, source="data")')
        if W.get("falsifiers"):
            L.append("falsifiers([" + ", ".join("[" + repr([list(x) for x in obs]) + f", {t!r}, {oa!r}]" for obs, t, oa in W["falsifiers"]) + "])")
        L.append(f'score({q(W["score"])}, of="counts", source="data")')
    return "\n".join(L) + "\n"

HOSTS = {}

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__)); ok = True
    frozen = {"appendix.py": (F(-51, 50), "test"), "shared_draw.py": (F(0), "hold"), "wordle_mini.py": (F(-5, 3), "cat"), "noisy_test.py": (F(-319, 250), "test"),
              "two_sources.py": (F(-319, 250), "test"), "three_states.py": (F(3, 40), "k1"), "garbling_direction.py": (F(0), "hold"), "kernel_from_file.py": (F(-51, 50), "test"), "fitted_reads_data.py": (F(-51, 50), "test"), "prior_of_two_sources.py": (F(0), "hold"), "census_counts_cells.py": (F(-51, 50), "test"), "param_named_after_a_declaration.py": (F(-51, 50), "test"),
              "appendix_a.py": (F(1, 4), "ask"), "appendix_a_shipped.py": (F(17, 50), "ask"), "falsified_refit.py": (F(1140850621, 3355443250), "ask"), "router_credence_prior.py": (F(1, 6), "exec"), "two_instruments.py": (F(23, 80), "ask"), "after_without_globals.py": (F(1, 4), "ask"), "monitor_all_global.py": (F(0, 1), "ship"), "monitor_shipping.py": (F(0, 1), "file"), "prefix_falsifier.py": (F(11912381800368774150598599799, 14931164199631225849401400201), "ask"), "quotes_in_names.py": (F(127, 1220), "ask"), "quotes_escaped_digest.py": (F(0, 1), "abstain"), "bottom_without_globals.py": (F(43, 100), "ask"), "product_kernel_name_counts.py": (F(39, 100), "both"), "refit_scored_falsifier.py": (F(4, 11), "ask"),
              # kit v0.13
              "think_with_globals.py": (F(63, 200), "ask"), "ending_outcome_graded.py": (F(3, 8), "ask"), "global_value_unnamed.py": (F(1, 4), "ask"),
              "falsifiers_before_counts.py": (F(1140850621, 3355443250), "ask"), "prefix_falsifier_ending.py": (F(21, 50), "ask")}
    print("lawful packs:")
    for fn in sorted(os.listdir(os.path.join(here, "packs/ok"))):
        if not fn.endswith(".py"): continue
        try:
            w = check(open(os.path.join(here, "packs/ok", fn), encoding="utf-8", newline="").read(), HOSTS, os.path.join(here, "packs/ok"))
            if "globals" in w:
                import counts_check as CC
                ew = CC.episode_world(w, CC.evidence(w)); got = S.REF.solve(ew["prior"], ew, ew["N"])
            else: got = S.REF.solve(w["prior"], w, w["N"])
            c = census(open(os.path.join(here, "packs/ok", fn), encoding="utf-8", newline="").read(), HOSTS, os.path.join(here, "packs/ok"))
            good = frozen.get(fn) in (None, got); ok &= good
            print(f"  {'ok ' if good else 'BAD'} {fn:22s} V_N, act = {got[0]}, {got[1]}   numerals by source: {c}")
        except Refused as e: ok = False; print(f"  BAD {fn}: refused {e}")
    print("poison packs:")
    for fn in sorted(os.listdir(os.path.join(here, "packs/poison"))):
        text = open(os.path.join(here, "packs/poison", fn), encoding="utf-8", newline="").read(); want = {w.strip() for w in text.splitlines()[0].replace("# expect:", "").split("|")}
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
    # ---- SURFACE v0.2
    import counts_check as CC
    rng = random.Random(2028); bad = 0; tried = 0
    while tried < 100:
        W = CC.rand_world(rng)
        try: CC.refuse(W)
        except S.Refused: continue
        tried += 1
        if rng.random() < 0.5:
            recs = CC.rand_records(W, rng, 3); c = Counter(recs)
            if CC.expressible(W, c): W["counts"] = c; W["counts_sha"] = CC.counts_sha(c); W["score"] = CC.loo_score(W, c)
        try: e = check(to_pack_v02(W))
        except S.Refused as ex: bad += 1; continue
        keys = ("locals", "globals", "prior_global", "prior_local", "T", "N", "d", "counts", "counts_sha", "score")
        if any(e.get(k) != W.get(k) for k in keys) or {k: v["K"] for k, v in e["O"].items()} != {k: v["K"] for k, v in W["O"].items()} or e["after"]["K"] != W["after"]["K"]: bad += 1
    print(f"round trip with Globals (R7): {100 - bad}/100 v0.2 Worlds survive, half of them shipping Counts"); ok &= bad == 0
    # kit v0.13: the pinned Worlds - ending outcomes among them - print and read back too (R7)
    bad = [label for label, maker in CC.PINNED.items() if "dplus" not in maker()
           for W in [maker()] for e in [check(to_pack_v02(W))] if any(e.get(k) != W.get(k) for k in ("locals", "globals", "prior_global", "T", "N", "d"))
           or {g: {l: p for l, p in r.items() if p} for g, r in e["prior_local"].items()} != {g: {l: p for l, p in r.items() if p} for g, r in W["prior_local"].items()}
           or {k: (v["K"], v.get("ends"), v.get("u_end")) for k, v in e["O"].items()} != {k: (v["K"], v.get("ends"), v.get("u_end")) for k, v in W["O"].items()}
           or (e.get("after") or {}).get("K") != (W.get("after") or {}).get("K")]
    print(f"round trip of the pinned Worlds (R7): {len(CC.PINNED) - len(bad)}/{len(CC.PINNED)} survive" + (f"; not {bad}" if bad else "")); ok &= not bad
    # kit v0.13: vectors - a raw surrogate handed over as text (QUESTIONS.md Q17), a Score of tens of thousands of digits
    try: check('world("\ud800", closed=True)\n'); got = "ACCEPTED"
    except Refused as e: got = e.name
    except Exception as e: got = f"raised {type(e).__name__}"
    good = got == "NOT_A_DECLARATION"; ok &= good
    print(f"  {'ok ' if good else 'BAD'} a raw lone surrogate, handed over as a str: {got}")
    W = CC.reliability_world([F(9, 10), F(3, 5)], [F(1, 2), F(1, 2)], F(-2)); rng = random.Random(1); recs = Counter()
    for _ in range(300):
        a_ = rng.choice(["a1", "a2"]); recs[((("ask", a_),), "say " + a_, a_ if rng.random() < F(4, 5) else {"a1": "a2", "a2": "a1"}[a_])] += 1
    W["counts"] = recs; W["counts_sha"] = CC.counts_sha(recs); W["score"] = CC.loo_score(W, recs)
    digits = len(decimal(W["score"].denominator))
    try: good = check(to_pack_v02(W))["score"] == W["score"] and digits > 4300
    except Exception as e: good = False
    ok &= good; print(f"  {'ok ' if good else 'BAD'} appendix A shipping 300 records: a Score of {digits} digits reads without lifting Python's limit of 4300")
    frozen_thoughts = {"appendix_think.py": ("think", "test"), "two_tests_think.py": ("think", "scan"), "think_struck_by_rate.py": ("struck_cap", "test"), "think_fitted_scored.py": ("think", "test"), "fitted_think_reads_elicited.py": ("think", "test")}
    for fn, want in frozen_thoughts.items():
        w = check(open(os.path.join(here, "packs/ok", fn), encoding="utf-8", newline="").read(), HOSTS, os.path.join(here, "packs/ok"))
        a_, how, paid = M.DPLUS.step(w["prior"], w, w["N"]); good = (how, a_) == want; ok &= good
        print(f"  {'ok ' if good else 'BAD'} {fn:26s} decide+ at the root: {how}, {a_}, paid {paid}")
    print("\nSURFACE PASSES" if ok else "\nSURFACE FAILS"); sys.exit(0 if ok else 1)
