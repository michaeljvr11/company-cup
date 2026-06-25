# Parallel Prompt: Implement Portfolio Runner and Candidate Tournament

Use the shared context from `00_shared_context_prompt.md`.

We need a top-level portfolio runner that executes multiple solvers, simulates
their candidates and emits the best valid submission.

## Goal

Create a deterministic portfolio system that can run level-specific solvers and
choose the highest-scoring simulator-validated candidate.

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

Use this mapping:

```text
Level 1:
  analytical_level1

Level 2:
  analytical_baseline
  fuel_dp
  fuel_lagrangian_sweep
  continuous_refinement

Level 3:
  weather_greedy
  weather_beam
  fuel_lagrangian_sweep
  continuous_refinement

Level 4:
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

Implement a CLI similar to:

```bash
python run_portfolio.py --level 4 --input levels/level4.json --mode deep --output output.txt
```

or equivalent in the project language.

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
