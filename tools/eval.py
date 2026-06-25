"""Tuning harness: score breakdown per level. Run: python tools/eval.py [levels...]"""

import sys
import time as _time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from f1.model import load_level
from f1.score import base_score, fuel_bonus, tyre_bonus
from f1.simulate import features, simulate
from f1.strategy import build_strategy

LEVELS = {n: f"levels/level{n}.json" for n in (1, 2, 3, 4)}


def evaluate(n: int) -> float:
    lvl = load_level(LEVELS[n])
    t0 = _time.perf_counter()
    strat = build_strategy(lvl, n)
    build_s = _time.perf_counter() - t0
    res = simulate(lvl, strat, **features(n))
    pits = sum(1 for lap in strat.laps if lap.pit.enter)
    tyre_changes = sum(1 for lap in strat.laps if lap.pit.enter and lap.pit.tyre_change_set_id)
    base = base_score(res.total_time)
    fb = fuel_bonus(res.fuel_used, lvl.race.fuel_soft_cap_limit) if n >= 2 else 0.0
    tb = tyre_bonus(res.total_degradation_used, res.blowouts) if n >= 4 else 0.0
    total = base + fb + tb
    print(f"L{n}  {lvl.race.name}   (start tyre {strat.initial_tyre_id} = {lvl.compound_of(strat.initial_tyre_id)})")
    print(f"  time={res.total_time:,.1f}s  laps={lvl.race.laps}  pits={pits} (tyre changes {tyre_changes})  build={build_s:.2f}s")
    print(
        f"  fuel_used={res.fuel_used:,.1f} / cap {lvl.race.fuel_soft_cap_limit}   "
        f"crashes={res.crashes}  blowouts={res.blowouts}  sum_deg={res.total_degradation_used:.2f}"
    )
    print(f"  base={base:,.0f}   fuel_bonus={fb:,.0f}   tyre_bonus={tb:,.0f}   TOTAL={total:,.0f}\n")
    return total


if __name__ == "__main__":
    ns = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4]
    grand = sum(evaluate(n) for n in ns)
    if len(ns) > 1:
        print(f"GRAND TOTAL: {grand:,.0f}")
