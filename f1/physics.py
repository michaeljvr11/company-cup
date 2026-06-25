"""Pure physics formulas from the problem statement.

These are the shared primitives. The simulator (`simulate.py`) composes them into
the full per-segment state machine; the optimizer (`strategy.py`) uses them to plan.
Keep this module free of race/lap state — just formulas in, numbers out.

Two spec ambiguities are isolated here as single switches. See docs/PHYSICS.md.
"""

import math

from f1.constants import GRAVITY, K_BRAKING, K_CORNER, K_FUEL_DRAG, K_STRAIGHT
from f1.model import TyreProps

# Ambiguity 1 — friction weather multiplier.
# Formula (page 6): tyre_friction = (base_friction - total_degradation) * weather_multiplier.
# The per-compound *_friction_multiplier table (page 5) exists precisely to supply that
# multiplier, so we use it. BUT the page-6 worked example multiplied by (1) for dry, not
# Soft's dry value of 1.18. If validation against organiser samples shows the example is
# literal, flip this to False.
USE_WEATHER_FRICTION_MULTIPLIER = True

# Ambiguity 2 — corner max-speed crawl term.
# Page 8 (and its worked example: sqrt(0.9*9.8*50)=21) uses NO crawl term. Page 4 shows a
# "+ crawl_constant" variant. We follow the worked example. Flip if validation disagrees.
ADD_CRAWL_TO_CORNER = False


# --- Tyre friction & corner limit -------------------------------------------------

def tyre_friction(tyre: TyreProps, total_degradation: float, weather: str) -> float:
    mult = tyre.friction_multipliers[weather] if USE_WEATHER_FRICTION_MULTIPLIER else 1.0
    return (tyre.base_friction - total_degradation) * mult


def max_corner_speed(friction: float, radius: float, crawl_speed: float = 0.0) -> float:
    v = math.sqrt(max(0.0, friction * GRAVITY * radius))
    return v + (crawl_speed if ADD_CRAWL_TO_CORNER else 0.0)


# --- Kinematics (constant acceleration) -------------------------------------------

def time_to_reach_speed(v0: float, v1: float, accel: float) -> float:
    return (v1 - v0) / accel


def distance_to_reach_speed(v0: float, v1: float, accel: float) -> float:
    return (v1 * v1 - v0 * v0) / (2 * accel)


def speed_after_distance(v0: float, accel: float, distance: float) -> float:
    """Speed after travelling `distance` at constant `accel` (negative = braking)."""
    return math.sqrt(max(0.0, v0 * v0 + 2 * accel * distance))


def time_over_distance(v0: float, accel: float, distance: float) -> float:
    """Time to cover `distance` from v0 at constant `accel`. accel may be 0."""
    if abs(accel) < 1e-12:
        return distance / v0 if v0 > 0 else float("inf")
    disc = v0 * v0 + 2 * accel * distance
    return (math.sqrt(max(0.0, disc)) - v0) / accel


# --- Fuel -------------------------------------------------------------------------

def fuel_used(k_base: float, v_initial: float, v_final: float, distance: float) -> float:
    avg = (v_initial + v_final) / 2
    return (k_base + K_FUEL_DRAG * avg * avg) * distance


def refuel_time(amount_l: float, rate_l_per_s: float) -> float:
    return amount_l / rate_l_per_s


# --- Tyre degradation -------------------------------------------------------------

def straight_degradation(deg_rate: float, length: float) -> float:
    return deg_rate * length * K_STRAIGHT


def braking_degradation(deg_rate: float, v_initial: float, v_final: float) -> float:
    return ((v_initial / 100) ** 2 - (v_final / 100) ** 2) * K_BRAKING * deg_rate


def corner_degradation(deg_rate: float, speed: float, radius: float) -> float:
    return K_CORNER * (speed * speed / radius) * deg_rate
