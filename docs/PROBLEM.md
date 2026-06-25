# Entelect Grand Prix — Problem Overview

Distilled from `Entelect F1 Hacakathon Problem Statement.pdf` (25 pages). This is the
single source of truth for *what* we're building. For *how the physics works* see
[PHYSICS.md](PHYSICS.md); for *code layout* see [ARCHITECTURE.md](ARCHITECTURE.md);
for *who does what* see [WORKPLAN.md](WORKPLAN.md).

## The task

You are the race strategist. Given a **level file** (JSON describing the car, track,
tyres, weather), produce a **strategy** (JSON output) that decides, per segment per lap:

- Which tyre compound to start on, and tyre changes at pit stops.
- Target speed on each straight.
- The braking point on each straight (metres before the next segment).
- When to pit (only at the end of a lap) to change tyres and/or refuel.

You're scored on **race time** (faster = more points), with bonuses for fuel and tyre
efficiency in later levels. Take a corner too fast → crash (time penalty + tyre damage +
crawl mode). Run out of fuel or blow a tyre → limp mode until you pit.

## Levels (each adds to the previous)

| Level | New factors | Scoring |
|-------|-------------|---------|
| **1** | Navigation, target speed, braking points, safe corner entry, start tyre. **Tyres do NOT degrade.** Fuel unlimited. Always dry. | `base = 1e9 / time` |
| **2** | Fuel management + pit stops (refuel). Fuel is a **soft cap** — exceeding it costs score. | `base + fuel_bonus` |
| **3** | Weather changes over time. Pick tyres for the weather; pit when it changes; friction shifts. | `base + fuel_bonus` |
| **4** | Tyre degradation matters. Manage a **limited** set of tyres; avoid blowouts; maximise tyre health used. | `base + fuel_bonus + tyre_bonus` |

## Scoring formulas (page 13)

```
base_score = 1_000_000_000 / time

fuel_bonus = -1_000_000 * (1 - fuel_used / fuel_soft_cap_limit)^2 + 1_000_000

tyre_bonus = 100_000 * Σ(tyre_degradation_used) - 50_000 * blowouts

final = base_score + fuel_bonus (L2/L3) + tyre_bonus (L4)
```

`fuel_bonus` is maximised (→ 1_000_000) as `fuel_used` approaches the soft cap from
below; it falls off quadratically. Going over the cap pushes the ratio > 1 and the
bonus negative. `tyre_bonus` rewards *using up* tyre life (high Σ degradation) without
blowouts. **Open question:** what exactly "Σ tyre_degradation_used" sums over — verify
against an organiser sample (see [PHYSICS.md](PHYSICS.md) §Open questions).

## Submission format

Two files to the Entelect Hackathon site:
1. A **ZIP of the source code**.
2. A **.txt file** containing the output JSON.

**Determinism is mandatory.** The organisers re-run your source; if it doesn't
reproduce the submitted `.txt` byte-for-byte-equivalent (same JSON), the submission is
invalid. → No unseeded randomness anywhere in strategy generation.

Output shape (see `f1/strategy_io.py` for the serialiser, pages 13-16 for the full
example):

```json
{
  "initial_tyre_id": 1,
  "laps": [
    {
      "lap": 1,
      "segments": [
        { "id": 1, "type": "straight", "target_m/s": 70, "brake_start_m_before_next": 800 },
        { "id": 2, "type": "corner" }
      ],
      "pit": { "enter": true, "tyre_change_set_id": 3, "fuel_refuel_amount_l": 20 }
    }
  ]
}
```

- Straights carry `target_m/s` and `brake_start_m_before_next`. Corners carry only
  `id` + `type`.
- `pit.enter` false → omit the rest. If `tyre_change_set_id` or `fuel_refuel_amount_l`
  is absent/zero, that change isn't made.

## Level file inputs

A level JSON has `car`, `race`, `track` (ordered `segments`), `tyres.properties` (per
compound), `available_sets` (tyre ids ↔ compound), and `weather.conditions`. JSON keys
carry unit suffixes (`max_speed_m/s`, `accel_m/se2`, …) — `f1/model.py` strips these.
Full field reference: PDF appendix pages 17-21, mirrored in `f1/model.py`.
