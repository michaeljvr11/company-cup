# Architecture

Flat, minimal, deterministic. One package `f1/`, pure-stdlib at runtime (pytest only
for tests). The design exists to make two people + agents work in parallel without
inventing conflicting contracts.

## Module map

```
f1/
  model.py        Level data model + JSON loader.   [DONE — shared contract]
  constants.py    Physics constants.                [DONE]
  physics.py      Pure formulas (friction, kinematics, fuel, wear). [DONE — shared]
  score.py        Scoring formulas per level.        [DONE]
  strategy_io.py  Strategy dataclasses + submission .txt serialiser. [DONE — shared contract]
  simulate.py     Race simulator state machine.      [DONE — all levels]
  strategy.py     Per-level optimiser.               [DONE — L1 optimised+verified; L2-4 safe baseline]
  cli.py          python -m f1 <level.json> [out] [--level N]. [DONE — wiring]
  __main__.py     module entry point.                [DONE]
levels/           level JSONs (level1.json provided; level2-4 land here).
output/           generated submission .txt files (gitignored).
tests/            test_smoke.py [DONE], test_simulate.py [grows with Track A].
docs/             PROBLEM, PHYSICS, ARCHITECTURE, WORKPLAN.
```

All modules are implemented. The shared/`contract` ones are frozen — extend, don't
reshape. Level 1 is fully optimised and verified against the simulator; levels 2-4
produce valid, crash-free, race-finishing strategies but their scoring (fuel-bonus
targeting, weather tyre windows, per-stint corner re-planning) is untuned until real
level files land — see WORKPLAN.md "Remaining".

## The two contracts that decouple everything

**1. Simulator** — `simulate(level: Level, strategy: Strategy) -> Result`
(`Result` / `SegmentResult` dataclasses in `simulate.py`). The optimiser and tests
code against `Result`; add fields rather than rename. This is the oracle: it turns any
strategy into time/fuel/wear/score.

**2. Strategy** — the `Strategy` dataclass (`strategy_io.py`) and its `.txt`
serialisation. The optimiser produces a `Strategy`; the simulator consumes it; the CLI
writes it. Matches the submission schema exactly.

Because both stub modules only touch these frozen contracts, Track A can build the
simulator against the existing baseline strategy while Track B builds smarter strategies
against the (eventually real) simulator. Until the simulator exists, Track B validates
shape via `to_submission` + hand-checked numbers.

## Data flow

```
level.json --load_level--> Level ---------\
                                            >-- build_strategy --> Strategy --write_submission--> output/*.txt
level_num ----------------------------------/                          |
                                                                       v
                                              simulate(Level, Strategy) --> Result --> final_score
```

## Conventions

- **Deterministic**: no unseeded randomness in `strategy.py`. If you need search/random
  restarts, seed a `random.Random(fixed_seed)`.
- **Pure stdlib at runtime.** `pytest` is the only dev dependency. Don't add libraries
  without a line in WORKPLAN saying why (per CLAUDE.md).
- **No new layers.** Resist controllers/services/repositories. Add a function before a
  module, a module before a package.
- Keep `physics.py` stateless; keep race/lap state inside `simulate.py`.
- New levels: drop `levels/levelN.json`, implement that branch in `build_strategy`.

## Running

```
python -m f1 levels/level1.json output/level1.txt --level 1
python -m pytest            # or: python tests/test_smoke.py
```
