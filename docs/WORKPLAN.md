# Work Plan — parallel tracks for 2 people + agents

The scaffold is done: shared contracts (`model`, `physics`, `score`, `strategy_io`,
`cli`) are implemented and the pipeline runs end-to-end with a baseline. Two big pieces
remain, and they're **independent** — that's the whole point of the design.

## The split

| Track | Owner | Files (yours to edit) | Depends on |
|-------|-------|-----------------------|------------|
| **A — Simulator** | person 1 / agent | `f1/simulate.py`, `tests/test_simulate.py` | frozen contracts only |
| **B — Optimiser** | person 2 / agent | `f1/strategy.py` | `Result` contract; baseline meanwhile |
| **Shared** | both, by PR | `docs/*`, `f1/physics.py` switches, `levels/*.json` | — |

Because A owns `simulate.py` and B owns `strategy.py`, and neither touches the other,
you can work fully concurrently and merge cleanly. The only shared-edit files are docs,
the two `physics.py` ambiguity switches, and new level JSONs — coordinate those by PR.

## Critical path

The simulator (Track A) is the critical path: scoring, optimisation, and validation all
need it. **Prioritise getting a correct L1 simulator first** — even a rough one unblocks
everything. Track B can start immediately against the baseline + hand-checked numbers,
then sharpen once the simulator lands.

## Track A — Simulator (`f1/simulate.py`)

Spec: [PHYSICS.md](PHYSICS.md) §"per-segment state machine". Build incrementally:

1. **Normal-mode L1**: straights (accel/cruise/brake) + corners (constant speed, crash
   check) for one lap, no fuel/wear/weather. Return time + crashes.
2. **Pin golden numbers**: hand-compute one straight and one corner from PHYSICS.md
   examples; assert them in `tests/test_simulate.py`. This is the oracle Track B trusts.
3. **Crawl mode** (post-crash) and **multi-lap**.
4. **Fuel** tracking + **limp mode** (L2).
5. **Weather** cycling affecting accel/decel/friction (L3).
6. **Tyre degradation** + blowouts + Σ-degradation bookkeeping (L4).
7. Fill out `Result`/`SegmentResult` as you go (add fields, don't rename).

Done when: `python -m f1 levels/level1.json` prints a time and `test_simulate.py`
passes with hand-verified L1 numbers.

## Track B — Optimiser (`f1/strategy.py`)

`build_strategy(level, level_num)` → `Strategy`. The L1 baseline is there as a starting
point and a correctness reference (it already brakes for the tightest upcoming corner).

- **L1**: maximise speed / minimise time. Per straight, search target speed + braking
  point; per corner sequence, enter at the tightest safe speed. Pick the start tyre
  giving the highest corner speeds (Soft, no degradation in L1). Use `simulate()` as the
  fitness function once it exists; until then, optimise analytically with `physics.py`.
- **L2**: add pit/refuel decisions; trade speed vs fuel to sit just under the soft cap
  (max `fuel_bonus`). Decide pit laps.
- **L3**: choose tyres per weather window; pit when weather changes; re-tune speeds as
  friction shifts.
- **L4**: manage the limited tyre set; pit before blowouts; maximise tyre life *used*
  without blowing out (max `tyre_bonus`).
- Keep it **deterministic** (seed any search).

Approach: since `simulate()` is the fitness function, a simple search (grid/greedy/
hill-climb over target speeds and braking points, then pit laps) beats hand-tuning.
Start greedy per-segment, then add search where it pays.

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
