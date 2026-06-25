# company-cup — Entelect Grand Prix race strategist

Python solver for the Entelect F1 hackathon: given a level file (car, track, tyres,
weather), produce an optimal race-strategy submission. Levels 1→4 add fuel, weather, and
tyre degradation in turn.

## Quick start

```bash
python -m f1 levels/level1.json output/level1.txt --level 1
python -m pytest        # or: python tests/test_smoke.py
```

Pure stdlib at runtime; `pytest` only for tests. Tested on Python 3.14.

## Where things are

| Doc | What |
|-----|------|
| [docs/PROBLEM.md](docs/PROBLEM.md) | What we're building, levels, scoring, submission format |
| [docs/PHYSICS.md](docs/PHYSICS.md) | All formulas + the simulator state machine (+ spec ambiguities) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Module map + the contracts that decouple the work |
| [docs/WORKPLAN.md](docs/WORKPLAN.md) | Parallel tracks for 2 people + agents, git workflow |

Code lives in `f1/`. The shared contracts (model, physics, scoring, output) are done;
the **simulator** (`f1/simulate.py`) and **optimiser** (`f1/strategy.py`) are the two
remaining tracks — see WORKPLAN.

## Status

- ✅ Scaffold, data model, physics, scoring, submission serialiser, CLI.
- ✅ Track A: race simulator (`f1/simulate.py`) — all-level physics, verified on L1.
- ✅ Track B: optimiser (`f1/strategy.py`) — **Level 1 fully optimised & verified**
  (flat-out, late braking to the corner limit, fastest start tyre; clean run, score ≈ 202k).
  Levels 2-4 produce valid crash-free strategies but their scoring is untuned pending
  real level files (see [docs/WORKPLAN.md](docs/WORKPLAN.md)).

Level 1: `python -m f1 levels/level1.json output/level1.txt --level 1` → 50 laps,
0 crashes, finishes on fuel, ~4952 s. `python -m pytest` → 7 passing.
