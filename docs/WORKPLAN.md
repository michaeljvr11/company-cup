# Work Plan — parallel tracks for 2 people + agents

**Status:** scaffold + both tracks implemented. The simulator (`simulate.py`) models all
levels and is verified on L1. The optimiser (`strategy.py`) fully solves L1 and produces
valid, crash-free baselines for L2-4. What's left is **scoring tuning for L2-4**, which
needs the real level files (we only have `level1.json`). See "Remaining" below.

The original split (two independent tracks behind frozen contracts) still holds for
that remaining work — A owns `simulate.py`, B owns `strategy.py`.

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
