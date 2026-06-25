"""Strategy generation / optimisation per level. STUB + baseline.

`build_strategy` currently returns a simple, VALID-but-unoptimised level-1 baseline
so the pipeline runs end-to-end today and the simulator has something to chew on.
Replace it with a real optimiser per docs/WORKPLAN.md (Track B). Must stay
deterministic — no unseeded randomness.
"""

from f1.model import Level
from f1.physics import distance_to_reach_speed, max_corner_speed, tyre_friction
from f1.strategy_io import LapPlan, PitAction, SegmentAction, Strategy


def build_strategy(level: Level, level_num: int = 1) -> Strategy:
    if level_num != 1:
        raise NotImplementedError(
            f"No optimiser for level {level_num} yet — see docs/WORKPLAN.md (Track B)."
        )
    return _level1_baseline(level)


def _level1_baseline(level: Level) -> Strategy:
    """Greedy baseline: full throttle on straights, brake just enough to enter the
    next corner sequence at its safe speed. Soft tyres (no degradation in L1)."""
    initial_tyre_id = 1
    tyre = level.tyre_props(initial_tyre_id)
    weather = level.starting_weather().condition
    car = level.car
    segs = level.track.segments
    n = len(segs)

    def safe_speed_for_upcoming_corners(i: int) -> float:
        safe = car.max_speed
        j = (i + 1) % n
        steps = 0
        while segs[j].type == "corner" and steps < n:
            fr = tyre_friction(tyre, 0.0, weather)
            safe = min(safe, max_corner_speed(fr, segs[j].radius, car.crawl_speed))
            j = (j + 1) % n
            steps += 1
        return safe

    laps = []
    for lap_no in range(1, level.race.laps + 1):
        actions = []
        for i, seg in enumerate(segs):
            if seg.type == "straight":
                safe = safe_speed_for_upcoming_corners(i)
                brake_dist = distance_to_reach_speed(safe, car.max_speed, car.brake)
                brake_dist = max(0.0, min(brake_dist, seg.length))
                actions.append(
                    SegmentAction(seg.id, "straight", target=car.max_speed, brake_start=round(brake_dist, 2))
                )
            else:
                actions.append(SegmentAction(seg.id, "corner"))
        laps.append(LapPlan(lap_no, actions, PitAction(enter=False)))

    return Strategy(initial_tyre_id, laps)
