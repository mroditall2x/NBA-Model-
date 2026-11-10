# Season data fix + role-change flag (11/10/26)

## What was wrong
`slate1021.py` (the prop sim) and `card_slate.py` loaded `S.load((2025, 2026))` = 2024-25 and 2025-26 only.
Season labels are the ending year, so **no 2026-27 game ever fed the player rates** (minutes were fine: `rot_blend.py`
already blends this season). Players whose role changed this season kept last year's numbers, e.g. Franz Wagner AST
mean 4.6-4.9 vs lines of 6.5-7.5 (actual 15 and 11). The card had drifted to almost all standard Unders and went 41% on
Unders from 10/31-11/08 (three straight losing days 11/06-11/08).

## Changes
1. `slate1021.py`, `card_slate.py`: load 2025, 2026 **and 2027**.
2. `nba_sim.py`: `SEASON_DISC` 0.7 -> 0.4 (prior-season games count 40%, so this season takes over faster).
3. `card_slate.py`: `role up` / `role down` flag when the player's last 8 games this season (5+ needed) run 25%+ above /
   below the model mean, by at least 1 (single stats), 2 (RA), 4 (PTS/PA/PR) or 5 (PRA).
   `run_day.py` blocks Unders on `role up` and Overs on `role down`.

## Replay 10/28-11/08 (10 slates, same lines, minutes and card rules; only data/weights change)
| version | top-10 card | card Unders | card Overs | qualifying pool | Brier (market 0.2521) |
|---|---|---|---|---|---|
| old (2 seasons) | 39-32 54.9% | 48.8% | 63.3% | 63.0% | 0.2543 (worse than market) |
| + 2027 | 48-31 60.8% | 56.2% | 67.7% | 65.3% | 0.2495 |
| + 2027, SEASON_DISC 0.4 | 56-25 69.1% | 64.7% | 76.7% | 67.7% | 0.2488 |
| + role flag (shipped) | 54-23 70.1% | 66.7% | 75.9% | 69.4% | 0.2488 |

Caveats: 10 days, ~80 card picks. SEASON_DISC 0.4 was a single try tested on the same days, so expect less going
forward (~60-65%). Re-run on fresh days in ~2 weeks (`replay_1028_1108_season_run.sh` + `_grade.py`).
SEASON_DISC also feeds team ratings, so full-game numbers (games.csv) shift too; not separately tested.

# Returning players (11/10/26, second change)
Problem: `rot_blend.py` averaged this-season minutes over every TEAM game, so a starter back from injury looked like a
part-timer (Dejounte Murray 11/04 given 24, played 45; Strus 11/02 13 vs 23; Jalen Johnson 11/07 28 vs 36), and
teammates kept the minutes they got while he was out.

Shipped (`rot_blend.py`, `card_slate.py`, `run_day.py`):
- Returning player = active today after missing 2+ straight team games, with his own prop line (or, when the game has
  no props, a 20+ min regular who has played this season). Minutes = his normal (games he was available for, blended
  with last season) x 0.9. Saved to `slate/<date>_returning.json`.
- Card: the returner is flagged `returning ... minutes unclear` (off the card, first game back). Teammates of a 20+ min
  returner whose last 8 run 15%+ above the model are flagged `teammate back` -> no Overs (their bump came while he was out).

Full-pipeline replay 10/28-11/08 (rot_blend -> pass 1 -> market blend -> pass 2 -> card), vs this morning's version:
| version | card | Unders | pool | returner minutes MAE / bias (13) | teammates MAE (130) |
|---|---|---|---|---|---|
| base (this morning) | 53-21 71.6% | 69.6% | 67.4% | 5.74 / -4.9 | 5.99 |
| returners + available-games minutes for all | 48-28 63.2% | 60.0% | 61.8% | 5.50 / +1.2 | 5.48 |
| returners + drop no-line players | 52-23 69.3% | 66.0% | 68.7% | 5.88 / +2.0 | 6.11 |
| **returners only (shipped)** | 53-22 70.7% | 68.1% | 68.4% | 5.92 / +2.0 | 6.12 |
The window had few real returns of regulars, so this is a safety change (no bets on a returner's guessed minutes, no
Overs on teammates losing his shots) more than a proven edge. Grade it from `returning.json` as cases pile up
(a star back from a long absence, e.g. Haliburton/Kawhi, is the case it is built for).
