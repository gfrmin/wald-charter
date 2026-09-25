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
    locals: List[Tuple[Name, List[Name]]]
    globals: List[Tuple[Name, List[Name]]]
    prior_global: Dict[Global, Fraction]
    prior_local: Dict[Global, Dict[Local, Fraction]]
    T: Dict[Name, Dict[State, Fraction]]
    O: Dict[Name, Act]
    after: After
    N: int
    d: int
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
