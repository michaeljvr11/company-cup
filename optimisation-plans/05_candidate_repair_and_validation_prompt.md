# Parallel Prompt: Future Candidate Repair and Validation Layer

Use the shared context from `00_shared_context_prompt.md`.

There is no shared candidate repair or validation module in the current codebase.
The only repair helper is `_repair_fuel()` inside `f1/strategy.py`, and speed / tyre
safety are built directly into `_speed_plan()`, `_weather_plan()`, `_assemble()` and
`_tyre_schedule_l4()`. Validation currently means calling `simulate()` and scoring
with `score.py` / `tools/eval.py`.

Treat this document as a future extension plan, not a description of existing APIs.

## Goal

If adding a broader search portfolio, implement a deterministic candidate repair
system that takes a high-level candidate and converts it into a valid,
simulator-ready `Strategy` / submission JSON.

This repair layer should make optimisation easier by allowing solvers to produce
imperfect candidates.

## Input

A high-level candidate may contain:

```text
initial_tyre_id
pit decisions
tyre changes
refuel amounts
target speed multipliers
corner entry speed multipliers
```

It may be partially invalid.

## Output

A valid submission JSON with:

```text
initial_tyre_id
laps
segments
pit objects
```

## Required Repairs

### 1. Speed Clamping

Clamp target speeds:

```text
crawl_speed <= target_speed <= car_max_speed
```

If target speed is lower than entry speed, remember that the car will follow
through at entry speed until braking.

### 2. Corner Safety

For every upcoming corner or consecutive corner chain:

1. compute current tyre friction
2. compute max safe corner speed
3. multiply by safety factor
4. ensure corner entry speed does not exceed this limit

Support safety factors:

```text
1.000
0.999
0.997
0.995
0.990
```

### 3. Braking Point Calculation

For every straight:

1. determine the desired end speed before next corner chain
2. determine the highest speed reached before braking
3. compute braking distance

```text
d_brake = (v_before_brake^2 - v_end^2) / (2 * brake)
```

Clamp to straight length.

If braking distance exceeds straight length:

```text
reduce target speed
or reduce straight entry speed if possible
or propagate speed constraint backwards
```

### 4. Pit and Fuel Repair

If simulator predicts fuel will run out:

1. first try adding refuel at existing earlier pit
2. then try increasing refuel at previous pit
3. then try adding a pit at previous lap end
4. if still impossible, reduce speeds

Clamp fuel to tank capacity.

### 5. Tyre Repair

If simulator predicts tyre blowout:

1. try changing tyres at an existing earlier pit
2. try adding a pit before the blowout lap
3. try choosing a harder or more weather-appropriate tyre
4. try lowering corner speeds to reduce tyre degradation

Respect available tyre set IDs and finite tyre reuse rules.

### 6. Weather-Aware Recalculation

Because weather depends on time, repair may change time and therefore weather.
After repair:

1. resimulate
2. recompute affected speeds
3. repeat until stable or max iterations reached

Use a configurable max repair iteration count, e.g.:

```text
max_repair_iterations = 5
```

## Validation

Potential future API:

```text
validate_submission(level_json, submission_json) -> validation_result
```

Validation result should include:

```text
is_valid
crash_count
blowout_count
fuel_runout
invalid_fields
race_time
score
diagnostics
```

## Repair API

Potential future repair API:

```text
repair_candidate(level_json, candidate, safety_factor) -> submission_json
```

Also implement:

```text
candidate_to_submission(level_json, candidate) -> submission_json
```

and:

```text
simulate_and_score(level_json, submission_json) -> score_result
```

If these are added, wire them into `build_strategy()`, `tools/eval.py`, or a new CLI
path, and update `00_shared_context_prompt.md` so the API list stays accurate.

## Acceptance Criteria

The repair layer must:

- be deterministic
- produce syntactically valid JSON
- avoid unsafe corner speeds when possible
- recompute braking points analytically
- interact cleanly with the simulator
- be reusable by all level solvers
