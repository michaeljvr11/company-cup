"""Strategy representation and submission serialization.

The submission `.txt` must contain exactly this JSON shape (problem statement,
pages 13-16): initial tyre id + per-lap, per-segment actions + a pit decision.
Straights carry target speed and braking point; corners carry only id/type.
"""

import json
from dataclasses import dataclass


@dataclass
class SegmentAction:
    id: int
    type: str  # "straight" | "corner"
    target: float | None = None  # m/s, straights only
    brake_start: float | None = None  # m before next segment, straights only


@dataclass
class PitAction:
    enter: bool
    tyre_change_set_id: int | None = None
    fuel_refuel_amount: float | None = None


@dataclass
class LapPlan:
    lap: int
    segments: list[SegmentAction]
    pit: PitAction


@dataclass
class Strategy:
    initial_tyre_id: int
    laps: list[LapPlan]


def _segment_json(a: SegmentAction) -> dict:
    if a.type == "straight":
        return {
            "id": a.id,
            "type": "straight",
            "target_m/s": a.target,
            "brake_start_m_before_next": a.brake_start,
        }
    return {"id": a.id, "type": a.type}


def _pit_json(p: PitAction) -> dict:
    out: dict = {"enter": p.enter}
    if p.enter:
        if p.tyre_change_set_id:
            out["tyre_change_set_id"] = p.tyre_change_set_id
        if p.fuel_refuel_amount:
            out["fuel_refuel_amount_l"] = p.fuel_refuel_amount
    return out


def to_submission(strategy: Strategy) -> dict:
    return {
        "initial_tyre_id": strategy.initial_tyre_id,
        "laps": [
            {
                "lap": lap.lap,
                "segments": [_segment_json(a) for a in lap.segments],
                "pit": _pit_json(lap.pit),
            }
            for lap in strategy.laps
        ],
    }


def write_submission(strategy: Strategy, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_submission(strategy), f, indent=2)
