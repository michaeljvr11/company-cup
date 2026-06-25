# Work Plan — parallel tracks for 2 people + agents

**Status:** all four levels implemented, tuned, and clean (0 crashes, 0 blowouts,
deterministic). Current scores: L1 ~201,934 · L2 ~913,471 · L3 ~859,196 · L4 ~1,490,777
(grand total ~3.47M). `python tools/eval.py` prints the live breakdown.

The split still holds for further work — A owns `simulate.py`, B owns `strategy.py`.

## How each level is solved (`f1/strategy.py`)

- **L1 / L2** (`_static_plan`): dry, single-condition, no degradation. Flat-out target,
  brake as late as possible to the corner limit, fastest start tyre (Soft). L2 adds
  simulator-driven refuel pits (`_repair_fuel`) — minimal count, since the tank (150 L) is
  far below total burn.
- **L3 / L4** (`_weather_plan`): weather varies, so corner speeds and braking points are
  planned **per lap** against the conditions in effect then. Iterate-and-simulate: simulate
  → read each lap's weather (and L4 degradation) from the result → re-plan → repeat. Two
  guards keep it crash/blowout-free despite the plan shifting lap timing:
  - Laps that ever crash are pinned to **worst-case weather + full wear** (can't crash).
  - L4 tyre stints are **balanced by wear** across all 9 sets (`_tyre_schedule_l4`), so no
    set blows out; set *ids* are matched to each stint's weather (Wet in heavy rain).

## Key findings (drove the tuning)

1. **Fuel is ~98% distance-bound.** The drag coefficient is tiny (1.5e-9), so fuel_used is
   set by laps×track-length, almost independent of speed — and it sits *above* every soft
   cap. So fuel_bonus is effectively fixed (~815k each for L2-4); you can't slow down to
   reach the cap without losing far more time. ⇒ drive flat-out; just minimise pits.
2. **L3: Soft is the highest-friction tyre in every L3 weather**, so no tyre changes — the
   only weather effect is corner speed (friction) and braking (decel multiplier).
3. **L4: tyre_bonus dominates** (100k × Σdegradation). Σdeg ≈ *total wear produced*,
   independent of how many sets you use — so the win is to spread wear across sets so none
   blows out (a blowout costs 50k *and* triggers limp mode = big time loss), and to drive
   fast (more corner/braking wear = more bonus). Wet's base friction is 1.6 here (not 1.1).

## Remaining ideas (diminishing returns; bonuses already near-fixed)

- L4: push Σdeg higher (currently 6.55 of a ~8.5 ceiling) by cornering closer to the live
  grip limit — tried, but tightening the degradation margin destabilised convergence
  (crashes/blowouts returned). Needs a more stable per-stint wear model, not just a smaller
  margin.
- L2/L4: combine refuel with tyre-change pits where laps align, to save base pit time.
- L3: trim the few transition laps that are planned conservatively.

## ⚠ Open questions — VALIDATE AGAINST THE REAL LEADERBOARD before trusting these scores

- **`time_reference_s`** appears in every level file (L4: 50800) but **not** in the
  documented `base_score = 1e9/time`. The real scoring may normalise time against this
  reference, which would weight time far more heavily than our base term does. If so, time
  matters much more than our breakdown suggests — re-tune toward lower time.
- **Crashing raises Σdeg** (+0.1 wear per crash) with only a 10 s time penalty, so against
  our simulator deliberate crashing can *increase* the tyre bonus. We deliberately do **not**
  exploit this (clean driving), as it's almost certainly penalised harder on the real
  leaderboard (see the time_reference question). Confirm before changing stance.
- The two friction ambiguities in [PHYSICS.md](PHYSICS.md) are still unresolved.

## The split

| Track | Owner | Files (yours to edit) | Depends on |
|-------|-------|-----------------------|------------|
| **A — Simulator** | person 1 / agent | `f1/simulate.py`, `tests/test_simulate.py` | frozen contracts only |
| **B — Optimiser** | person 2 / agent | `f1/strategy.py` | `Result` contract; baseline meanwhile |
| **Shared** | both, by PR | `docs/*`, `f1/physics.py` switches, `levels/*.json` | — |

Because A owns `simulate.py` and B owns `strategy.py`, and neither touches the other,
you can work fully concurrently and merge cleanly. The only shared-edit files are docs,
the two `physics.py` ambiguity switches, and new level JSONs — coordinate those by PR.

## Done so far

**Track A — Simulator (`f1/simulate.py`)** — complete for all levels: straights
(accel/cruise/brake with the crawl floor), corners (constant speed + crash check),
crawl mode (post-crash), limp mode (fuel-out/blowout), multi-lap, fuel, weather cycling
(accel/decel/friction), tyre degradation + blowouts + Σ-degradation bookkeeping, pit
stops. `apply_degradation` is gated by level (off ≤ L3). Verified on L1 with golden
numbers in `tests/test_simulate.py`.

**Track B — Optimiser (`f1/strategy.py`)**:
- **L1 — fully optimised & verified.** Flat-out target (`max_speed`), latest-possible
  braking to enter each corner sequence at its limit (analytic `_optimal_brake_start`
  via a 2-lap forward pass), fastest start tyre chosen by simulation (Soft). Clean run,
  ~4952 s, score ≈ 202k. Corners entered within 0.03 m/s of the limit.
- **L2-L4 — valid, crash-free baselines.** Same speed plan + conservative corner limits
  (L3: lowest friction across weathers; L4: friction at full wear) + simulator-driven
  pit repair (`_repair_fuel`, `_repair_tyres`) so the race always finishes without
  limp/blowout. **Scoring is not yet optimised** (see Remaining).

## Remaining (needs the real level 2-4 files — we only have level1.json)

1. **L2 fuel bonus**: tune speeds + refuel amounts to land fuel_used *just under* the
   soft cap (bonus → 1e6), instead of just "don't run dry". Pick pit laps to minimise
   pit-time vs fuel-bonus trade-off.
2. **L3 weather**: pick the tyre compound per weather window and pit on weather changes,
   rather than one conservative tyre for the whole race. Re-tune braking per window.
3. **L4 tyre bonus**: per-stint corner re-planning (go faster while fresh, ease off as
   the tyre wears) instead of the worst-case-friction baseline; choose pit laps to
   maximise tyre life *used* (Σ degradation → high) without blowing out.
4. Resolve the two [PHYSICS.md](PHYSICS.md) friction ambiguities against an organiser
   sample and lock the switches.

Approach for all of these: `simulate()` is the fitness function — wrap it in a small
deterministic search (greedy / hill-climb over speeds, braking points, pit laps, tyre
choices). Add a `levels/levelN.json`, then iterate.

## How agents fit in

The two tracks map cleanly onto two agents (or two people, or a mix). When spinning up
an agent, point it at this repo and tell it: *"Implement Track A (simulator) per
docs/PHYSICS.md, editing only f1/simulate.py and tests/test_simulate.py"* (or Track B
analogously). The frozen contracts keep their work non-conflicting. Run them on separate
git branches / worktrees and merge via PR.

## Git workflow (two clones, shared GitHub repo)

- `main` stays runnable. Branch per track: `track-a-simulator`, `track-b-optimiser`.
- Small, frequent PRs. The frozen-contract boundary means A and B rarely touch the same
  files — conflicts should be limited to docs and the two `physics.py` switches.
- When you resolve a PHYSICS.md ambiguity, do it in one PR (switch default + doc + golden
  test) so both clones pick up the same decision.
- Don't commit `output/*.txt` (gitignored) — they're regenerated.

## Definition of done (per level)

`python -m f1 levels/levelN.json output/levelN.txt --level N` produces a valid
submission, `simulate()` confirms no unintended crashes/limp, and the printed score is
sane. Then submit source ZIP + the `.txt`.
