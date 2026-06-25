"""Strategy generation / optimisation.

Level 1 is fully optimised and verified against the simulator: drive flat-out, brake as
late as possible to enter each corner sequence at its safe limit, and pick the start
tyre that gives the fastest clean lap. The same speed plan plus conservative
(weather-robust) corner limits and simulator-driven pit repair produces valid,
race-finishing strategies for levels 2-4 — those are functional baselines to tune once
the level files exist (fuel-bonus targeting and weather-optimal tyre windows aren't
optimised yet). Deterministic throughout.
"""

import math

from f1.model import Level, TyreProps
from f1.physics import max_corner_speed, straight_kinematics, tyre_friction
from f1.simulate import features, simulate
from f1.strategy_io import LapPlan, PitAction, SegmentAction, Strategy

CORNER_SAFETY = 0.999  # enter corners just under the limit to avoid rounding-induced crashes


def build_strategy(level: Level, level_num: int = 1) -> Strategy:
    apply_degradation = features(level_num)["apply_degradation"]

    best_key: tuple[int, float, int] | None = None
    best_strat: Strategy | None = None
    for tyre_id in _candidate_start_tyres(level):
        strat = _speed_plan(level, tyre_id, level_num)
        if level_num >= 2:
            strat = _repair_fuel(level, strat, apply_degradation)
        if level_num >= 4:
            strat = _repair_tyres(level, strat)
        res = simulate(level, strat, apply_degradation=apply_degradation)
        # rank: fewest crashes+blowouts, then fastest time, then lowest id (deterministic)
        key = (res.crashes + res.blowouts, res.total_time, tyre_id)
        if best_key is None or key < best_key:
            best_key, best_strat = key, strat
    assert best_strat is not None
    return best_strat


def _candidate_start_tyres(level: Level) -> list[int]:
    return [s.ids[0] for s in level.available_sets]


def _safe_corner_speed(level: Level, tyre: TyreProps, level_num: int, start_weather: str, radius: float) -> float:
    """Max safe entry speed for a corner, planned against the *worst* friction the tyre
    will see, so we never crash. Weather (>=3): lowest friction across all conditions.
    Degradation (>=4): friction at full wear (deg = life_span), the worst case before a
    pit. This is conservative; per-stint re-planning to go faster is future L4 work."""
    if level_num >= 3 and level.weather:
        weathers = {c.condition for c in level.weather}
    else:
        weathers = {start_weather}
    plan_deg = tyre.life_span if level_num >= 4 else 0.0
    friction = min(tyre_friction(tyre, plan_deg, w) for w in weathers)
    return max_corner_speed(friction, radius, level.car.crawl_speed) * CORNER_SAFETY


def _speed_plan(level: Level, tyre_id: int, level_num: int) -> Strategy:
    car = level.car
    segs = level.track.segments
    n = len(segs)
    tyre = level.tyre_props(tyre_id)
    start_weather = level.starting_weather().condition

    def upcoming_safe(i: int) -> float:
        """Tightest safe entry speed over the run of corners right after straight i."""
        safe = car.max_speed
        j = (i + 1) % n
        for _ in range(n):
            if segs[j].type != "corner":
                break
            safe = min(safe, _safe_corner_speed(level, tyre, level_num, start_weather, segs[j].radius))
            j = (j + 1) % n
        return safe

    # forward pass over two laps; record the second (steady-state) lap's braking points
    speed = 0.0
    brake_for: dict[int, float] = {}
    for _ in range(2):
        for i, seg in enumerate(segs):
            if seg.type == "straight":
                v_safe = upcoming_safe(i)
                b = _optimal_brake_start(speed, v_safe, seg.length, car.accel, car.brake, car.max_speed)
                brake_for[seg.id] = round(b, 3)
                speed, _, _ = straight_kinematics(
                    speed, car.max_speed, b, seg.length, car.accel, car.brake, car.crawl_speed, car.max_speed
                )
            else:
                speed = min(speed, _safe_corner_speed(level, tyre, level_num, start_weather, seg.radius))

    laps = []
    for lap_no in range(1, level.race.laps + 1):
        actions = []
        for seg in segs:
            if seg.type == "straight":
                actions.append(
                    SegmentAction(seg.id, "straight", target=car.max_speed, brake_start=brake_for[seg.id])
                )
            else:
                actions.append(SegmentAction(seg.id, "corner"))
        laps.append(LapPlan(lap_no, actions, PitAction(enter=False)))
    return Strategy(tyre_id, laps)


def _optimal_brake_start(v0: float, v_safe: float, length: float, accel: float, brake: float, max_speed: float) -> float:
    """Latest braking point that still reaches v_safe by the end of the straight."""
    if v_safe >= max_speed:
        return 0.0
    x = (v_safe * v_safe - v0 * v0 + 2 * brake * length) / (2 * (accel + brake))
    if x <= 0:
        return length
    v_peak = math.sqrt(max(0.0, v0 * v0 + 2 * accel * x))
    if v_peak <= max_speed:
        b = length - x
    else:
        b = (max_speed * max_speed - v_safe * v_safe) / (2 * brake)
    return max(0.0, min(b, length))


def _repair_fuel(level: Level, strat: Strategy, apply_degradation: bool) -> Strategy:
    """Insert refuel-to-full pits before any lap where the car would run dry."""
    tank = level.car.fuel_tank_capacity
    for _ in range(len(strat.laps)):
        res = simulate(level, strat, apply_degradation=apply_degradation)
        limp_lap = next((sr.lap for sr in res.segments if sr.limp), None)
        if limp_lap is None:
            return strat
        pit_lap = max(1, limp_lap - 1)
        lp = strat.laps[pit_lap - 1]
        if lp.pit.enter and lp.pit.fuel_refuel_amount:
            pit_lap = max(1, pit_lap - 1)  # already pitting here; move earlier
            lp = strat.laps[pit_lap - 1]
        lp.pit = PitAction(enter=True, tyre_change_set_id=lp.pit.tyre_change_set_id, fuel_refuel_amount=tank)
    return strat


def _repair_tyres(level: Level, strat: Strategy) -> Strategy:
    """Insert tyre-change pits before any lap where the tyre would blow out."""
    spare_ids = [i for s in level.available_sets for i in s.ids]
    for _ in range(len(strat.laps)):
        res = simulate(level, strat, apply_degradation=True)
        if res.blowouts == 0:
            return strat
        blow_lap = next((sr.lap for sr in res.segments if sr.limp), None)
        if blow_lap is None:
            return strat
        pit_lap = max(1, blow_lap - 1)
        lp = strat.laps[pit_lap - 1]
        new_id = spare_ids[pit_lap % len(spare_ids)]
        lp.pit = PitAction(enter=True, tyre_change_set_id=new_id, fuel_refuel_amount=lp.pit.fuel_refuel_amount)
    return strat
