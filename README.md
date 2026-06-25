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

## Status — all four levels tuned, clean (0 crashes, 0 blowouts), deterministic

| Level | Score | Notes |
|-------|------:|-------|
| L1 | ~201,934 | flat-out, late braking to the corner limit, Soft tyres |
| L2 | ~913,471 | + minimal refuel pits (fuel is ~distance-bound, so ≈ optimal) |
| L3 | ~859,196 | + per-lap weather-aware braking/corner speeds (Soft wins every L3 weather) |
| L4 | ~1,490,777 | + degradation: wear-balanced tyre stints across all 9 sets, weather-matched |

Generate every submission and see the score breakdown:

```bash
for n in 1 2 3 4; do python -m f1 levels/level$n.json output/level$n.txt --level $n; done
python tools/eval.py          # score breakdown per level (tuning harness)
python -m pytest              # 14 passing
```

Outputs are byte-identical across separate processes (required for submission validity).
See [docs/WORKPLAN.md](docs/WORKPLAN.md) for the optimisation approach, remaining ideas,
and **open questions to validate against the real leaderboard**.
