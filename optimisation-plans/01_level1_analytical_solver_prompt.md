# Parallel Prompt: Improve Level 1 Analytical Solver

Use the shared context from `00_shared_context_prompt.md`.

Level 1 is already implemented in `f1/strategy.py` through:

```text
build_strategy(level, 1)
   -> _static_plan(level, 1)
   -> _speed_plan(...)
   -> _optimal_brake_start(...)
```

Current verified output is clean and deterministic: score about 201,934, time
about 4,952.1 s, start tyre 1 / Soft, no pits, no crashes and no blowouts.
There is no public `solve_level1_analytical()` function.

Use this prompt for validating or improving the current Level 1 solver.

## Level 1 Constraints

Level 1 has:

- no fuel limitation
- no tyre degradation
- no weather complexity unless present in input, but treat default dry correctly
- no pit strategy required unless the existing framework requires pit fields
- objective is minimum race time with no crashes

This should be solved analytically, not with random search.

## Goal

Improve or verify the deterministic Level 1 analytical solver so it produces the
fastest valid strategy according to the simulator.

## Algorithm

For each available initial tyre set:

1. Determine tyre compound.
2. Compute friction in current weather.
3. Compute max safe speed for every corner.
4. Group consecutive corners into corner chains.
5. For each chain, compute the chain safe speed:

```text
chain_safe_speed = min(max_safe_speed of all corners in chain)
```

6. Compute the fastest feasible speed profile:
   - accelerate as hard as possible on straights
   - target car max speed where possible
   - brake as late as possible
   - enter each corner chain at or below safe speed
   - if adding new logic, handle any too-short straight case explicitly

7. Generate:
   - `target_m/s` for every straight
   - `brake_start_m_before_next` for every straight
   - corner entries unchanged

8. Simulate every candidate and select the fastest clean strategy. For Level 1,
   this is equivalent to selecting the highest score.

## Current Brake Planning

The current code does not implement a general backward propagation pass. Instead,
`_optimal_brake_start()` solves the latest brake point for a straight, using the
current entry speed and the required safe speed for the next corner chain. `_speed_plan()`
runs a two-lap forward pass and records the second pass braking points to account
for multi-lap carry-over.

If a future track contains a straight that is too short to brake from the entry
speed to the required end speed, add explicit constraint propagation. The useful
formula is:

```text
v_start_max = sqrt(v_end^2 + 2 * brake * L)
```

## Brake Point Calculation

Given:

```text
v_brake_start
v_required_end
brake
```

compute:

```text
braking_distance =
  max(0, (v_brake_start^2 - v_required_end^2) / (2 * brake))
```

Then:

```text
brake_start_m_before_next = braking_distance
```

Clamp to:

```text
0 <= brake_start_m_before_next <= straight_length
```

If braking distance exceeds straight length, reduce target/entry speed and
recompute.

## Safety Margin

The current Level 1/2 code uses one fixed margin:

```text
CORNER_SAFETY_STATIC = 0.999
```

Future tuning may generate multiple candidates using additional safety factors,
but that sweep is not implemented yet. If added, compute:

```text
effective_safe_speed = chain_safe_speed * safety_factor
```

Simulate all variants and choose the best valid candidate.

## Deliverables

Use the current public entry point:

```text
build_strategy(level, 1) -> Strategy
to_submission(strategy) -> submission_json
```

If adding a dedicated Level 1 helper, wire it through `build_strategy()` and expose
debug output through the CLI or `tools/eval.py` rather than leaving an unused API.
Useful debug output:

```text
candidate tyre
safety factor
simulated time
score
number of crashes
```

## Acceptance Criteria

The solver must:

- be deterministic
- produce valid JSON
- avoid crashes in the best selected strategy
- beat or match the current Level 1 score/time
- produce reproducible output from the same input
