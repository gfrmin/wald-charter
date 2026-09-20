# SURFACE v0

Status: in force from the author-signed tag surface-v0

Marks **[K1]–[K11]** are author judgements, ruled in §7. `laws/surface_check.py` is a reference checker for this page; `laws/packs/` is its corpus.

## 1. What a pack is

A pack is a text file in Python's syntax. It is **parsed and never executed** **[K1]**: the checker reads the syntax tree, builds a World (the dict of `INTERFACE.md`) and hands it to `declare`. Every top-level statement is a call to one of the nine declarations of §2. Inside a declaration there are only names in quotes, `True` and `False`, lists, tuples and dicts of these, table cells (§3), `by`, and the kernel forms of §4. There is no import, assignment, definition, branch, loop, comparison, boolean operator, conditional expression, lambda, comprehension, attribute, subscript, f-string, starred argument or call to any other name. What the grammar does not give a form, a pack cannot say: in particular it cannot choose (CHARTER E5), compare a probability (S1) or update a belief (§2).

## 2. The nine declarations

| declaration | says |
|---|---|
| `world(name, closed=True)` or `world(name, bottom=state)` | the World and its stance on zero evidence (S5). A `bottom` names a state of Ω, and in every kernel that state's row gives every outcome of that kernel a mass above zero; otherwise `ZERO_EVIDENCE`. A World that is neither is `ZERO_EVIDENCE` too. |
| `horizon(N, source=…)`, `depth(d, source=…)` | the Horizon and the Depth (E3), whole numbers, each with its own source |
| `space({component: [names], …})` | the components. A state is a name (one component) or a tuple of names, in declared order. |
| `param(name, value, source=…)` | **a table cell written once and read by name [K11]**. It is not a seventh place for numerals: it is housed in every table that reads it, which is why CHARTER S3 refuses a parameter nobody reads. The name is an identifier that is not a Python keyword; it is declared once and read by cells declared after it. |
| `prior({state: number}, source=…)` | P₀, written out state by state (no `by`). **Ω is the set of states the prior names** **[K10]**: a state of the product it leaves out is not in Ω, and a prior cell of zero is refused (`PRIOR`): leave the state out. Every other table over states comes after the prior and has exactly the states of Ω as its keys, no fewer and no more. |
| `utility({act: table}, ending={act: {outcome: table}}, source=…)` | u and u_end. The terminal acts, in this order, are the first part of the menu (J3). |
| `price({act: number}, source=…)` | the Price of every observational act |
| `act(name, once=True\|False, kernel=…, reads=[…])` | an observational act, declared once; `once=False` is `fresh`. Acts join the menu in declared order. |

`world`, `horizon`, `depth`, `space`, `prior`, `utility` and `price` appear exactly once. A table over states is a dict keyed by state, or `by(component, {value: …})` when it depends on one component only; a `by` has a row for exactly the values of its component that occur in Ω. A key written twice in one dict, or a state listed twice in a `data` file, is refused. A name is one act: no name is both a terminal and an observational act.

**`reads` [K9].** Every act says what it reads: a non-empty list of components of the space and, for a `once` act, named private sources. A component its kernel names (in `point` or `by`) must be in `reads`, and the kernel may depend on no component outside `reads`; the checker verifies both (`UNDECLARED_READ`). A source named by two acts must be a component, and a `fresh` act that names anything but a component is refused: both are `SHARED_SOURCE` (CHARTER S2). What the page cannot check is whether two instruments share something the pack never named; it can only make the pack say what it claims.

## 3. Numbers (CHARTER S3)

A number appears only in a table cell (written in place, or once as a `param`), a mixture weight, a `price`, the `horizon` or the `depth`: these are CHARTER S3's six tables, a mixture weight being part of its Kernel. A cell is an integer, a ratio of integers, a parameter, or `+ − * /` and unary minus over these **[K2]**. No decimals: `0.9` is refused, `9/10` is lawful. Division by zero is refused. A number anywhere else is refused, 0 and 1 included **[K3]**. Every table and every `param` names its `source`: `data`, `elicited` or `fitted`. A parameter keeps its own source wherever it is read. **`fitted` is fenced**: whatever reads a `fitted` parameter must itself say `fitted`; there is no way, in v0, to promote a fitted number (CHARTER E4 sends a fitted pack to the held-out comparison). A parameter nobody reads is refused. The checker returns the count of **quantities** by source — each cell, parameter, weight, price, horizon and depth counts once, however it is written — which scoreboards print.

## 4. Kernels (CHARTER S4)

A kernel is built from these and nothing else. Every row of probabilities is checked where it is written: each cell non-negative, each row summing to 1 — in a `table`, a `by`, a `data` file, a garbling, and the weights of a `mixture` (`KERNEL_ROW`). A combination of things that are not kernels is refused even when the result would be one.

| form | meaning |
|---|---|
| `table({state: {outcome: number}}, source=…)`, `by(component, {value: {outcome: number}}, source=…)` | rows written out |
| `point(component)` | emits the value of a component of the state, with certainty |
| `data(file, sha256=…, source=data\|fitted)` **[K5]** | rows read from a JSON file beside the pack: a list of `[state, {outcome: "a/b"}]` pairs, a tuple state written as a JSON list. The pack pins the file by the SHA-256 of its bytes; a file that does not match is refused (`DATA_HASH`). An `elicited` number is written in the pack, where its owner can see it. |
| `mixture([(weight, kernel), …], source=…)` | weights non-negative, summing to 1 |
| `product(kernel, kernel)` | both outcomes, independent given the state |
| `compose(kernel, {outcome: {outcome: number}}, source=…)` | the first kernel read through a garbling: the outer key is the outcome the first kernel emitted, the inner key is what is seen |

Each table names its own source, and the World records every source an act's kernel draws on **[K6]**.

## 5. Refusals, by name

Of the surface: `SYNTAX`, `NOT_A_DECLARATION`, `DUPLICATE`, `BAD_NAME`, `UNKNOWN_NAME`, `FLOAT`, `DIVISION_BY_ZERO`, `UNHOUSED_NUMERAL`, `TABLE_SOURCE`, `DATA_HASH`, `UNDECLARED_READ`, `MISSING`, `UNREAD_PARAMETER`. Of the World, from `declare`: `EMPTY_T`, `TABLE_SHAPE`, `PRIOR`, `KERNEL_ROW`, `PRICE`, `DEPTH`, `ZERO_EVIDENCE`, `SHARED_SOURCE`.

**Which name [K7].** Anything the grammar of §1 gives no form, wherever it stands, is `NOT_A_DECLARATION`. A pack that breaks one rule is refused by that rule's name. A pack that breaks several is refused by one of their names; which one is not specified, and no tool may depend on it. (Conformance suites for WebAssembly, JSON Schema and TOML promise rejection, not the identity of the first error; two attack sessions showed why.)

**No defaults.** Nothing in a pack has a default: no cell, no source, no `reads`, no `once`. What is not written is refused, never assumed. A kernel is a table from states to distributions over outcomes: rows are keyed by state and each row sums to 1.

## 6. Consequences — what the kit will check

- **R1 Round trip.** Every World of `INTERFACE.md`, its states renamed to names, can be printed as a pack that elaborates back to the same World, menu order included.
- **R2 Poisons.** Every pack in `laws/packs/poison` is refused by the name on its first line, or, where that line lists several, by one of them.
- **R3 Frozen answers.** Every pack in `laws/packs/ok` elaborates, and the oracle's V_N and act on it are the frozen ones.
- **R4 Inertness.** Checking a pack imports nothing, opens no file but a `data` file beside the pack, and calls nothing. No code outside the checker runs.

## 7. Rulings

| mark | question | ruling | date |
|---|---|---|---|
| K1 | Python's syntax, parsed and never executed | accept | 2026-09-20 |
| K2 | arithmetic over integers and parameters is allowed inside a cell | accept | 2026-09-20 |
| K3 | no number outside a table, 0 and 1 included (stricter than CHARTER S3) | accept | 2026-09-20 |
| K4 | **reversed.** There is no `host` form in v0. Two attack sessions showed a page cannot keep numbers out of arbitrary code (a state's name, `ord("*")`). Big deterministic tables enter as `data` files; hosts return in a later version as author-custodied, fingerprinted code | accept | 2026-09-20 |
| K5 | **amended.** `data` files for `data` and `fitted` tables only, pinned by the SHA-256 of their bytes; `elicited` numbers live in the pack | accept | 2026-09-20 |
| K6 | **replaced.** Every table and `param` names its source; a parameter keeps its own source wherever read; only `fitted` is fenced (no promotion in v0); the count is of quantities, not numerals; horizon and depth are sourced separately | accept | 2026-09-20 |
| K7 | **replaced.** One broken rule, that rule's name; several, any one of theirs. No ordering is promised | accept | 2026-09-20 |
| K8 | out of v0, named for later: host instruments (as author-custodied builtins with typed signatures that receive declared features, never a state's name); a factored or decision-diagram kernel form for big deterministic tables; an owner's endorsement of a `fitted` number; numeric latent components | accept | 2026-09-20 |
| K9 | **new.** `reads` is mandatory; a component the kernel names, or depends on, must be in it; undeclared sharing in the world is beyond the page | accept | 2026-09-20 |
| K11 | **new.** A `param` is a cell read by name, housed in the tables that read it; CHARTER S3's list is not extended. Erratum queued for CHARTER v0.1: S3 should name parameters where it lists the tables | accept | 2026-09-20 |
| K10 | **new.** Ω is the set of states the prior names | accept | 2026-09-20 |

Attack sessions:
- Session 1, on draft 1 (2026-09-20): 13 findings claimed (1.1–1.3, 2.1–2.3, 3.1, 3.2, 4.1–4.3, 5.1, 5.2); 13 reproduced, each now a pack in `laws/packs/`; all resolved in draft 2. Finding 1.3 is resolved as far as a page can: the pack must say what it reads and the checker holds it to that; an instrument shared in the world and never named is a modelling claim, like ⊥ (CHARTER J5).
- Session 2, on draft 2 (2026-09-20): 10 findings claimed (1.1–1.3, 3.1, 4.1, 4.2, 5.1–5.4); 10 reproduced, each now a pack; all resolved in draft 3. Findings 1.1 and 1.2 are resolved by concession: the `host` form is withdrawn (K4).
- Prior-art review (2026-09-20), between sessions 2 and 3: data files pinned by hash (Dhall, Nix, Bazel); `fitted` made absorbing (integrity lattices; endorsement deferred); refusal order dropped (conformance-suite practice); no defaults (the `.pomdp` and RDDL pitfalls). Draft 4.
- Session 3, run on draft 3 (2026-09-20): 13 findings claimed (1.1–1.4, 2.1, 3.1, 3.2, 4.1, 5.1–5.5); all reproduce against draft 3. 1.1–1.4, 2.1, 3.2 and 4.1 are resolved in draft 5 and are packs in the corpus; 3.1 was already resolved by draft 4's pinned list-of-pairs file; 5.1–5.5 are retired by draft 4's K7, with `NOT_A_DECLARATION` now stated as the name for any form the grammar lacks. Nothing is carried to v0.1.
- Session 4, on draft 5 (2026-09-20): 2 findings claimed; nothing in categories 2 and 3; the newest machinery held. (1) The ⊥ full-support rule was enforced by the checker but never stated on the page, and no corpus pack used `bottom`: now stated, with one lawful and two poison packs. (4) CHARTER S3's list of tables does not name `param`: resolved by K11 without touching the signed page, with an erratum queued for CHARTER v0.1. Neither changes an act or the checker. Draft 6 is the signing text.
- Signed as `surface-v0`: ___ claimed, ___ reproduced, resolved or carried to v0.1: ___.
