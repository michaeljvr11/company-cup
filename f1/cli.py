"""Entry point: build a submission for a level and (if available) report its sim result.

    python -m f1 levels/level1.json
    python -m f1 levels/level1.json output/level1.txt --level 1
"""

import re
import sys
from pathlib import Path

from f1 import simulate as sim
from f1.model import load_level
from f1.score import final_score
from f1.strategy import build_strategy
from f1.strategy_io import write_submission


def _infer_level(path: str, override: int | None) -> int:
    if override is not None:
        return override
    m = re.search(r"level\s*0*(\d+)", path, re.IGNORECASE)
    return int(m.group(1)) if m else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: python -m f1 <level.json> [out.txt] [--level N] [--level3-beam-width N] [--level3-lambdas CSV|full] [--level3-log]")
        return 1

    level_override = None
    if "--level" in argv:
        i = argv.index("--level")
        level_override = int(argv[i + 1])
        del argv[i : i + 2]

    level3_beam_width = None
    if "--level3-beam-width" in argv:
        i = argv.index("--level3-beam-width")
        level3_beam_width = int(argv[i + 1])
        del argv[i : i + 2]

    level3_lambda_fuel = "default"
    if "--level3-lambdas" in argv:
        i = argv.index("--level3-lambdas")
        raw = argv[i + 1].strip().lower()
        level3_lambda_fuel = None if raw == "full" else tuple(float(x) for x in raw.split(",") if x)
        del argv[i : i + 2]

    level3_log = False
    if "--level3-log" in argv:
        argv.remove("--level3-log")
        level3_log = True

    level_path = argv[0]
    out_path = argv[1] if len(argv) > 1 else "output/submission.txt"
    level_num = _infer_level(level_path, level_override)

    level = load_level(level_path)
    kwargs = {}
    if level_num == 3:
        if level3_beam_width is not None:
            kwargs["level3_beam_width"] = level3_beam_width
        if level3_lambda_fuel != "default":
            kwargs["level3_lambda_fuel"] = level3_lambda_fuel
        kwargs["level3_log"] = level3_log
    strategy = build_strategy(level, level_num, **kwargs)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    write_submission(strategy, out_path)
    print(f"wrote {out_path}  (level {level_num}, {level.race.laps} laps)")

    try:
        result = sim.simulate(level, strategy, **sim.features(level_num))
        score = final_score(
            level_num,
            result.total_time,
            result.fuel_used,
            level.race.fuel_soft_cap_limit,
            result.total_degradation_used,
            result.blowouts,
        )
        print(
            f"time={result.total_time:.3f}s  fuel={result.fuel_used:.2f}l  "
            f"crashes={result.crashes}  blowouts={result.blowouts}  score={score:,.0f}"
        )
    except NotImplementedError as e:
        print(f"(simulate not implemented yet) {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
