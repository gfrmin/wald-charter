# INTERFACE — how the kit talks to an implementation

The kit imports `wald.kit_adapter` from the path given by `--impl` and calls `make_agent()`. The adapter is a thin test-only shim over the real kernel; it converts plain data to the kernel's own types and back. Nothing in the adapter may choose, update or compute on its own (CHARTER E5).

All numbers are `fractions.Fraction`. States, acts and outcomes are hashable values (strings or tuples).

**World** (a plain dict):
- `prior`: `{state: Fraction}`, strictly positive, summing to 1.
- `T`: `{terminal_act: {state: Fraction}}`, in menu order (dict order is the declared order). Non-empty.
- `O`: `{observational_act: spec}`, in menu order, where `spec` is
  `{"K": {state: {outcome: Fraction}}, "price": Fraction, "once": bool, "ends": {outcome: {state: Fraction}}}`.
  `ends` maps each ending outcome to its u_end.

**The agent** returned by `make_agent()` has four methods:
- `push(b, K) -> {outcome: Fraction}` — the predictive P_b(o|k).
- `condition(b, K, o) -> {state: Fraction}` — the posterior. If P_b(o|k) = 0 it raises an exception whose class is named `WorldFalsified`.
- `expect(b, f) -> Fraction` — E_b[f] for `f: {state: Fraction}`.
- `decide(b, world, n, used) -> act` — decide_n(b, M): the first entry of M attaining V_n. `b` is a belief as `{state: Fraction}`; `used` is a frozenset of `once` acts already executed (M is the declared menu without them); `n` is the number of observations left. The kit passes `n = min(d, n)` itself when it tests a floor.

The kit never reads the implementation's source. It checks C1–C11, S5 and E2 of the signed page on worlds drawn from a seed kept in CI, on forced-tie variants of them (J3), and on the appendix vector.
