"""Physics constants from the problem statement. Single source of truth."""

GRAVITY = 9.8

# Tyre degradation coefficients (problem statement, page 6).
K_STRAIGHT = 0.0000166
K_BRAKING = 0.0398
K_CORNER = 0.000265

# Fuel coefficients (page 7). K_base is also per-car in the JSON
# (car.fuel_consumption) — prefer the JSON value; this is the documented default.
K_FUEL_BASE = 0.0005
K_FUEL_DRAG = 0.0000000015

# Canonical base friction coefficients (page 5 table). Used as a fallback when a
# level JSON omits the per-compound `base_friction` field (the level-4 example does).
BASE_FRICTION = {
    "Soft": 1.8,
    "Medium": 1.7,
    "Hard": 1.6,
    "Intermediate": 1.2,
    "Wet": 1.1,
}

# Weather condition keys, matching the *_friction_multiplier / *_degradation suffixes.
WEATHER_CONDITIONS = ("dry", "cold", "light_rain", "heavy_rain")
