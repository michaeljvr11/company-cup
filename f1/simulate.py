"""Race simulator — THE shared foundation. STUB: implement against docs/PHYSICS.md.

Given a Level and a Strategy, deterministically replay the race and report time,
fuel, tyre wear, crashes and blowouts. Everything else (optimisation, scoring,
validation) depends on this being correct, so it is the critical path.

The Result / SegmentResult dataclasses below are a FROZEN CONTRACT — the optimizer
and tests code against them, so add fields rather than rename/remove. The body of
`simulate()` is the implementation work; see docs/PHYSICS.md for the per-segment
algorithm (accelerate/cruise/brake, corner crash + crawl, limp mode, pit stops).
"""

from dataclasses import dataclass, field

from f1.model import Level
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


def simulate(level: Level, strategy: Strategy) -> Result:
    raise NotImplementedError(
        "Race simulator not implemented yet. See docs/PHYSICS.md for the full "
        "per-segment algorithm and docs/WORKPLAN.md (Track A)."
    )
