# Parallel Prompt: Future Level 3 Weather-Aware Search Solver

Use the shared context from `00_shared_context_prompt.md`.

Level 3 is currently handled inside `f1/strategy.py` by `_weather_plan()` plus
`_repair_fuel()`. It iterates simulate -> sample per-lap weather/deceleration ->
reassemble per-lap braking points until stable. Tyre degradation is not active in
Level 3. For the current level data, the schedule uses Soft for the whole race.

Current verified output is clean and deterministic: score about 859,196, time
about 21,912.8 s, fuel used about 529.8 L, 3 pits, no crashes and no blowouts.
No beam search, candidate portfolio, or public `solve_level3_weather_beam()` API
exists yet. Treat the beam-search details below as a future extension plan.

## Level 3 Constraints

Level 3 introduces:

- weather conditions
- weather-dependent acceleration
- weather-dependent braking
- weather-dependent tyre friction
- weather-dependent tyre degradation rates in the data, but degradation is not
  applied by `features(3)`
- tyre changes at pit stops
- fuel management remains relevant

The hard part is that weather depends on race time, and race time depends on the
strategy.

## Goal

If extending beyond the current implementation, implement a deterministic
time-dependent beam search / dynamic programming solver that explores tyre, pit
and fuel strategies under changing weather.

## Weather Handling

Reuse the existing model helper:

```text
Level.active_condition(time_s) -> WeatherCondition | None
Level.weather_at(time_s) -> condition name
```

Weather conditions cycle if the race exceeds the total weather schedule duration.

Be careful about whether the simulator applies weather changes:

```text
at segment start only
mid-segment
at segment end
```

Match the simulator.

## State / Label

Use labels containing:

```text
lap_index
segment_index
time_so_far
current_speed
fuel_remaining
fuel_used
current_tyre_id
current_tyre_compound
actions_so_far
pit_history
```

If tyre degradation is not active in Level 3, ignore degradation for pruning but
still preserve tyre identity for output.

## Beam Search

At each segment or lap boundary, expand candidate labels.

Recommended beam widths:

```text
fast: 100
normal: 1000
deep: 5000+
```

Keep beam width configurable.

## Segment Actions

For each straight, generate target speed choices based on:

```text
car max speed under current conditions
95% max speed
90% max speed
85% max speed
fuel-saving speed
speed needed for next corner chain
```

For corner entry, use:

```text
100% safe speed
99.7% safe speed
99.5% safe speed
99.0% safe speed
```

## Pit Actions

At the end of each lap, branch into:

```text
no pit
pit + tyre change only
pit + refuel only
pit + tyre change + refuel
```

For tyre changes, do not try every tyre set blindly if there are many. Prefer
candidate tyres based on current and upcoming weather:

```text
dry/cold: Soft, Medium, Hard
light rain: Intermediate, Wet, Soft as fallback
heavy rain: Wet, Intermediate
```

Still allow at least one candidate from each available compound so the search can
discover unusual strategies.

For refuel amounts, use discrete options:

```text
0
enough for next lap
enough for next 2 laps
enough to finish
full tank
```

## Ranking Heuristic

Rank partial labels by estimated final potential.

Suggested heuristic:

```text
estimated_score_proxy =
  -time_so_far
  -projected_remaining_time
  +fuel_bonus_estimate
  -pit_loss_estimate
```

Alternatively minimise:

```text
objective =
  time_so_far
  + lambda_fuel * fuel_used
  + estimated_remaining_time
```

Run several `lambda_fuel` values:

```text
0.0
0.1
0.25
0.5
1.0
2.0
5.0
```

## Weather-Aware Tyre Heuristic

Use this only for candidate ordering, not as a hard rule:

```text
dry:        Soft > Medium > Hard > Intermediate > Wet
cold:       Soft > Intermediate > Medium > Hard > Wet
light rain: Intermediate > Wet > Soft > Medium > Hard
heavy rain: Wet > Intermediate > Soft > Medium > Hard
```

## Deliverables

Current public entry point:

```text
build_strategy(level, 3) -> Strategy
to_submission(strategy) -> submission_json
```

If adding search helpers, either keep them private and wire them through
`build_strategy(level, 3)` or add public functions deliberately and update the CLI,
tests and shared context.

Log:

```text
beam_width
lambda_fuel
tyre sequence
pit laps
refuel amounts
weather encountered
race_time
fuel_used
score
crashes
blowouts
```

## Acceptance Criteria

The solver must:

- be deterministic
- correctly handle cyclic weather
- produce valid strategy JSON
- evaluate candidates using the simulator
- beat or match the current Level 3 score
- expose beam width and lambda sweep configuration
