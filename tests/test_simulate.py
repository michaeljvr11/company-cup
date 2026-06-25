"""Simulator + level-1 optimiser golden tests.

These pin the verified level-1 behaviour so regressions in the physics or the optimiser
are caught immediately. Numbers were hand-checked against docs/PHYSICS.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from f1.model import load_level
from f1.physics import fuel_used, max_corner_speed, tyre_friction
from f1.simulate import features, simulate
from f1.strategy import build_strategy

LEVEL1 = str(Path(__file__).resolve().parents[1] / "levels" / "level1.json")


def test_physics_matches_spec_examples():
    # corner: sqrt(0.9 * 9.8 * 50) = 21 (page 8)
    assert round(max_corner_speed(0.9, 50), 3) == 21.0
    # fuel: v 50->70 over 800 m = 0.40432 l (page 7)
    assert round(fuel_used(0.0005, 50, 70, 800), 5) == 0.40432


def test_soft_dry_friction():
    level = load_level(LEVEL1)
    # Soft base 1.8, dry multiplier 1.18, no degradation -> 2.124
    assert round(tyre_friction(level.tyre_props(1), 0.0, "dry"), 4) == 2.124


def test_level1_optimiser_is_clean_and_fast():
    level = load_level(LEVEL1)
    strat = build_strategy(level, 1)
    assert strat.initial_tyre_id == 1  # Soft = highest friction = fastest
    res = simulate(level, strat, **features(1))
    assert res.crashes == 0
    assert res.blowouts == 0
    assert res.fuel_used < level.car.initial_fuel  # finishes without refuelling
    assert round(res.total_time, 1) == 4949.6  # golden time


def test_no_corner_exceeds_its_limit():
    level = load_level(LEVEL1)
    res = simulate(level, build_strategy(level, 1), **features(1))
    fr = tyre_friction(level.tyre_props(1), 0.0, "dry")
    by_id = {s.id: s for s in level.track.segments}
    for sr in res.segments:
        if sr.type == "corner":
            assert sr.entry_speed <= max_corner_speed(fr, by_id[sr.id].radius, level.car.crawl_speed) + 1e-6


def test_deterministic():
    level = load_level(LEVEL1)
    s = build_strategy(level, 1)
    assert simulate(level, s, **features(1)).total_time == simulate(level, s, **features(1)).total_time
