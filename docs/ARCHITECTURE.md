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
  simulate.py     Race simulator + per-set tyre wear. [DONE — all levels]
  strategy.py     Optimiser (static L1/L2; weather+wear-aware L3/L4). [DONE — tuned]
  cli.py          python -m f1 <level.json> [out] [--level N]. [DONE — wiring]
  __main__.py     module entry point.                [DONE]
levels/           level{1,2,3,4}.json.
output/           generated submission .txt files (gitignored).
tools/eval.py     score-breakdown harness for tuning.
tests/            test_smoke, test_simulate (L1 golden), test_levels (L1-4 clean + floors).
docs/             PROBLEM, PHYSICS, ARCHITECTURE, WORKPLAN.
```

All modules are implemented and all four levels are tuned: clean (0 crashes, 0 blowouts),
deterministic, scoring ~3.47M total. The shared/`contract` modules are frozen — extend,
don't reshape. The simulator tracks per-set tyre wear (spec: sets retain wear across
swaps). See WORKPLAN.md for the per-level approach and the open questions to validate
against the real leaderboard.

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
