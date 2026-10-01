# The Counts' likelihood, measured (2026-10-01, steel)

**The question** (HANDOFF §6): an episode's cost grows with the Counts on the arena's World — does S13 admit an exact sufficient form of the Counts' likelihood that would stop it?

**The answer: the question was aimed at the wrong place.** Counts are already the sufficient statistic (CHARTER v0.2 §4, "Why Counts and not a posterior"), and computing P(Global | Counts) from them is a small part of an episode. The cost is in the lookahead: it carries the posterior's exact masses — about 16 bits a record, 9,735 bits each at 600 records — through sums over 13,824 states as Python `Fraction`s, each with its own reduced denominator, and `Fraction` addition takes a gcd of two long denominators every time. At 600 records, 53 of an episode's 66 seconds are `math.gcd`. The lookahead visits 71 nodes. Nothing here is the law's: the same measure scaled to integers by a common denominator gives the same acts and the same final belief 3–4× faster, exactly, with nothing persisted.

**World**: the arena's `omniscience-p1-c0` pack (stage 2, `gfrmin/wald-arena` master `51f5adc`), 1,152 Global values × 12 locals = 13,824 states, N = d = 3, shipping 300 calibration records of 24 distinct. `T = 600` doubles every multiplicity. wald v0.2.1 from the arena's venv (`~/git/wald-arena/.venv`), run from the pack's directory. Scripts: `profile_counts.py` (the posterior three ways, the episode, a cProfile at the last T), `scaled_prior.py` (the same episode from a normalised and from an integer-scaled prior). Door scripted: `b1`, `all`, `same`, `right`.

## 1. Where an episode's seconds go (`profile_counts.out`)

| records T | `posterior_global` (kernel: `_update` per token) | normalise once (the reference's form) | bits per mass | `episode_prior` | `_play` (the episode) |
|---|---|---|---|---|---|
| 0 | 0.00 s | 0.00 s | 11 | 0.01 s | 1.3 s |
| 300 | 3.3 s | 1.4 s | 4,866 | 3.5 s | 20.0 s |
| 600 | 4.8 s | 1.7 s | 9,735 | 5.3 s | 57.2 s |

cProfile of `episode_prior` + `_play` at T = 600: 65.6 s in all; `math.gcd` 53.5 s (5.8 M calls), all from `Fraction._add` (53.3 s) under `_dot` (37.8 s) and `_mass` (15.6 s); `_value` 71 calls; `posterior_global` 8.7 s. Peak RSS 1.26 GB with the memo cleared between episodes.

The kernel's `posterior_global` normalises after every token (`_update`, "the one update"); the reference's `post_global` multiplies every token in and normalises once. Same rationals; the kernel's form costs 2.3–2.8× more. Both are a tenth of the episode.

## 2. The lookahead from an integer measure (`scaled_prior.out`)

`scaled_prior` builds P(Global | Counts) P(local | Global) times one integer: each record's likelihoods over the Global values brought to their lcm denominator, the prior's and the locals' likewise, so every weight is an int. The lookahead is written unnormalised already (`belief._split`, `_dot`, `_mass`: "mass(m) E_{m/mass(m)}[f]"), so it takes the measure as it is.

| records T | prior, normalised | prior, integer | `_play`, normalised | `_play`, integer | acts | final belief |
|---|---|---|---|---|---|---|
| 300 | 3.1 s | 1.0 s | 19.6 s | 6.3 s | equal | equal |
| 600 | 4.7 s | 1.0 s | 55.1 s | 14.6 s | equal | equal |

What remains in the integer run is `Fraction` arithmetic against the kernel rows and utilities, whose denominators are small; a lookahead whose rows and utilities are also brought to a common denominator per act would be integer throughout.

## What it means

- **Not a page question.** S13 is not asked to admit anything: Counts are sufficient, nothing is persisted, and the posterior's representation grows with T because it must — the page says so of a carried posterior, and the same holds of a computed one. The growth is linear in T and in the states, and that is the floor of exact arithmetic.
- **A kernel item, kit-neutral**: the lookahead over integer weights (a common denominator per episode, rows and utilities per act), and `posterior_global` normalising once. Acts and values identical; the structural, surface, counts and library suites see nothing. E6's operation counts are the same operations. A brief candidate (011), after 010.
- **Not measured here**: filtered arithmetic (float bounds with exact fallback on a near-tie) would cut the T-dependence further but performs different operations, so it is a question for E6 and the think kit before it is a kernel's.
- **Beside the point, noted**: declaring the 12 MB pack takes 196–218 s (`load_pack` + `declare`), once per plate.
