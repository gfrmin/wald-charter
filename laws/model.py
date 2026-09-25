"""
model.py - the typed shape of what the references, the kit and any implementation pass between them (kit v0.12).
Shape mismatches between modules were the last class of bug the gate did not find: an ending utility a number in one
module and a per-state table in another; a record's end a string in one place and a pair in another; `None` inside a
record read by one reader and not another. This module states each shape once, with types a checker can read and
validators the gate and the kit run on every World and record they touch.
"""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple, TypedDict, Union

Name = str
Outcome = Union[Name, Tuple[Name, ...]]          # a product kernel's outcome is a tuple of names (K27: never in a record)
Local = Tuple[Name, ...]                          # a local value: one name per local component, () when there is none
Global = Tuple[Name, ...]                         # a Global value: one name per Global component, () when there is none
State = Tuple[Local, Global]
Draw = Tuple[Name, Name]                          # (act, outcome) - in a record every outcome is a name (V2.6)
End = Optional[Name]                              # a terminal, "end:act=outcome" (V2.6), or None for a prefix falsifier
Record = Tuple[Tuple[Draw, ...], End, Optional[Name]]
Kernel = Dict[State, Dict[Outcome, Fraction]]

class Act(TypedDict, total=False):
    K: Kernel
    price: Fraction
    once: bool
    ends: Set[Outcome]                            # ending outcomes
    u_end: Dict[Outcome, Dict[State, Fraction]]   # an ending utility is a per-state table, never a number

class After(TypedDict, total=False):
    K: Dict[Name, Dict[State, Dict[Name, Fraction]]]   # end -> state -> after-outcome -> p
    price: Fraction
    name: Name

class World(TypedDict, total=False):
    locals: List[Tuple[Name, List[Name]]]         # the space's components and values; the prior may name fewer (Q11)
    globals: List[Tuple[Name, List[Name]]]
    prior_global: Dict[Global, Fraction]          # the Global values P(Global) names: these, not the space's, are the Globals of Omega
    prior_local: Dict[Global, Dict[Local, Fraction]]
    T: Dict[Name, Dict[State, Fraction]]
    O: Dict[Name, Act]
    after: After
    N: int
    d: int
    closed: bool
    bottom: Union[Name, Tuple[Name, ...]]         # the catch-all state as the space spells it; only without Globals (V2.14)
    dplus: int
    fraction: Fraction
    rate: Fraction
    ops: Dict[int, Fraction]
    counts: Counter
    counts_sha: str
    score: Fraction
    falsifiers: List[Record]

class ShapeError(Exception):
    "a value that is not the shape model.py states"

def _tuple_of_names(x, what):
    if not (isinstance(x, tuple) and all(isinstance(v, str) for v in x)): raise ShapeError(f"{what} is a tuple of names, not {x!r}")

def _prob(p, what):
    if not isinstance(p, Fraction) or isinstance(p, bool): raise ShapeError(f"{what} is an exact Fraction, not {type(p).__name__} {p!r}")

def check_record(r, falsifier=False):
    "V2.6, V2.7: (draws, end, after): draws a tuple of (act, name) pairs; end a name, or None only for a prefix falsifier"
    if not (isinstance(r, tuple) and len(r) == 3): raise ShapeError(f"a record is (draws, end, after), not {r!r}")
    draws, end, after = r
    if not isinstance(draws, tuple) or not all(isinstance(d, tuple) and len(d) == 2 and all(isinstance(x, str) for x in d) for d in draws):
        raise ShapeError(f"a record's draws are a tuple of (act, outcome) name pairs, not {draws!r}")
    if end is None and not falsifier: raise ShapeError("only a falsifier's record may have no end")
    if end is not None and not isinstance(end, str): raise ShapeError(f"an end is a name, not {end!r}")
    if after is not None and not isinstance(after, str): raise ShapeError(f"an after-report is a name or None, not {after!r}")
    if end is None and after is not None: raise ShapeError("a prefix falsifier has no after-report")

def check_world(W):
    "every shape of World, stated once; raises ShapeError at the first departure"
    for key in ("locals", "globals", "prior_global", "prior_local", "T", "O", "N", "d"):
        if key not in W: raise ShapeError(f"a World has {key!r}")
    for part in ("locals", "globals"):
        for c, vs in W[part]:
            if not isinstance(c, str) or not isinstance(vs, list) or not all(isinstance(v, str) for v in vs): raise ShapeError(f"{part}: (name, [names])")
    for g, p in W["prior_global"].items(): _tuple_of_names(g, "a Global value"); _prob(p, "P(Global)")
    for g, row in W["prior_local"].items():
        _tuple_of_names(g, "a Global value")
        for l, p in row.items(): _tuple_of_names(l, "a local value"); _prob(p, "P(local | Global)")
    def state(s):
        if not (isinstance(s, tuple) and len(s) == 2): raise ShapeError(f"a state is (local, Global), not {s!r}")
        _tuple_of_names(s[0], "a state's local"); _tuple_of_names(s[1], "a state's Global")
    for t, row in W["T"].items():
        for s, u in row.items(): state(s); _prob(u, f"utility of {t!r}")
    for k, a in W["O"].items():
        for s, row in a["K"].items():
            state(s)
            for o, p in row.items():
                if not (isinstance(o, str) or (isinstance(o, tuple) and all(isinstance(v, str) for v in o))): raise ShapeError(f"an outcome is a name or a tuple of names, not {o!r}")
                _prob(p, f"kernel of {k!r}")
        _prob(a["price"], f"price of {k!r}")
        if not isinstance(a["once"], bool): raise ShapeError(f"once of {k!r} is a bool")
        if "ends" in a and not isinstance(a["ends"], (set, frozenset)): raise ShapeError(f"ends of {k!r} is a set, not {type(a['ends']).__name__}")
        for o, ue in a.get("u_end", {}).items():
            if not isinstance(ue, dict): raise ShapeError(f"the ending utility of {k!r} at {o!r} is a per-state table, not {ue!r}")
            for s, u in ue.items(): state(s); _prob(u, "an ending utility")
    if W.get("after"):
        for e, K in W["after"]["K"].items():
            if not isinstance(e, str): raise ShapeError(f"an end is a name, not {e!r}")
            for s, row in K.items():
                state(s)
                for o, p in row.items():
                    if not isinstance(o, str): raise ShapeError(f"an after-outcome is a name, not {o!r}")
                    _prob(p, "the After-act's kernel")
        _prob(W["after"]["price"], "the After-act's price")
    if not (isinstance(W["N"], int) and isinstance(W["d"], int)) or isinstance(W["N"], bool): raise ShapeError("N and d are ints")
    if "counts" in W:
        if not isinstance(W["counts"], Counter): raise ShapeError("Counts are a Counter of records")
        for r, n in W["counts"].items():
            check_record(r)
            if not (isinstance(n, int) and not isinstance(n, bool) and n >= 1): raise ShapeError(f"a multiplicity is a whole number >= 1, not {n!r}")
    for f in W.get("falsifiers", []): check_record(f, falsifier=True)
    if "score" in W: _prob(W["score"], "the Score")
    if "counts_sha" in W and not (isinstance(W["counts_sha"], str) and len(W["counts_sha"]) == 64): raise ShapeError("the digest is 64 hex characters")

def omega(W) -> Set[State]:
    "the states: the pairs (local, Global) to which P(Global) and P(local | Global) together give positive probability (V2.4)"
    return {(l, g) for g, pg in W["prior_global"].items() if pg > 0 for l, pl in W["prior_local"].get(g, {}).items() if pl > 0}

def ends_of(W) -> Set[Name]:
    "every end: each terminal, and each ending outcome as end:act=outcome (V2.5, V2.6)"
    return set(W["T"]) | {f"end:{k}={o}" for k, a in W["O"].items() for o in a.get("ends", ())}

def _space(dims):
    out = [()]
    for _, vs in dims: out = [x + (v,) for x in out for v in vs]
    return set(out)

def _dist(row, what):
    if any(p < 0 for p in row.values()) or sum(row.values()) != 1: raise ShapeError(f"{what} is a distribution: cells never negative, summing to 1")

def _over(table, om, what):
    if set(table) != om: raise ShapeError(f"{what} is keyed by exactly the states of Omega (V2.4): {len(set(table) - om)} beyond it, {len(om - set(table))} missing")

def bottom_state(W) -> State:
    "the catch-all as a state of Omega: without Globals, the whole state is the local (V2.14)"
    b = W["bottom"]
    return (b if isinstance(b, tuple) else (b,), ())

def check_values(W):
    """values, not only types (kit v0.13): every row a distribution, the After-act's included; every table over states keyed
    by exactly Omega; the After-act's kernel keyed by exactly the ends; every price at least 0; a catch-all state gives every
    outcome of every kernel positive mass, the After-act's included. A key written twice cannot be seen in a dict: that
    half of the rule is `mutation_check.py`'s, which writes rows twice under two spellings of one key and asks for a refusal.
    Raises ShapeError at the first departure. Call check_world first: this assumes its shapes."""
    pg = W["prior_global"]
    if any(p <= 0 for p in pg.values()) or sum(pg.values()) != 1: raise ShapeError("P(Global) is strictly positive and sums to 1 (V2.2)")
    if set(W["prior_local"]) != set(pg): raise ShapeError("P(local | Global) has a row for exactly the Global values P(Global) names (V2.3)")
    gspace, lspace = _space(W["globals"]), _space(W["locals"])
    if not set(pg) <= gspace: raise ShapeError("P(Global) names a value outside the space (V2.2)")
    for g, row in W["prior_local"].items():
        _dist(row, f"P(local | {g!r})")
        if not set(row) <= lspace: raise ShapeError(f"P(local | {g!r}) names a local value outside the space (V2.3)")
    om = omega(W)
    for t, u in W["T"].items(): _over(u, om, f"the utility of {t!r}")
    for k, a in W["O"].items():
        _over(a["K"], om, f"the kernel of {k!r}")
        for s, row in a["K"].items(): _dist(row, f"the kernel of {k!r} at {s!r}")
        if a["price"] < 0: raise ShapeError(f"the price of {k!r} is at least 0")
        named = {o for row in a["K"].values() for o in row}
        ends = set(a.get("ends", ()))
        if not ends <= named: raise ShapeError(f"an ending outcome of {k!r} is one its kernel names")
        if set(a.get("u_end", {})) != ends: raise ShapeError(f"{k!r} has an ending utility for exactly its ending outcomes")
        for o, ue in a.get("u_end", {}).items(): _over(ue, om, f"the ending utility of {k!r} at {o!r}")
    if W.get("after"):
        A = W["after"]
        if set(A["K"]) != ends_of(W): raise ShapeError("the After-act's kernel is keyed by exactly the ends (V2.5)")
        for e, K in A["K"].items():
            _over(K, om, f"the After-act's kernel at {e!r}")
            for s, row in K.items(): _dist(row, f"the After-act's kernel at {e!r}, {s!r}")
        if A["price"] < 0: raise ShapeError("the After-act's price is at least 0 (V2.5)")
    if "bottom" in W and W["bottom"] is not None:
        if W["globals"]: raise ShapeError("a catch-all state beside Globals is not sayable (V2.14)")
        b = bottom_state(W)
        if b not in om: raise ShapeError("the catch-all is a state of Omega")
        for k, a in W["O"].items():
            named = {o for row in a["K"].values() for o in row}
            if any(a["K"][b].get(o, 0) <= 0 for o in named): raise ShapeError(f"the catch-all gives every outcome of {k!r} positive mass (S5)")
        for e, K in (W["after"]["K"].items() if W.get("after") else ()):
            named = {o for row in K.values() for o in row}
            if any(K[b].get(o, 0) <= 0 for o in named): raise ShapeError(f"the catch-all gives every after-outcome under {e!r} positive mass (C2.S12)")
