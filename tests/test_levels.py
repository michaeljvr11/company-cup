"""End-to-end regression tests for all four levels.

Each level must build a clean (no crashes, no blowouts), deterministic strategy that
beats a score floor. Floors are set below the current tuned scores so normal tuning
doesn't trip them but a real regression does.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from f1.model import load_level
from f1.score import base_score, fuel_bonus, tyre_bonus
from f1.simulate import features, simulate
from f1.strategy import build_strategy
from f1.strategy_io import to_submission

ROOT = Path(__file__).resolve().parents[1]
SCORE_FLOOR = {1: 202_000, 2: 900_000, 3: 850_000, 4: 1_450_000}


def _score(n, lvl, res):
    s = base_score(res.total_time)
    if n >= 2:
        s += fuel_bonus(res.fuel_used, lvl.race.fuel_soft_cap_limit)
    if n >= 4:
        s += tyre_bonus(res.total_degradation_used, res.blowouts)
    return s


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_level_clean_and_scores(n):
    lvl = load_level(str(ROOT / f"levels/level{n}.json"))
    strat = build_strategy(lvl, n)
    res = simulate(lvl, strat, **features(n))
    assert res.crashes == 0, f"L{n} has {res.crashes} crashes"
    assert res.blowouts == 0, f"L{n} has {res.blowouts} blowouts"
    assert res.finished
    # every lap covers every segment in track order
    seg_ids = [s.id for s in lvl.track.segments]
    for lap in to_submission(strat)["laps"]:
        assert [s["id"] for s in lap["segments"]] == seg_ids
    assert _score(n, lvl, res) >= SCORE_FLOOR[n]


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_level_deterministic(n):
    lvl = load_level(str(ROOT / f"levels/level{n}.json"))
    a = to_submission(build_strategy(lvl, n))
    b = to_submission(build_strategy(lvl, n))
    assert a == b
