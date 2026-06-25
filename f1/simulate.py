"""Race simulator — THE shared foundation.

Given a Level and a Strategy, deterministically replay the race and report time,
fuel, tyre wear, crashes and blowouts. See docs/PHYSICS.md for the algorithm.

`apply_degradation` is off for levels 1-3 (the spec says tyres don't degrade until
level 4); fuel and weather are always modelled (inert when a level is single-condition
dry with ample fuel). The Result / SegmentResult dataclasses are the contract the
optimiser and tests code against — add fields rather than rename/remove.

Limp (fuel-out / blowout) and crawl (crash) transitions are resolved at segment
granularity — a segment that *would* deplete fuel or blow the tyre is treated as
entering the failure mode for that whole segment. Good enough; the optimiser's job is
to never get there. Fuel for a segment uses its entry & exit speed (the spec's per-
segment fuel formula).
"""

from dataclasses import dataclass, field

from f1.model import Level
from f1.physics import (
    braking_degradation,
    corner_degradation,
    fuel_used,
    max_corner_speed,
    refuel_time,
    straight_degradation,
    straight_kinematics,
    tyre_friction,
)
from f1.strategy_io import Strategy


@dataclass
class SegmentResult:
    lap: int
    id: int
    type: str
    entry_speed: float
    exit_speed: float
    time: float
    fuel_used: float
    degradation: float  # tyre degradation accrued on this segment
    crashed: bool = False
    limp: bool = False


@dataclass
class Result:
    total_time: float
    fuel_used: float
    total_degradation_used: float  # sum across tyre sets used, for the tyre bonus
    blowouts: int
    crashes: int
    finished: bool
    segments: list[SegmentResult] = field(default_factory=list)


def features(level_num: int) -> dict:
    """Which physics layers are active for a given level."""
    return {"apply_degradation": level_num >= 4}


def simulate(level: Level, strategy: Strategy, apply_degradation: bool = True) -> Result:
    car = level.car
    race = level.race
    k_base = car.fuel_consumption

    speed = 0.0
    tank = car.initial_fuel
    tyre = level.tyre_props(strategy.initial_tyre_id)
    degradation = 0.0
    elapsed = 0.0
    mode = "normal"  # normal | crawl | limp

    fuel_consumed = 0.0
    total_deg_used = 0.0
    blowouts = 0
    crashes = 0
    results: list[SegmentResult] = []

    segs = level.track.segments
    for lap in strategy.laps:
        action_by_id = {a.id: a for a in lap.segments}
        for seg in segs:
            entry = speed
            cond = level.active_condition(elapsed)
            weather = cond.condition if cond else "dry"
            a_eff = car.accel * (cond.accel_multiplier if cond else 1.0)
            d_eff = car.brake * (cond.decel_multiplier if cond else 1.0)
            deg_rate = tyre.degradation[weather]

            crashed = False

            if mode != "limp" and tank <= 1e-9:
                mode = "limp"

            if mode == "limp":
                v_exit = car.limp_speed
                seg_time = seg.length / car.limp_speed
                seg_fuel = fuel_used(k_base, car.limp_speed, car.limp_speed, seg.length)
                seg_deg = (
                    straight_degradation(deg_rate, seg.length)
                    if seg.type == "straight"
                    else corner_degradation(deg_rate, car.limp_speed, seg.radius)
                ) if apply_degradation else 0.0

            elif seg.type == "straight":
                mode = "normal"  # a straight ends crawl mode
                action = action_by_id.get(seg.id)
                target = action.target if action and action.target is not None else car.max_speed
                brake_start = action.brake_start if action and action.brake_start is not None else 0.0
                v_exit, seg_time, v_bp = straight_kinematics(
                    speed, target, brake_start, seg.length, a_eff, d_eff, car.crawl_speed, car.max_speed
                )
                seg_fuel = fuel_used(k_base, speed, v_exit, seg.length)
                seg_deg = 0.0
                if apply_degradation:
                    seg_deg = straight_degradation(deg_rate, seg.length) + braking_degradation(
                        deg_rate, v_bp, v_exit
                    )

            else:  # corner
                if mode == "crawl":
                    used_speed = car.crawl_speed
                    v_exit = car.crawl_speed
                    seg_time = seg.length / car.crawl_speed
                else:
                    friction = tyre_friction(tyre, degradation, weather)
                    v_max = max_corner_speed(friction, seg.radius, car.crawl_speed)
                    if speed > v_max:
                        crashed = True
                        crashes += 1
                        mode = "crawl"
                        used_speed = car.crawl_speed
                        v_exit = car.crawl_speed
                        seg_time = seg.length / car.crawl_speed + race.corner_crash_penalty
                        if apply_degradation:
                            degradation += 0.1
                    else:
                        used_speed = speed
                        v_exit = speed
                        seg_time = seg.length / used_speed
                seg_fuel = fuel_used(k_base, used_speed, used_speed, seg.length)
                seg_deg = corner_degradation(deg_rate, used_speed, seg.radius) if apply_degradation else 0.0

            # commit segment
            elapsed += seg_time
            fuel_consumed += seg_fuel
            tank = max(0.0, tank - seg_fuel)
            limp_here = mode == "limp"
            if apply_degradation:
                degradation += seg_deg
                if degradation >= tyre.life_span and mode != "limp":
                    blowouts += 1
                    mode = "limp"
                    limp_here = True
            speed = v_exit
            results.append(
                SegmentResult(lap.lap, seg.id, seg.type, entry, v_exit, seg_time, seg_fuel, seg_deg, crashed, limp_here)
            )

        # pit stop (lap end only)
        pit = lap.pit
        if pit.enter:
            extra = race.base_pit_stop_time
            if pit.tyre_change_set_id:
                if apply_degradation:
                    total_deg_used += degradation
                tyre = level.tyre_props(pit.tyre_change_set_id)
                degradation = 0.0
                extra += race.pit_tyre_swap_time
            if pit.fuel_refuel_amount and pit.fuel_refuel_amount > 0:
                amount = min(pit.fuel_refuel_amount, car.fuel_tank_capacity - tank)
                tank += amount
                extra += refuel_time(amount, race.pit_refuel_rate)
            elapsed += extra
            mode = "normal"
            speed = race.pit_exit_speed

    if apply_degradation:
        total_deg_used += degradation

    return Result(
        total_time=elapsed,
        fuel_used=fuel_consumed,
        total_degradation_used=total_deg_used,
        blowouts=blowouts,
        crashes=crashes,
        finished=True,
        segments=results,
    )
