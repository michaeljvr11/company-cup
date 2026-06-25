# Parallel Prompt: Implement Level 1 Analytical Solver

Use the shared context from `00_shared_context_prompt.md`.

We need a high-quality Level 1 solver.

## Level 1 Constraints

Level 1 has:

- no fuel limitation
- no tyre degradation
- no weather complexity unless present in input, but treat default dry correctly
- no pit strategy required unless the existing framework requires pit fields
- objective is minimum race time with no crashes

This should be solved analytically, not with random search.

## Goal

Implement a deterministic Level 1 analytical solver that produces the fastest valid
strategy according to the simulator.

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
   - propagate constraints backwards if a straight is too short to brake enough

7. Generate:
   - `target_m/s` for every straight
   - `brake_start_m_before_next` for every straight
   - corner entries unchanged

8. Simulate every candidate and select the highest score.

## Backward Constraint Propagation

If a straight has length `L` and the required end speed is `v_end`, then the
maximum safe start speed if braking over the whole straight is:

```text
v_start_max = sqrt(v_end^2 + 2 * brake * L)
```

Use this to propagate speed constraints backwards around the lap.

Account for the fact that the race start speed is 0 m/s.

For multi-lap races, handle the speed carry-over from the final segment of one
lap to the first segment of the next lap unless simulator rules say otherwise.

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

## Safety Variants

Generate multiple candidates using corner safety factors:

```text
1.000
0.999
0.997
0.995
0.990
```

For each corner chain:

```text
effective_safe_speed = chain_safe_speed * safety_factor
```

Simulate all variants and choose the best valid candidate.

## Deliverables

Implement:

```text
solve_level1_analytical(level_json) -> submission_json
```

Also expose debug output:

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
- beat or match the current baseline Level 1 solver
- produce reproducible output from the same input
