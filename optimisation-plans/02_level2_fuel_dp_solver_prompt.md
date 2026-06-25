# Parallel Prompt: Future Level 2 Fuel-Aware DP Solver

Use the shared context from `00_shared_context_prompt.md`.

Level 2 was previously handled inside `f1/strategy.py` by `_static_plan()` plus
`_repair_fuel()`. That baseline drove flat-out, simulated the strategy, and inserted
refuel-to-full pits before the first lap that would limp. Previous verified output:
score about 913,471, time about 10,398.3 s, fuel used about 312.6 L, 2 pits, no
crashes and no blowouts.

A first lap-level portfolio solver is now wired through `build_strategy(level, 2)`.
It keeps the flat-out speed plan, uses the tightest Level 1 dry safety factor, enumerates
two-stop pit schedules, computes the minimal refuel needed for each feasible schedule,
and selects by simulator score plus a `time_reference_s`-weighted proxy because the prior
leaderboard scores suggest time may be normalised differently. Current result: score
about 913,747, time about 10,367.6 s, fuel used about 312.6 L, 2 pits at laps 21 and
33, no crashes and no blowouts.

No segment-level DP, Lagrangian sweep, or public `solve_level2_fuel_dp()` API exists
yet. The current implementation is a lap-level candidate portfolio for two-stop
minimal-refuel schedules. Treat the DP content below as a future extension plan.

## Level 2 Constraints

Level 2 introduces:

- fuel consumption
- refuelling
- pit stops
- fuel soft cap scoring

Tyre degradation and weather complexity are not the main focus.

## Goal

If extending beyond the current implementation, implement a deterministic
resource-constrained solver for Level 2 using dynamic programming / label-setting
plus scalarised fuel-time sweeps.

## Main Idea

Generate a set of Pareto-efficient strategies that trade race time against fuel
usage, then score all candidates with the simulator and keep the best.

## State

Use a compact state at segment boundaries:

```text
lap_index
segment_index
entry_speed_bucket
fuel_remaining_bucket
```

Each label should store:

```text
time_so_far
fuel_used
fuel_remaining
current_speed
actions_so_far
pit_history
```

If implementation complexity is high, start with lap-level states and then refine
to segment-level states.

## Actions

For each straight, generate several target speed choices:

```text
car max speed
95% max speed
90% max speed
85% max speed
80% max speed
fuel-saving speed based on next corner
```

Also generate corner entry speed choices:

```text
100% safe speed
99.7% safe speed
99.5% safe speed
99.0% safe speed
```

At lap end, generate pit/refuel actions:

```text
no pit
pit with enough fuel for next lap
pit with enough fuel for next 2 laps
pit with fuel to reach end
pit with full tank
```

Clamp all refuel amounts to tank capacity.

## Pareto Pruning

At each state, prune dominated labels.

Label A dominates label B if:

```text
A.time_so_far <= B.time_so_far
A.fuel_used <= B.fuel_used
A.fuel_remaining >= B.fuel_remaining
```

and at least one is strictly better.

Use epsilon domination to control state explosion:

```text
time_epsilon = 0.05 to 0.2 seconds
fuel_epsilon = 0.01 to 0.1 litres
speed_bucket = 0.5 to 1.0 m/s
fuel_bucket = 0.1 to 0.5 litres
```

## Lagrangian Sweep

Run the DP several times using different scalar objectives:

```text
objective = time_so_far + lambda_fuel * fuel_used
```

Use this lambda grid:

```text
0.0
0.05
0.1
0.25
0.5
1.0
2.0
5.0
10.0
```

After each run, reconstruct the best candidate and evaluate it with the
simulator.

The simulator score, not the scalar objective, chooses the final answer.

## Candidate Generation

The solver should output many candidates, not just one.

For each lambda:

1. Run search.
2. Build submission JSON.
3. Repair candidate if needed.
4. Simulate.
5. Store candidate and score.

Finally select the highest score.

## Deliverables

Current public entry point:

```text
build_strategy(level, 2) -> Strategy
to_submission(strategy) -> submission_json
```

If adding DP helpers, either keep them private and wire them through
`build_strategy(level, 2)` or add public functions deliberately and update the CLI,
tests and shared context.

Add logs:

```text
lambda_fuel
race_time
fuel_used
fuel_soft_cap
score
pit_count
refuel_total
validity
```

## Acceptance Criteria

The solver must:

- be deterministic
- never select a candidate that runs out of fuel
- beat or match the current Level 2 score
- produce a portfolio of scored candidates
- use simulator score for final selection
