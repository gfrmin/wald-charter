# SURFACE v0 — draft 1, ruled, awaiting attack

Status: unsigned. Nothing here is in force until the author's signed tag `surface-v0`. This page is subordinate to `CHARTER.md` (tag `charter-v0`): it says how a World is written down. It adds no semantics.

Marks **[K1]–[K8]** are author judgements, ruled in §7. `laws/surface_check.py` is a reference checker for this page; `laws/packs/` is its corpus.

## 1. What a pack is

A pack is a text file in Python's syntax. It is **parsed and never executed** **[K1]**: the checker reads the syntax tree, builds a World (the dict of `INTERFACE.md`) and hands it to `declare`. A pack is a list of top-level calls to the eight declarations of §2 and nothing else. There is no import, assignment, definition, branch, loop, comparison, boolean operator, lambda, comprehension, attribute, subscript, f-string or call to any other name. What the grammar does not give a form, a pack cannot say: in particular it cannot choose (CHARTER E5), compare a probability (S1) or update a belief (§2).

## 2. The eight declarations

| declaration | says |
|---|---|
| `world(name, closed=True)` or `world(name, bottom=state)` | the World and its stance on zero evidence (S5) |
| `clock(horizon=N, depth=d, source=…)` | the Horizon and the Depth (E3) |
| `space(component=[names], …)` | Ω, the product of the components. A state is a name (one component) or a tuple of names, in declared order. |
| `param(name, value, source=…)` | a named number, usable in any table cell declared after it |
| `prior(table, source=…)` | P₀, a table over states |
| `utility({act: table}, ending={act: {outcome: table}}, source=…)` | u and u_end. The terminal acts, in this order, are the first part of the menu (J3). |
| `price({act: number}, source=…)` | the Price of every observational act |
| `act(name, once=True\|False, kernel=…, reads=[sources])` | an observational act; `once=False` is `fresh`. Acts join the menu in declared order. `reads` names sources; a source that is a component of the space is a declared component of Ω (S2). |

`world`, `clock`, `space`, `prior`, `utility` and `price` appear exactly once. A table over states is a dict keyed by state, or `by(component, {value: …})` when it depends on one component only.

## 3. Numbers (CHARTER S3)

A number appears only in a table cell, a `param`, a `price`, or the `clock`. A cell is an integer, a ratio of integers, a parameter, or `+ − * /` and unary minus over these **[K2]**. No decimals: `0.9` is refused, `9/10` is lawful. A number anywhere else is refused, 0 and 1 included **[K3]**. Every table names its `source`: `data`, `elicited` or `fitted`. A parameter nobody reads is refused. The checker returns the count of numerals by source, which scoreboards print.

## 4. Kernels (CHARTER S4)

A kernel is built from these and nothing else:

| form | meaning |
|---|---|
| `table({state: {outcome: number}}, source=…)`, `by(component, {value: {outcome: number}}, source=…)` | rows written out |
| `point(component)` | emits the value of a component of the state, with certainty |
| `host(name)` **[K4]** | a deterministic instrument: a pure function from the state to an outcome, registered by the host under `name`. Its rows sum to 1 by construction. It sees a state, never a belief, a utility or the menu. |
| `data(file, source=data\|fitted)` **[K5]** | rows read from a JSON file beside the pack, ratios as strings. An `elicited` number is written in the pack, where its owner can see it. |
| `mixture([(weight, kernel), …], source=…)` | weights non-negative, summing to 1 |
| `product(kernel, kernel)` | both outcomes, independent given the state |
| `compose(kernel, {outcome: {outcome: number}}, source=…)` | the first kernel read through a garbling |

All tables inside one act's kernel share one source **[K6]**.

## 5. Refusals, by name

Of the surface: `SYNTAX`, `NOT_A_DECLARATION`, `UNKNOWN_NAME`, `UNKNOWN_HOST`, `FLOAT`, `UNHOUSED_NUMERAL`, `UNREAD_PARAMETER`, `DUPLICATE`, `MISSING`. Of the World, passed through from `declare`: `EMPTY_T`, `PRIOR`, `KERNEL_ROW`, `DEPTH`, `ZERO_EVIDENCE`, `SHARED_SOURCE`, `TABLE_SOURCE`, `PRICE`, `TABLE_SHAPE`. The first rule broken, reading top to bottom, names the refusal **[K7]**.

## 6. Consequences — what the kit will check

- **R1 Round trip.** Every World of `INTERFACE.md` can be printed as a pack that elaborates back to the same World, menu order included. The grammar can say every lawful World.
- **R2 Poisons.** Every pack in `laws/packs/poison` is refused by the name on its first line.
- **R3 Frozen answers.** Every pack in `laws/packs/ok` elaborates, and the oracle's V_N and act on it are the frozen ones.
- **R4 Inertness.** Checking a pack imports nothing, opens no file but a `data` file beside the pack, and calls no function but registered hosts.

## 7. Rulings

| mark | question | ruling | date |
|---|---|---|---|
| K1 | Python's syntax, parsed and never executed | accept | 2026-09-20 |
| K2 | arithmetic over integers and parameters is allowed inside a cell | accept | 2026-09-20 |
| K3 | no number outside a table, 0 and 1 included (stricter than CHARTER S3) | accept | 2026-09-20 |
| K4 | `host(name)`: deterministic host instruments are lawful kernels; stochastic ones are not, in v0 | accept | 2026-09-20 |
| K5 | `data` files for `data` and `fitted` tables only; `elicited` numbers live in the pack | accept | 2026-09-20 |
| K6 | one source per act's kernel | accept | 2026-09-20 |
| K7 | the first rule broken names the refusal | accept | 2026-09-20 |
| K8 | out of v0: numeric latent components (write a grid of named values and its tables by hand), generated tables, stochastic hosts | accept | 2026-09-20 |

Attack sessions:
- Session 1, on draft 1: ___ claimed, ___ reproduced, all resolved: yes / no.
