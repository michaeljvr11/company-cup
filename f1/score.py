"""Scoring formulas (problem statement, page 13)."""


def base_score(total_time: float) -> float:
    return 1_000_000_000 / total_time


def fuel_bonus(fuel_used: float, fuel_soft_cap_limit: float) -> float:
    return -1_000_000 * (1 - fuel_used / fuel_soft_cap_limit) ** 2 + 1_000_000


def tyre_bonus(total_degradation_used: float, blowouts: int) -> float:
    return 100_000 * total_degradation_used - 50_000 * blowouts


def final_score(
    level_num: int,
    total_time: float,
    fuel_used: float = 0.0,
    fuel_soft_cap_limit: float = 0.0,
    total_degradation_used: float = 0.0,
    blowouts: int = 0,
) -> float:
    score = base_score(total_time)
    if level_num >= 2 and fuel_soft_cap_limit > 0:
        score += fuel_bonus(fuel_used, fuel_soft_cap_limit)
    if level_num >= 4:
        score += tyre_bonus(total_degradation_used, blowouts)
    return score
