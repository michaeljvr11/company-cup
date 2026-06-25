# Parallel Prompt: Future Continuous Speed Refinement

Use the shared context from `00_shared_context_prompt.md`.

There is no continuous speed-refinement module in the current codebase. Current
speed planning is analytical and lives in `f1/strategy.py`: `_speed_plan()` for
Level 1/2 and `_assemble()` inside `_weather_plan()` for Level 3/4. The code uses
fixed target max speed and computes braking points; it does not optimise raw speed
multipliers with coordinate search, SciPy or CMA-ES.

Treat this document as a future extension plan.

## Goal

If adding refinement, given a candidate with fixed:

```text
initial tyre
pit laps
tyre changes
refuel amounts
```

optimise:

```text
target speeds on straights
corner entry speed multipliers
possibly stint-level speed multipliers
```

to improve simulator score.

## Optimisation Variables

Use compact variables rather than every raw JSON field.

Recommended variables:

```text
target_speed_multiplier_per_straight_occurrence
corner_entry_multiplier_per_corner_chain_occurrence
optional_global_pace_multiplier
optional_stint_pace_multiplier
```

Bounds:

```text
target_speed_multiplier: 0.70 to 1.00
corner_entry_multiplier: 0.95 to 1.00
global_pace_multiplier: 0.80 to 1.00
stint_pace_multiplier: 0.80 to 1.00
```

The repair layer converts these variables into actual target speeds and braking
points.

## Objective

Maximise simulator score.

If the optimiser minimises, use:

```text
objective = -simulator_score + penalties
```

Penalties:

```text
crash_count * large_penalty
blowout_count * large_penalty
fuel_runout * large_penalty
invalid_json * huge_penalty
```

## Optimisers to Support

Implement at least two deterministic methods:

### 1. Coordinate Search

Simple, robust and deterministic.

For each variable:

1. try increasing by step
2. try decreasing by step
3. keep improvement
4. reduce step size
5. repeat

Suggested steps:

```text
0.05
0.02
0.01
0.005
0.002
0.001
```

### 2. Powell / Nelder-Mead / COBYLA / SLSQP

If using Python SciPy, support:

```text
Powell
COBYLA
SLSQP
```

If SciPy is not available, coordinate search is acceptable.

### 3. CMA-ES Optional

If available, implement deterministic CMA-ES with a fixed seed.

Use only for Level 3 and Level 4 deep mode.

## Candidate Selection

For each input candidate:

1. evaluate original candidate
2. run continuous refinement
3. repair each refined candidate
4. simulate
5. keep the best

## Deliverables

Potential future API:

```text
refine_candidate_speeds(level_json, candidate, mode) -> refined_candidate
```

If this is added, wire it through `build_strategy()` or a portfolio runner and make
sure the refined candidate is never selected without simulator validation.

Modes:

```text
fast
normal
deep
```

Suggested budgets:

```text
fast:   50 simulator calls
normal: 300 simulator calls
deep:   1000+ simulator calls
```

## Logging

Log:

```text
initial score
best score
number of simulator calls
optimiser used
best variables
crashes
blowouts
fuel used
race time
```

## Acceptance Criteria

The continuous optimiser must:

- be deterministic
- never return a candidate worse than input unless explicitly requested
- integrate with repair layer
- work for Level 2, Level 3 and Level 4
- improve at least some baseline candidates in tests
