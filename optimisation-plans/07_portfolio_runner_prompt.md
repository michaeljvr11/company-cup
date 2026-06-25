# Parallel Prompt: Future Portfolio Runner and Candidate Tournament

Use the shared context from `00_shared_context_prompt.md`.

There is no portfolio runner in the current codebase. The current CLI path is:

```text
python3 -m f1 levels/levelN.json output/levelN.txt --level N
```

which calls `build_strategy()` once for the requested level. `tools/eval.py` is a
score-breakdown harness for the current built-in solver, not a candidate tournament.

Treat this document as a future extension plan.

## Goal

Create a deterministic, level-scoped portfolio system. Every level should have a
portfolio of candidate generators, with the portfolio size matching the level's
complexity. The runner simulates all generated candidates and chooses the
highest-scoring simulator-validated submission.

## Inputs

```text
level_json_path
level_number
mode
output_path
```

Modes:

```text
fast
normal
deep
```

## Solver Portfolio

The current mapping is simply:

```text
Level 1: build_strategy(level, 1)
Level 2: build_strategy(level, 2)
Level 3: build_strategy(level, 3)
Level 4: build_strategy(level, 4)
```

Target future portfolio mapping:

```text
Level 1:
  analytical_baseline
  tyre_and_safety_margin_sweep
  braking_refinement

Level 2:
  current_lap_level_minimal_refuel_portfolio
  analytical_baseline
  fuel_dp
  fuel_lagrangian_sweep
  continuous_refinement

Level 3:
  current_iterative_weather_baseline
  weather_greedy
  weather_beam
  fuel_lagrangian_sweep
  continuous_refinement

Level 4:
  current_wear_balanced_baseline
  greedy_stint
  beam_strategy
  pareto_dp_if_available
  memetic
  continuous_refinement
```

## Runner Flow

1. Load level JSON.
2. Detect level capabilities:
   - fuel present?
   - weather present?
   - tyre degradation active?
   - available tyre sets?
3. Run appropriate solvers for selected mode.
4. Collect all candidates.
5. Deduplicate candidates.
6. Repair candidates.
7. Simulate candidates.
8. Sort by true simulator score.
9. Emit best valid submission JSON.
10. Write detailed report.

## Candidate Metadata

Each candidate should carry metadata:

```text
source_solver
source_config
random_seed if any
safety_factor
lambda_fuel
mu_tyre
beam_width
refinement_budget
```

## Deduplication

Deduplicate by canonical JSON or candidate hash.

Canonicalise:

```text
initial_tyre_id
pit sequence
tyre sequence
rounded refuel amounts
rounded target speeds
rounded brake points
```

## Tournament Selection

Reject candidates with:

```text
invalid JSON
fuel runout
unrepaired blowout
unacceptable crash count
simulator error
```

Then sort by:

```text
final_score descending
race_time ascending
fuel_used according to level scoring
tyre_bonus according to level scoring
```

The simulator's final score is the primary criterion.

## Report

Write a report file containing:

```text
level name
mode
number of candidates generated
number of candidates simulated
number of invalid candidates
best score
best race time
best fuel used
best tyre degradation
best pit strategy
best tyre sequence
top 20 candidates table
```

## CLI

Potential future CLI:

```bash
python run_portfolio.py --level 4 --input levels/level4.json --mode deep --output output.txt
```

or equivalent in the current `python3 -m f1 ...` CLI.

## Determinism

The same command on the same input must produce the same output.

If some solvers use randomness:

```text
use fixed seeds
run seeds in fixed order
sort candidates deterministically
avoid nondeterministic parallel reduction
```

Parallel execution is allowed, but final sorting and tie-breaking must be stable.

## Acceptance Criteria

The portfolio runner must:

- run all available solvers for a level
- evaluate candidates with the simulator
- choose the highest simulator score
- output valid submission JSON
- produce a detailed report
- be deterministic
