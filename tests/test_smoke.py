"""Smoke tests: the pipeline loads, plans, and serialises a valid submission.

Run: python -m pytest   (or: python tests/test_smoke.py)
The simulator tests live in test_simulate.py and are skipped until it's implemented.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from f1.model import load_level
from f1.strategy import build_strategy
from f1.strategy_io import to_submission

LEVEL1 = str(Path(__file__).resolve().parents[1] / "levels" / "level1.json")


def test_load_level1():
    level = load_level(LEVEL1)
    assert level.race.laps == 50
    assert len(level.track.segments) == 15
    assert level.tyre_props(1).name == "Soft"
    assert level.weather_at(0) == "dry"


def test_baseline_submission_shape():
    level = load_level(LEVEL1)
    sub = to_submission(build_strategy(level, 1))
    assert sub["initial_tyre_id"] == 1
    assert len(sub["laps"]) == 50
    seg_ids = [s["id"] for s in sub["laps"][0]["segments"]]
    assert seg_ids == [s.id for s in level.track.segments]
    for s in sub["laps"][0]["segments"]:
        if s["type"] == "straight":
            assert "target_m/s" in s and "brake_start_m_before_next" in s
    # round-trips through JSON
    json.loads(json.dumps(sub))


if __name__ == "__main__":
    test_load_level1()
    test_baseline_submission_shape()
    print("smoke tests passed")
