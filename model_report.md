# Model error report

_Updated 2026-11-17 01:15 CT. 296 graded picks with a model probability (2026-10-21 to 2026-11-16). Report only: nothing here changes the model._

**Overall:** model said 67.7%, picks hit 60.8% (180-116). z = -2.6 -> LIKELY REAL (model too high).

_How to read: `gap` = actual minus what the model said. `z` says whether the gap is bigger than luck would explain for that many picks. Only LIKELY REAL rows are worth acting on, and only after the out-of-sample check._

## 1. Calibration (is a 65% pick really 65%?)

| model p | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| <55% | 3 | 52.7% | 66.7% | +13.9% | 0.5 | noise |
| 55-60% | 65 | 58.3% | 61.5% | +3.2% | 0.5 | noise |
| 60-65% | 105 | 62.4% | 45.7% | -16.7% | -3.5 | LIKELY REAL (model too high) |
| 65-70% | 40 | 67.0% | 50.0% | -17.0% | -2.3 | LIKELY REAL (model too high) |
| 70-80% | 16 | 73.1% | 62.5% | -10.6% | -1.0 | noise |
| 80%+ | 67 | 84.9% | 89.6% | +4.6% | 1.1 | watch (running hot) |

## 2. By stat

| stat | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| 3PM | 54 | 64.0% | 48.1% | -15.9% | -2.5 | LIKELY REAL (model too high) |
| REB | 49 | 67.3% | 51.0% | -16.3% | -2.5 | LIKELY REAL (model too high) |
| PA | 9 | 73.0% | 55.6% | -17.5% | -1.2 | watch (running cold) |
| AST | 88 | 65.6% | 62.5% | -3.1% | -0.6 | noise |
| SB | 13 | 75.0% | 69.2% | -5.8% | -0.5 | noise |
| PRA | 10 | 78.5% | 80.0% | +1.5% | 0.1 | noise |
| RA | 39 | 65.0% | 66.7% | +1.7% | 0.2 | noise |
| PR | 17 | 78.3% | 82.4% | +4.1% | 0.4 | noise |

## 3. Over vs Under

| side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Less | 194 | 62.9% | 50.5% | -12.4% | -3.6 | LIKELY REAL (model too high) |
| More | 97 | 76.3% | 79.4% | +3.0% | 0.7 | noise |

## 4. Stat + side

| stat_side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| 3PM Less | 47 | 63.2% | 46.8% | -16.4% | -2.3 | LIKELY REAL (model too high) |
| REB Less | 34 | 62.7% | 44.1% | -18.6% | -2.3 | LIKELY REAL (model too high) |
| AST Less | 62 | 62.8% | 53.2% | -9.6% | -1.6 | watch (running cold) |
| REB More | 14 | 77.1% | 64.3% | -12.8% | -1.2 | watch (running cold) |
| RA More | 10 | 71.5% | 70.0% | -1.5% | -0.1 | noise |
| PR More | 12 | 84.4% | 83.3% | -1.1% | -0.1 | noise |
| RA Less | 27 | 61.0% | 63.0% | +2.0% | 0.2 | noise |
| PRA More | 8 | 82.5% | 87.5% | +5.0% | 0.4 | noise |
| AST More | 25 | 71.7% | 84.0% | +12.3% | 1.4 | watch (running hot) |
| SB More | 8 | 79.0% | 100.0% | +21.0% | 1.5 | watch (running hot) |

## 5. By tier

| tier | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| standard | 136 | 62.1% | 45.6% | -16.5% | -4.0 | LIKELY REAL (model too high) |
| extra-line | 15 | 65.6% | 46.7% | -19.0% | -1.6 | watch (running cold) |
| 62-65 | 14 | 63.4% | 50.0% | -13.4% | -1.0 | watch (running cold) |
| 65-70 | 14 | 67.4% | 57.1% | -10.2% | -0.8 | noise |
| goblin | 43 | 85.1% | 83.7% | -1.4% | -0.3 | noise |
| 70+ | 11 | 73.7% | 81.8% | +8.1% | 0.6 | noise |
| card-standard | 8 | 62.4% | 75.0% | +12.6% | 0.7 | noise |
| extra-goblin | 11 | 82.0% | 100.0% | +18.0% | 1.6 | watch (running hot) |
| four | 33 | 62.9% | 75.8% | +12.8% | 1.6 | watch (running hot) |

## 6. By line size

| line_size | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| 0.5-2.5 | 127 | 67.6% | 60.6% | -7.0% | -1.7 | watch (running cold) |
| 7-15.5 | 53 | 67.4% | 56.6% | -10.8% | -1.7 | watch (running cold) |
| 3-6.5 | 93 | 66.4% | 59.1% | -7.3% | -1.5 | watch (running cold) |
| 16+ | 23 | 74.2% | 78.3% | +4.0% | 0.5 | noise |

## 7. Projection bias (projected mean vs what happened)

_Positive miss = players beat the projection (model too low). Only players the model picked, so this leans toward whatever side the card favours._

| stat | n | avg_projection | avg_actual | miss | beat_projection | z | read |
|---|---|---|---|---|---|---|---|
| 3PM | 44 | 1.44 | 2.11 | +0.68 | 55% | 2.4 | LIKELY REAL (projects too low) |
| AST | 64 | 3.13 | 4.08 | +0.95 | 53% | 2.6 | LIKELY REAL (projects too low) |
| PA | 9 | 15.71 | 16.89 | +1.18 | 56% | 0.6 | noise |
| PR | 15 | 18.96 | 20.2 | +1.24 | 47% | 0.5 | noise |
| PRA | 10 | 21.8 | 24.3 | +2.50 | 60% | 1.2 | watch (projects too low) |
| PTS | 12 | 12.21 | 12.58 | +0.38 | 42% | 0.2 | noise |
| RA | 44 | 7.93 | 8.95 | +1.02 | 64% | 2.1 | LIKELY REAL (projects too low) |
| REB | 37 | 5.31 | 5.97 | +0.66 | 65% | 1.4 | watch (projects too low) |
| STL | 8 | 0.65 | 0.88 | +0.23 | 62% | 0.8 | noise |

## 8. Price check (card picks with a real book price)

- 107 priced picks: hit 43.9% vs average break-even 61.3% (average price -163).
- Model's own EV was **negative at the posted price on 55 of 107** (those went 29-26, -9.98u). The card ranks by chance, not price, so heavy-juice Unders (e.g. 3PM Unders at -180 to -240) make the card even when the price eats the edge.
- Picks the model rated +EV at the price went 18-34, -21.44u.

## 9. Players picked 4+ times

_Small samples: treat as a heads-up, not a rule._

| player | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Tari Eason | 10 | 62.1% | 30.0% | -32.1% | -2.1 | LIKELY REAL (model too high) |
| Caleb Martin | 5 | 63.2% | 20.0% | -43.2% | -2.0 | LIKELY REAL (model too high) |
| Franz Wagner | 6 | 65.8% | 33.3% | -32.5% | -1.7 | watch (running cold) |
| Kyshawn George | 4 | 60.6% | 25.0% | -35.6% | -1.5 | watch (running cold) |
| Evan Mobley | 5 | 68.4% | 40.0% | -28.4% | -1.4 | watch (running cold) |
| Devin Booker | 6 | 72.3% | 50.0% | -22.3% | -1.3 | watch (running cold) |
| Myles Turner | 6 | 68.3% | 50.0% | -18.3% | -1.0 | noise |
| P.J. Washington | 4 | 65.1% | 50.0% | -15.1% | -0.7 | noise |
| Kyle Kuzma | 5 | 67.5% | 60.0% | -7.5% | -0.4 | noise |
| Isaiah Jackson | 8 | 62.1% | 62.5% | +0.4% | 0.0 | noise |
| Ace Bailey | 4 | 72.2% | 75.0% | +2.8% | 0.1 | noise |
| Brandin Podziemski | 4 | 60.6% | 75.0% | +14.4% | 0.6 | noise |
| Karl-Anthony Towns | 4 | 77.8% | 100.0% | +22.2% | 1.1 | watch (running hot) |
| Jamal Murray | 4 | 78.4% | 100.0% | +21.6% | 1.1 | watch (running hot) |
| Dyson Daniels | 4 | 76.5% | 100.0% | +23.5% | 1.1 | watch (running hot) |
| Stephon Castle | 4 | 70.9% | 100.0% | +29.1% | 1.3 | watch (running hot) |
| Dillon Brooks | 8 | 68.3% | 100.0% | +31.7% | 2.0 | watch (running hot) |

## 10. Out-of-sample check (calibration)

Fit on the oldest 207 picks (2026-10-21 to 2026-11-06), tested on the newest 89 (2026-11-07 to 2026-11-16) that the fit never saw.

- Best extra shrink on the old picks: x1.0 (1.0 = keep the current probabilities).
- Log loss on the new picks: current 0.7487, with x1.0: 0.7487 (lower is better).
- **Does not pass: keep the current calibration.**

## Rules

- This report never changes the model. A change needs (1) a LIKELY REAL pattern, (2) a fix that holds up out-of-sample on picks it was not fit on, and (3) Deon's approval.
- Re-check after ~50 more graded picks; patterns under ~30 picks are usually noise.
