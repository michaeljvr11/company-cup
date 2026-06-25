"""Level data model: load a level JSON into typed objects.

This is the shared contract every module builds on. The JSON keys carry unit
suffixes (`max_speed_m/s`, `accel_m/se2`, ...); we strip them here so the rest of
the codebase deals in plain names.
"""

import json
from dataclasses import dataclass

from f1.constants import BASE_FRICTION


@dataclass
class Car:
    max_speed: float
    accel: float
    brake: float
    limp_speed: float
    crawl_speed: float
    fuel_tank_capacity: float
    initial_fuel: float
    fuel_consumption: float  # K_base, l/m


@dataclass
class Race:
    name: str
    laps: int
    base_pit_stop_time: float
    pit_tyre_swap_time: float
    pit_refuel_rate: float
    corner_crash_penalty: float
    pit_exit_speed: float
    fuel_soft_cap_limit: float
    starting_weather_condition_id: int
    time_reference: float | None = None


@dataclass
class Segment:
    id: int
    type: str  # "straight" | "corner"
    length: float
    radius: float | None = None  # corners only


@dataclass
class Track:
    name: str
    segments: list[Segment]


@dataclass
class TyreProps:
    name: str
    life_span: float
    base_friction: float
    friction_multipliers: dict[str, float]  # weather condition -> multiplier
    degradation: dict[str, float]  # weather condition -> degradation rate


@dataclass
class TyreSet:
    ids: list[int]
    compound: str


@dataclass
class WeatherCondition:
    id: int
    condition: str  # "dry" | "cold" | "light_rain" | "heavy_rain"
    duration: float
    accel_multiplier: float
    decel_multiplier: float


@dataclass
class Level:
    car: Car
    race: Race
    track: Track
    tyres: dict[str, TyreProps]  # compound name -> props
    available_sets: list[TyreSet]
    weather: list[WeatherCondition]

    def compound_of(self, tyre_id: int) -> str:
        for s in self.available_sets:
            if tyre_id in s.ids:
                return s.compound
        raise KeyError(f"unknown tyre id {tyre_id}")

    def tyre_props(self, tyre_id: int) -> TyreProps:
        return self.tyres[self.compound_of(tyre_id)]

    def starting_weather(self) -> WeatherCondition:
        for c in self.weather:
            if c.id == self.race.starting_weather_condition_id:
                return c
        return self.weather[0]

    def active_condition(self, elapsed_s: float) -> WeatherCondition | None:
        """The weather condition in effect at a given elapsed race time.

        Conditions cycle in list order starting from the race's starting
        condition; a non-positive duration is treated as 'never changes'.
        """
        conds = self.weather
        if not conds:
            return None
        idx = next(
            (k for k, c in enumerate(conds) if c.id == self.race.starting_weather_condition_id),
            0,
        )
        remaining = elapsed_s
        for _ in range(len(conds) * 1000):  # generous guard against runaway loops
            d = conds[idx].duration
            if d <= 0 or remaining < d:
                return conds[idx]
            remaining -= d
            idx = (idx + 1) % len(conds)
        return conds[idx]

    def weather_at(self, elapsed_s: float) -> str:
        cond = self.active_condition(elapsed_s)
        return cond.condition if cond else "dry"


def load_level(path: str) -> Level:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    c = data["car"]
    car = Car(
        max_speed=c["max_speed_m/s"],
        accel=c["accel_m/se2"],
        brake=c["brake_m/se2"],
        limp_speed=c["limp_constant_m/s"],
        crawl_speed=c["crawl_constant_m/s"],
        fuel_tank_capacity=c["fuel_tank_capacity_l"],
        initial_fuel=c["initial_fuel_l"],
        fuel_consumption=c["fuel_consumption_l/m"],
    )

    r = data["race"]
    race = Race(
        name=r["name"],
        laps=r["laps"],
        base_pit_stop_time=r["base_pit_stop_time_s"],
        pit_tyre_swap_time=r["pit_tyre_swap_time_s"],
        pit_refuel_rate=r["pit_refuel_rate_l/s"],
        corner_crash_penalty=r["corner_crash_penalty_s"],
        pit_exit_speed=r["pit_exit_speed_m/s"],
        fuel_soft_cap_limit=r.get("fuel_soft_cap_limit_l", r.get("fuel_soft_cap_limit", 0.0)),
        starting_weather_condition_id=r.get(
            "starting_weather_condition_id", r.get("starting_weather_condition", 1)
        ),
        time_reference=r.get("time_reference_s"),
    )

    track = Track(
        name=data["track"]["name"],
        segments=[
            Segment(id=s["id"], type=s["type"], length=s["length_m"], radius=s.get("radius_m"))
            for s in data["track"]["segments"]
        ],
    )

    tyres: dict[str, TyreProps] = {}
    for name, p in data["tyres"]["properties"].items():
        tyres[name] = TyreProps(
            name=name,
            life_span=p["life_span"],
            base_friction=p.get("base_friction", BASE_FRICTION[name]),
            friction_multipliers={
                "dry": p["dry_friction_multiplier"],
                "cold": p["cold_friction_multiplier"],
                "light_rain": p["light_rain_friction_multiplier"],
                "heavy_rain": p["heavy_rain_friction_multiplier"],
            },
            degradation={
                "dry": p["dry_degradation"],
                "cold": p["cold_degradation"],
                "light_rain": p["light_rain_degradation"],
                "heavy_rain": p["heavy_rain_degradation"],
            },
        )

    available_sets = [TyreSet(ids=s["ids"], compound=s["compound"]) for s in data["available_sets"]]

    weather = [
        WeatherCondition(
            id=w["id"],
            condition=w["condition"],
            duration=w["duration_s"],
            accel_multiplier=w["acceleration_multiplier"],
            decel_multiplier=w["deceleration_multiplier"],
        )
        for w in data.get("weather", {}).get("conditions", [])
    ]

    return Level(car=car, race=race, track=track, tyres=tyres, available_sets=available_sets, weather=weather)
