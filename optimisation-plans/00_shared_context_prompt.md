# Shared Context Prompt: Entelect Grand Prix Optimisation

You are helping us optimise an Entelect Grand Prix race strategy generator.

We already have:

- Baseline solvers for each level.
- A simulator that can replay a generated strategy and return time, fuel usage,
  tyre degradation, crashes, blowouts and score.
- Level JSON files containing car, race, track, tyre and weather data.

Your job is to improve our solver portfolio.

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

The car accelerates and brakes at constant rates. Weather can modify acceleration
and braking. The car starts at 0 m/s. After a pit stop, it exits at pit lane
speed.

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

Constants:

```text
K_base = 0.0005
K_drag = 0.0000000015
K_STRAIGHT = 0.0000166
K_BRAKING = 0.0398
K_CORNER = 0.000265
```

## Tyre Compounds

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

## Desired Solver Portfolio

We want multiple solvers, not one monolithic optimiser.

Recommended portfolio:

```text
Level 1:
  analytical optimal solver

Level 2:
  fuel-aware resource-constrained dynamic programming
  Lagrangian fuel/time sweep
  continuous speed refinement

Level 3:
  time-dependent weather-aware beam search / dynamic programming
  tyre strategy enumeration
  continuous speed refinement

Level 4:
  hybrid beam search over pit/tyre/fuel strategy
  Pareto label-setting dynamic programming
  memetic/evolutionary optimiser
  continuous speed refinement
```

## General Deliverables

When implementing a solver, provide:

1. Clean deterministic code.
2. Reusable candidate representation.
3. Conversion from candidate to submission JSON.
4. Validation through the simulator.
5. Candidate scoring and ranking.
6. Logs showing:
   - best score
   - race time
   - fuel used
   - tyre degradation
   - pit stops
   - crashes
   - blowouts
7. Unit tests or small integration tests where possible.

## Determinism

All solvers must be deterministic.

If randomness is used:

- Use a fixed seed.
- Log the seed.
- Make sure repeated runs on the same input produce the same output.

## Safety Margins

When computing corner entry speeds, support configurable safety factors:

```text
1.000
0.999
0.997
0.995
0.990
```

Use simulator validation to choose the fastest valid candidate.

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
