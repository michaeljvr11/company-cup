# Physics & Simulation Spec

Everything needed to implement `f1/simulate.py` correctly. The pure formulas already
live in `f1/physics.py` — this doc is the **state machine** that composes them into a
full race, plus the constants and the spec ambiguities you must watch.

> All units SI (metres, seconds). Gravity `g = 9.8` (matches the page-8 worked example).

## Constants (`f1/constants.py`)

| Name | Value | Use |
|------|-------|-----|
| `g` | 9.8 | corner max speed |
| `K_STRAIGHT` | 0.0000166 | straight tyre wear |
| `K_BRAKING` | 0.0398 | braking tyre wear |
| `K_CORNER` | 0.000265 | corner tyre wear |
| `K_FUEL_BASE` | 0.0005 | fuel (also `car.fuel_consumption` in JSON — prefer JSON) |
| `K_FUEL_DRAG` | 0.0000000015 | fuel, speed term |

## Core formulas (all in `f1/physics.py`)

**Tyre friction** (page 6):
```
tyre_friction = (base_friction - total_degradation) * weather_multiplier
```

**Max safe corner speed** (page 8). Exceed it → crash:
```
max_corner_speed = sqrt(tyre_friction * g * radius)
```
Worked example: `sqrt(0.9 * 9.8 * 50) = 21 m/s`.

**Kinematics** (constant accel `a`):
```
time   to go v0→v1 :  (v1 - v0) / a
dist   to go v0→v1 :  (v1² - v0²) / (2a)
v after distance d :  sqrt(v0² + 2·a·d)        (a<0 for braking)
time over distance :  (sqrt(v0² + 2·a·d) - v0) / a
```

**Fuel used over a segment** (page 7):
```
F = (K_base + K_drag * ((v_initial + v_final)/2)²) * distance
```
Example: v 50→70, d 800 → 0.40432 L.

**Tyre degradation** (page 6) — only matters L4 (L1–L3 tyres don't degrade):
```
straight :  deg_rate * length * K_STRAIGHT
braking  :  ((v_i/100)² - (v_f/100)²) * K_BRAKING * deg_rate
corner   :  K_CORNER * (speed² / radius) * deg_rate
```
`deg_rate` = the compound's degradation value for the active weather.

**Refuel / pit** (pages 7, 9):
```
refuel_time   = amount_to_refuel / refuel_rate
pit_stop_time = refuel_time + pit_tyre_swap_time + base_pit_stop_time
```
Tyre swap time applies only when changing tyres; refuel time only when refuelling.

## Weather multipliers (page 10)

Weather affects **acceleration**, **deceleration** (via `acceleration_multiplier` /
`deceleration_multiplier` on the condition) and **tyre wear + friction** (via the
per-compound `*_friction_multiplier` / `*_degradation`). On a straight use
`accel * accel_multiplier` and `brake * decel_multiplier`. Conditions cycle in list
order from the starting condition; when all have elapsed, it restarts. Default dry if
none specified. Helper: `Level.weather_at(elapsed_s)`.

## The per-segment state machine — implement this in `simulate()`

State carried across segments: `current_speed`, `fuel`, `tyre` (compound + `total_degradation`),
`elapsed_time`, mode ∈ {normal, crawl, limp}, and bookkeeping (crashes, blowouts,
Σ degradation per tyre set used).

Initial state: `speed = 0`, `fuel = car.initial_fuel`, tyre = `initial_tyre_id`,
mode = normal, weather = starting condition.

Process laps in order; within a lap, segments in order; **pit only at lap end**.

### Limp mode (highest priority)
Triggered when `fuel` hits 0 mid-segment **or** tyre `life_span`/health hits 0 (blowout).
Car travels at constant `car.limp_speed`, **no accel/decel**, for the rest of that
segment and **all subsequent segments** until a pit stop fixes it. Time =
`length / limp_speed`. A blowout also counts toward `blowouts`.

### Crawl mode (from a crash)
Triggered when corner entry speed > `max_corner_speed`. On that corner: add
`corner_crash_penalty_s` to time, add **flat 0.1** to tyre degradation, set speed =
`car.crawl_speed`. Car stays in crawl (constant `crawl_speed`, no accel) for any
**subsequent corners** until a **straight** is reached, where it can accelerate again.

### Straight (normal mode)
Inputs: entry speed `v0`, `target` speed `vt`, braking point `b` =
`brake_start_m_before_next` (metres before the end), length `L`. Effective
`a = accel * accel_multiplier`, `d = brake * decel_multiplier`. Min speed everywhere is
`crawl_speed`; max is `car.max_speed`.

1. **Non-braking portion** = `L - b`. Accelerate `v0 → min(vt, max_speed)`:
   - If `vt > v0`: accel distance = `(vt² - v0²)/(2a)`. If ≤ `L-b`, reach `vt` then
     cruise; speed at brake point = `vt`. Else still accelerating: speed = `sqrt(v0² + 2a(L-b))`.
   - If `vt ≤ v0` (**follow-through rule, assumption 11**): no acceleration, cruise at
     `v0`; speed at brake point = `v0`. (You do *not* brake down to a lower target — the
     only braking is for the upcoming corner, via `b`.)
2. **Braking portion** = `b`. Decelerate at `d`: exit speed =
   `max(crawl_speed, sqrt(v_brakepoint² - 2·d·b))`. If `b = 0`, exit = brake-point speed.
3. **Time** = sum of accel-phase + cruise-phase + brake-phase times (use kinematics
   helpers per phase). **Fuel** = `fuel_used(...)` over the segment (split by phase if
   you want precision; the formula takes avg of entry & exit). **Wear** =
   `straight_degradation` + `braking_degradation` (L4 only).
4. Exit speed becomes the next segment's entry speed.

### Corner
Constant speed through the corner = the entry speed (no accel/decel, assumption 5).
1. Compute `max_corner_speed` from current `tyre_friction` and `radius`.
2. If entry speed > max → **crash** (see Crawl mode). Otherwise proceed at entry speed.
3. Time = `length / speed`. Fuel = `fuel_used(speed, speed, length)`. Wear =
   `corner_degradation` (L4). Exit speed = entry speed (unless crashed → crawl speed).

> ⚠ **Consecutive corners share one entry speed.** You can't brake or accelerate
> between corners, so a run of corners must be entered at a speed safe for the *tightest*
> one. The optimiser must brake on the preceding straight for the minimum of the upcoming
> corner sequence. (The L1 baseline in `strategy.py` already does this.)

### Pit stop (lap end only)
If `pit.enter`: apply tyre change (reset degradation for the new set, record Σ degradation
*used* on the old set) and/or refuel (cap at `fuel_tank_capacity`). Add `pit_stop_time`.
After a pit, car **exits at `pit_exit_speed`** and limp/crawl mode clears. Refuelling/tyre
change is what lifts limp mode.

## ⚠ Open questions / spec ambiguities — RESOLVE BY TESTING

Both are isolated as single switches in `f1/physics.py`. Validate against any
organiser-provided sample output or the leaderboard, then lock the choice.

1. **Friction weather multiplier** (`USE_WEATHER_FRICTION_MULTIPLIER`, default `True`).
   The formula multiplies by `weather_multiplier`, and the per-compound table exists to
   supply it (Soft/dry = 1.18). But the page-6 worked example multiplied by `(1)`. We
   use the table; flip to `False` to match the example literally.

2. **Corner crawl term** (`ADD_CRAWL_TO_CORNER`, default `False`). Page 8 + its worked
   example (`=21`) use no crawl term; page 4 shows `+ crawl_constant`. We follow page 8.

3. **Σ tyre_degradation in the tyre bonus** — sum of final degradation across all tyre
   sets used? Per set? Confirm before optimising L4.

4. **base_friction in level files** — present in `level1.json`, absent in the PDF's
   level-4 example. `model.py` falls back to the page-5 canonical table when absent.

When you resolve one, update the switch's default here and in `physics.py`, and pin a
golden test in `tests/test_simulate.py`.
