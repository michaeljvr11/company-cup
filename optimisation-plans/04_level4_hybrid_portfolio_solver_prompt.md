# Parallel Prompt: Implement Level 4 Hybrid Portfolio Solver

Use the shared context from `00_shared_context_prompt.md`.

We need the strongest possible Level 4 solver.

## Level 4 Constraints

Level 4 includes:

- fuel management
- weather
- tyre degradation
- finite tyre sets
- tyre reuse
- tyre blowouts
- pit stops
- tyre bonus
- fuel bonus
- time score

This is a mixed discrete-continuous optimisation problem.

## Goal

Implement a hybrid portfolio solver combining:

1. greedy stint planning
2. beam search over pit/tyre/fuel strategy
3. Pareto label-setting dynamic programming where practical
4. memetic/evolutionary strategy search
5. continuous speed refinement

The final candidate must be selected by simulator score.

## Candidate Representation

Create a high-level candidate representation:

```text
initial_tyre_id

for each lap:
  pit_enter
  tyre_change_set_id or null
  fuel_refuel_amount_l

for each straight occurrence:
  target_speed_multiplier
  corner_entry_speed_multiplier
```

Then convert this to submission JSON by:

1. computing safe corner speeds from tyre/weather/degradation state
2. computing target speeds
3. computing braking points analytically
4. repairing invalid actions
5. simulating

## Solver A: Greedy Stint Planner

Implement a fast seed generator:

1. Pick tyres based on weather forecast.
2. Estimate per-lap tyre degradation.
3. Pit before projected blowout.
4. Refuel only when needed.
5. Use near-max safe speeds.

Generate several variants:

```text
aggressive tyre usage
balanced tyre usage
conservative tyre usage
fuel-saving
max-pace
```

## Solver B: Beam Search

At each lap end, branch over:

```text
no pit
pit + refuel
pit + tyre change
pit + tyre change + refuel
```

Tyre change options:

```text
best available dry tyre
best available cold tyre
best available light-rain tyre
best available heavy-rain tyre
least-used tyre of each compound
current tyre if still viable
```

Refuel options:

```text
0
enough for next lap
enough for next 2 laps
enough to finish
fill to soft-cap-aware target
full tank
```

Beam widths:

```text
fast: 100
normal: 1000
deep: 5000 to 10000
```

Use configurable beam width.

## Solver C: Pareto Label-Setting

If feasible, maintain labels at segment/lap boundaries.

State:

```text
lap_index
segment_index
speed_bucket
fuel_bucket
current_tyre_id
current_tyre_degradation_bucket
time_bucket or exact time
```

Each label stores:

```text
time_so_far
fuel_used
fuel_remaining
current_speed
current_tyre_id
degradation_by_tyre_id
blowout_count
actions_so_far
```

Prune using epsilon domination:

```text
time_epsilon = 0.05 to 0.2 seconds
fuel_epsilon = 0.01 to 0.1 litres
degradation_epsilon = 0.0005 to 0.005
speed_bucket = 0.5 to 1.0 m/s
fuel_bucket = 0.1 to 0.5 litres
```

Label A dominates label B if A has:

```text
less or equal time
less or equal fuel used
greater or equal fuel remaining
less or equal blowouts
similar or better tyre degradation state
```

Use approximate domination if exact tyre-state domination is too strict.

## Solver D: Memetic / Evolutionary Search

Implement a deterministic evolutionary search seeded by:

```text
baseline solver
greedy stint planner
beam search candidates
DP candidates
```

Genome:

```text
initial_tyre_id
pit decisions per lap
tyre choice per pit
refuel amount per pit
target speed multipliers
corner entry speed multipliers
```

Mutation operators:

```text
add pit
remove pit
move pit one lap earlier/later
change tyre compound
change tyre set id
increase/decrease refuel amount
scale all speeds in a stint
scale one straight speed
make strategy more fuel-saving
make strategy more tyre-saving
```

Crossover:

```text
prefix laps from parent A, suffix laps from parent B
or
stint-level crossover
```

After every mutation/crossover:

1. repair candidate
2. simulate
3. score
4. keep if valid and useful

Use fixed seed.

Suggested config:

```text
population_size = 50 to 200
generations = 50 to 500
elite_count = 5 to 20
mutation_rate = 0.2 to 0.5
```

## Scalar Objective Sweeps

Generate candidates using multiple scalar proxies:

```text
objective =
  time
  + lambda_fuel * fuel_used
  - mu_tyre * total_tyre_degradation
  + blowout_penalty * blowouts
```

Sweep:

```text
lambda_fuel = [0, 0.1, 0.25, 0.5, 1, 2, 5]
mu_tyre = [0, 0.1, 0.25, 0.5, 1, 2]
blowout_penalty = very large
```

Do not intentionally allow blowouts unless simulator scoring proves it is
beneficial.

## Candidate Selection

The final solver should:

1. Generate candidates from all subsolvers.
2. Repair every candidate.
3. Simulate every candidate.
4. Sort by true simulator score.
5. Emit the best valid submission JSON.

## Deliverables

Implement:

```text
solve_level4_hybrid(level_json) -> submission_json
generate_level4_candidates(level_json) -> list[candidate]
```

Log:

```text
solver source
race_time
fuel_used
fuel_bonus
tyre_degradation_total
tyre_bonus
pit_count
tyre_sequence
blowouts
crashes
final_score
```

## Acceptance Criteria

The solver must:

- be deterministic
- manage finite tyre sets correctly
- avoid blowouts in selected candidate unless intentionally justified
- evaluate using simulator score
- beat or match baseline Level 4 solver
- support fast/normal/deep optimisation modes
