"""
mutations.py - the corpus, mutated: every pack under packs/ok and packs/poison, with each of the edits below applied
one at a time. Used by two gate checks (kit v0.13): `mutation_check.py` (every variant is a World or a named refusal,
never another exception) and `model_check.py` (every World the reference accepts has model.py's values, and a row
written twice under two spellings of one key is refused).

The edits, each a class of fault a reader must survive:
  lines   each line deleted, doubled, swapped with the next, moved to the front, moved to the end (QUESTIONS.md Q17);
  cells   each number negated, set to 0, and less 1 - a price of 0 becomes -1 (Q10a, Q10c);
  keys    each dict given one more row, under a key no table has (Q10b);
  spell   each After-act row whose key the pages spell two ways - an ending end as (act, outcome) or "end:act=outcome", a state of
          a one-component space as a name or a one-name tuple - written again under the other (Q10e);
  stance  `closed=True` replaced by `bottom=` each state the pack's prior names (Q10d);
  text    a byte-order mark, a raw lone surrogate inside the first string, a CR LF for the first line end (Q16, Q17).
The builder's own differential (gfrmin/wald, tests/test_surface_differential.py) found Q17 on 13,445 of these; this is the
reference's half of it, run by the gate so that a crash in the reference is found before a builder finds it.
"""
import ast, io, os, re, tokenize

HERE = os.path.dirname(os.path.abspath(__file__))

def corpus():
    "(folder/name, text) for every pack, read as its bytes are written (V2.11)"
    for folder in ("ok", "poison"):
        d = os.path.join(HERE, "packs", folder)
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".py"): yield f"{folder}/{fn}", open(os.path.join(d, fn), "rb").read().decode("utf-8")

def _lines(text):
    L = text.split("\n")
    for i in range(len(L)):
        yield f"minus line {i}", "\n".join(L[:i] + L[i + 1:])
        yield f"line {i} twice", "\n".join(L[:i + 1] + [L[i]] + L[i + 1:])
        if i + 1 < len(L): yield f"lines {i}, {i + 1} swapped", "\n".join(L[:i] + [L[i + 1], L[i]] + L[i + 2:])
        if i: yield f"line {i} first", "\n".join([L[i]] + L[:i] + L[i + 1:])
        if i + 1 < len(L): yield f"line {i} last", "\n".join(L[:i] + L[i + 1:] + [L[i]])

def _offsets(text, utf8=False):
    "a (line, column) position as an index into the text; `ast` counts columns in UTF-8 bytes, `tokenize` in characters"
    lines = text.split("\n"); starts, n = [0], 0
    for line in lines: n += len(line) + 1; starts.append(n)
    def at(row, col):
        if utf8: col = len(lines[row - 1].encode("utf-8", "surrogatepass")[:col].decode("utf-8", "surrogatepass"))
        return starts[row - 1] + col
    return at

def _tree(text):
    try: return ast.parse(text)
    except (SyntaxError, ValueError, UnicodeError): return None

def _cells(text):
    "each number literal negated, and set to 0: tokenize finds them, so a number inside a string is never touched"
    try: toks = [t for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type == tokenize.NUMBER]
    except (tokenize.TokenError, SyntaxError, IndentationError): return
    at = _offsets(text)
    for t in toks:
        a, b = at(*t.start), at(*t.end)
        yield f"number {t.string} at {t.start} negated", text[:a] + "-" + text[a:]
        yield f"number {t.string} at {t.start} set to 0", text[:a] + "0" + text[b:]
        yield f"number {t.string} at {t.start} less 1", text[:a] + "(" + text[a:b] + "-1)" + text[b:]

def _strs(k):
    return isinstance(k, ast.Constant) and isinstance(k.value, str)

def _dicts(tree):
    return [n for n in ast.walk(tree) if isinstance(n, ast.Dict) and n.keys and all(k is not None for k in n.keys)]

def _keys(text):
    "each dict literal given one more row, a copy of its first under a key no table can have"
    tree = _tree(text)
    if tree is None: return
    at = _offsets(text, utf8=True)
    for n in _dicts(tree):
        k, v = n.keys[0], n.values[0]
        vs = ast.get_source_segment(text, v)
        if _strs(k): nk = repr(k.value + "~stranger")
        elif isinstance(k, ast.Tuple) and k.elts and all(_strs(e) for e in k.elts): nk = repr((k.elts[0].value + "~stranger",) + tuple(e.value for e in k.elts[1:]))
        else: continue
        a = at(n.lineno, n.col_offset) + 1
        yield f"a stranger row in the dict at line {n.lineno}", text[:a] + f"{nk}: {vs}, " + text[a:]

def _respellings(k, states):
    """the other spellings the pages give one key: an ending end as (act, outcome) or "end:act=outcome" (V2.5, V2.6), and
    a state of a one-component space as its name or a one-name tuple. An act named "t" and one named ("t",) are two acts,
    not one key: only a key the pages spell two ways is respelled."""
    if _strs(k):
        m = re.fullmatch(r"end:(.*)=(.*)", k.value, re.S)
        out = [repr((k.value,))] if k.value in states else []
        if m: out.append(repr((m.group(1), m.group(2))))
        return out
    if isinstance(k, ast.Tuple) and all(_strs(e) for e in k.elts):
        vals = tuple(e.value for e in k.elts)
        out = []
        if len(vals) == 2 and vals not in states: out.append(repr(f"end:{vals[0]}={vals[1]}"))
        if len(vals) == 1 and vals[0] in states: out.append(repr(vals[0]))
        return out
    return []

def _after_tables(tree):
    "the rows of each After-act's kernel: after(name, kernel=table({end: {state: ...}}))"
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "after":
            for kw in n.keywords:
                t = kw.value
                if kw.arg == "kernel" and isinstance(t, ast.Call) and t.args and isinstance(t.args[0], ast.Dict): yield t.args[0]

def spellings(text, states=()):
    """each row whose key the pages spell two ways, written again under the other spelling: one key, written twice.
    Scoped to the After-act's kernel, the one table the reference reads through a map of spellings (an end both ways, a
    state as a name or a one-name tuple); every other table over states is checked against Omega as written, before any
    spelling is mapped, so a second spelling there is a stranger row, which the `keys` edit already writes."""
    tree = _tree(text)
    if tree is None: return
    at = _offsets(text, utf8=True); states = set(states)
    for top in _after_tables(tree):
        for n in [top] + [v for v in top.values if isinstance(v, ast.Dict)]:
            for k, v in zip(n.keys, n.values):
                for nk in _respellings(k, states):
                    vs = ast.get_source_segment(text, v); a = at(n.lineno, n.col_offset) + 1
                    yield f"the row {ast.get_source_segment(text, k)} at line {n.lineno} again as {nk}", text[:a] + f"{nk}: {vs}, " + text[a:]

def _stance(text, states):
    if "closed=True" not in text: return
    for s in states[:4]: yield f"closed=True -> bottom={s!r}", text.replace("closed=True", f"bottom={s!r}", 1)

def _text(text):
    yield "a byte-order mark", "﻿" + text
    m = re.search(r'"', text)
    if m: yield "a raw lone surrogate in the first string", text[:m.end()] + "\ud800" + text[m.end():]
    if "\n" in text: yield "a CR LF for the first line end", text.replace("\n", "\r\n", 1)

def states_of(text):
    "the states a lawful pack's prior names, as the space spells them - for the stance edit (at most four)"
    import surface_check as SC
    try: c = SC.Checker(text, {}, os.path.join(HERE, "packs", "ok")); c.spec(); return list(c.prior)
    except Exception: return []

def all_variants(name, text):
    "every mutation of the corpus pack `name` (folder/file): a lawful pack's states feed the stance edit"
    return variants(text, states_of(text) if name.startswith("ok/") else ())

def variants(text, states=()):
    "(label, text) for every mutation of one pack; `states` are the states its prior names, for the stance edit"
    yield from _lines(text)
    yield from _cells(text)
    yield from _keys(text)
    yield from spellings(text, states)
    yield from _stance(text, states)
    yield from _text(text)
