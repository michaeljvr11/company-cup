# Shared Context Prompt: Entelect Grand Prix Optimisation

You are helping us optimise an Entelect Grand Prix race strategy generator.

We currently have:

- `f1/model.py`: level JSON loader for `levels/level1.json` through
  `levels/level4.json`.
- `f1/simulate.py`: simulator that replays a `Strategy` and returns time, fuel
  usage, tyre degradation, crashes and blowouts.
- `f1/score.py`: scoring formulas.
- `f1/strategy.py`: the deterministic solver entry point,
  `build_strategy(level, level_num)`.
- `f1/strategy_io.py`: strategy dataclasses and submission JSON serialisation.
- `tools/eval.py`: live score breakdown for all levels.

There are no separate public `solve_level*_...` APIs, no shared candidate repair
module, no portfolio runner, and no continuous refinement module yet. Future
optimisers should either preserve the existing `build_strategy()` entry point or
intentionally add new APIs and wire them through the CLI/tests.

Current verified simulator scores from `python3 tools/eval.py`:

```text
L1  202,038   0 crashes, 0 blowouts, 0 pits
L2  913,747   0 crashes, 0 blowouts, 2 pits
L3  859,196   0 crashes, 0 blowouts, 3 pits
L4 1,490,777  0 crashes, 0 blowouts, 14 pits / 8 tyre changes
Grand total: 3,465,758
```

Prior-session external scores to beat / reconcile:

```text
L1 1,601,646
L2 2,108,044
L3 1,437,072
L4 1,135,340
```

These targets do not match the current local PDF score formula. The local solver
already beats the L4 target under `tools/eval.py`, but is far below the L1-L3
targets. Keep this as evidence that the official leaderboard may use
`time_reference_s` or another hidden normalisation, but do not change `f1/score.py`
until we have the exact submitted strategy telemetry and official score for the
same run.

Project end state: build a portfolio of solver candidates for every level, then
simulate and score those candidates and emit the best deterministic submission.
The portfolio should be level-appropriate: Level 1 can be a small analytical
portfolio, while Level 4 should be broad enough to include multiple discrete and
continuous search styles.

Your job is to evolve the current single-entry solver toward that portfolio
without breaking deterministic, clean submissions.

## Problem Summary

A race strategy JSON must specify:

- `initial_tyre_id`
- For every lap:
  - For every straight:
    - `target_m/s`
    - `brake_start_m_before_next`
  - For every corner:
    - no speed action, but corner entry speed must be safe
  - Optional pit stop:
    - `enter`
    - `tyre_change_set_id`
    - `fuel_refuel_amount_l`

The car accelerates and brakes at constant rates. Weather modifies acceleration
and braking through the active condition's multipliers. The car starts at 0 m/s.
After a pit stop, it exits at pit lane speed.

The objective is to maximise final score, which depends mainly on race time, fuel
usage and, in Level 4, tyre degradation.

## Important Physics

For a straight:

- The car accelerates until target speed is reached.
- It then holds target speed.
- From `brake_start_m_before_next`, it brakes until the end of the straight.
- If the target speed is below entry speed, speed follows through and does not
  slow down until braking.

Braking distance from speed `v0` to speed `v1`:

```text
d = (v0^2 - v1^2) / (2 * brake)
```

Acceleration distance from speed `v0` to speed `v1`:

```text
d = (v1^2 - v0^2) / (2 * accel)
```

Corner speed limit:

```text
max_corner_speed = sqrt(tyre_friction * gravity * radius)
```

Tyre friction:

```text
tyre_friction =
  (base_friction_coefficient - total_degradation) * weather_multiplier
```

Fuel usage:

```text
fuel_used =
  (K_base + K_drag * ((initial_speed + final_speed) / 2)^2) * distance
```

Constants and code source of truth:

```text
K_base = car.fuel_consumption from the level JSON
K_FUEL_BASE = 0.0005      # documented fallback/default
K_FUEL_DRAG = 0.0000000015
K_STRAIGHT = 0.0000166
K_BRAKING = 0.0398
K_CORNER = 0.000265
```

Current simulator behaviour:

- Weather is sampled once at segment start from elapsed race time.
- Weather schedules cycle in list order from `starting_weather_condition_id`.
- Effective straight acceleration/braking are `car.accel * acceleration_multiplier`
  and `car.brake * deceleration_multiplier`.
- Tyre degradation is applied only when `features(level_num)["apply_degradation"]`
  is true, which currently means level 4 and above.
- Crash check is strict: a corner crashes when entry speed is greater than the
  computed max corner speed.
- Crash mode adds the corner penalty, adds 0.1 degradation in level 4, uses crawl
  speed through consecutive corners, and clears on the next straight.
- Fuel-out or tyre blowout enters limp mode at segment granularity until a pit.
- Pit stops happen only at lap end, cap refuel to tank capacity, clear limp/crawl,
  and exit at pit lane speed.
- Tyre set wear is retained by tyre set id across swaps.

## Tyre Compounds

`f1/constants.py` contains canonical fallback base friction values. The level JSON
can override them, and `load_level()` prefers the JSON value when present. In the
current level files, level 4 overrides Wet base friction to 1.6.

Base friction:

```text
Soft:         1.8
Medium:       1.7
Hard:         1.6
Intermediate: 1.2
Wet:          1.1
```

Weather friction multipliers:

```text
Dry:
  Soft 1.18, Medium 1.08, Hard 0.98, Intermediate 0.90, Wet 0.72

Cold:
  Soft 1.00, Medium 0.97, Hard 0.92, Intermediate 0.96, Wet 0.88

Light Rain:
  Soft 0.92, Medium 0.88, Hard 0.82, Intermediate 1.08, Wet 1.02

Heavy Rain:
  Soft 0.80, Medium 0.74, Hard 0.68, Intermediate 1.02, Wet 1.20
```

Degradation rates:

```text
Dry:
  Soft 0.14, Medium 0.10, Hard 0.07, Intermediate 0.11, Wet 0.16

Cold:
  Soft 0.11, Medium 0.08, Hard 0.06, Intermediate 0.09, Wet 0.12

Light Rain:
  Soft 0.12, Medium 0.09, Hard 0.07, Intermediate 0.08, Wet 0.09

Heavy Rain:
  Soft 0.13, Medium 0.10, Hard 0.08, Intermediate 0.09, Wet 0.05
```

## Optimisation Philosophy

Do not optimise raw JSON blindly.

Instead:

1. Represent a strategy in a compact high-level form:
   - tyre choices
   - pit decisions
   - refuel amounts
   - target speed multipliers
   - desired corner entry speed multipliers

2. Derive low-level JSON fields analytically:
   - compute safe corner speeds
   - compute braking distances
   - compute `brake_start_m_before_next`

3. Repair unsafe or infeasible plans:
   - clamp target speeds
   - reduce speed before corners
   - add refuel if needed
   - add tyre change if blowout is likely
   - recompute braking points

4. Always evaluate candidates using the existing simulator.

The simulator is the source of truth.

## Current Solver Entry Point

The current implementation is not yet a full multi-solver portfolio. It has one
public level-dispatched entry point in `f1/strategy.py`:

```text
Level 1:
  `_static_plan`: try the first id from each available tyre set and sweep dry
  safety factors, generate a flat-out plan, brake analytically for each upcoming
  corner chain, simulate, and choose the clean fastest candidate.

Level 2:
  `_level2_fuel_portfolio_plan`: flat-out dry speed plan on the best dry tyre,
  use the tightest Level 1 dry safety factor, enumerate feasible two-stop pit
  schedules, compute minimal refuel amounts from simulated lap fuel burn, and
  select the best clean candidate using simulator score plus a
  `time_reference_s`-weighted time proxy.

Level 3:
  `_weather_plan`: iterate simulate -> sample per-lap weather/deceleration ->
  reassemble per-lap braking points. Tyre schedule is currently one best tyre
  for the race; for current level 3 data this is Soft.

Level 4:
  `_weather_plan` with degradation enabled. `_tyre_schedule_l4` balances wear
  across all available tyre sets, chooses set ids by stint weather, and plans
  with degradation margins to avoid crashes/blowouts.
```

## Target Solver Portfolio

The intended target is a portfolio for each level. Future improvement ideas, not
currently implemented:

```text
Level 1:
  analytical baseline variants
  tyre and safety-margin sweep
  braking-point refinement / validation pass

Level 2:
  current flat-out + lap-level minimal-refuel pit portfolio
  fuel-aware resource-constrained dynamic programming
  Lagrangian fuel/time sweep
  continuous speed refinement

Level 3:
  current iterative weather baseline
  time-dependent weather-aware beam search / dynamic programming
  tyre strategy enumeration
  continuous speed refinement

Level 4:
  current wear-balanced weather baseline
  hybrid beam search over pit/tyre/fuel strategy
  Pareto label-setting dynamic programming
  memetic/evolutionary optimiser
  continuous speed refinement
```

## Current Extension Contracts

When implementing or improving a solver, preserve or update these contracts:

1. `build_strategy(level: Level, level_num: int) -> Strategy` remains the CLI path
   unless you intentionally replace and wire it.
2. Submission output goes through `Strategy` and `to_submission()` /
   `write_submission()`.
3. Simulator validation uses `simulate(level, strategy, **features(level_num))`.
4. Score calculation uses `final_score()` or the same components as `tools/eval.py`.
5. Any new search must be deterministic and should log enough to compare:
   - best score
   - race time
   - fuel used
   - tyre degradation
   - pit stops
   - crashes
   - blowouts
6. Add or update tests where possible. Existing coverage includes `tests/test_smoke.py`,
   `tests/test_simulate.py`, and `tests/test_levels.py`.

## Determinism

All solvers must be deterministic.

If randomness is used:

- Use a fixed seed.
- Log the seed.
- Make sure repeated runs on the same input produce the same output.

## Safety Margins

Current safety constants in `f1/strategy.py`:

```text
CORNER_SAFETY_STATIC = 0.999  # L1/L2
CORNER_SAFETY = 0.985         # L3/L4
DEG_MARGIN = 1.15             # L4 degradation planning
```

Future solvers may sweep additional safety factors, but the current code does not
expose that as a public configuration. Always use simulator validation to choose
the fastest valid candidate.

## Key Implementation Warning

There may be small differences between the written rules and simulator behaviour.

Always check:

- weather timing
- whether weather can change mid-segment
- whether degradation is applied before or after a segment
- exact crash comparison
- exact fuel depletion behaviour
- limp/crawl handling
- pit stop timing
- tyre reuse handling

Optimise against the simulator, not only the PDF.
