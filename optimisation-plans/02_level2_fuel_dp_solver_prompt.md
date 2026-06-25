# Parallel Prompt: Implement Level 2 Fuel-Aware DP Solver

Use the shared context from `00_shared_context_prompt.md`.

We need a strong Level 2 solver that optimises the trade-off between race time
and fuel usage.

## Level 2 Constraints

Level 2 introduces:

- fuel consumption
- refuelling
- pit stops
- fuel soft cap scoring

Tyre degradation and weather complexity are not the main focus.

## Goal

Implement a deterministic resource-constrained solver for Level 2 using dynamic
programming / label-setting plus scalarised fuel-time sweeps.

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

Implement:

```text
solve_level2_fuel_dp(level_json) -> submission_json
generate_level2_candidates(level_json) -> list[candidate]
```

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
- beat or match the baseline Level 2 solver
- produce a portfolio of scored candidates
- use simulator score for final selection
