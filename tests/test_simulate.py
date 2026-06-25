"""Simulator tests — fill these in as Track A implements f1/simulate.py.

The first job once simulate() exists: pin down the per-segment numbers by hand
(from docs/PHYSICS.md worked examples) and assert them here. That gives the
optimiser a trustworthy oracle.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from f1 import simulate as sim
from f1.model import load_level
from f1.strategy import build_strategy

LEVEL1 = str(Path(__file__).resolve().parents[1] / "levels" / "level1.json")


def _implemented() -> bool:
    try:
        sim.simulate(load_level(LEVEL1), build_strategy(load_level(LEVEL1), 1))
        return True
    except NotImplementedError:
        return False


@pytest.mark.skipif(not _implemented(), reason="simulate() not implemented yet")
def test_level1_baseline_finishes_without_crashes():
    level = load_level(LEVEL1)
    result = sim.simulate(level, build_strategy(level, 1))
    assert result.finished
    assert result.crashes == 0
    assert result.total_time > 0


@pytest.mark.skipif(not _implemented(), reason="simulate() not implemented yet")
def test_deterministic():
    level = load_level(LEVEL1)
    strat = build_strategy(level, 1)
    assert sim.simulate(level, strat).total_time == sim.simulate(level, strat).total_time
