# Model error report

_Updated 2026-11-14 22:11 CT. 281 graded picks with a model probability (2026-10-21 to 2026-11-14). Report only: nothing here changes the model._

**Overall:** model said 68.3%, picks hit 62.3% (175-106). z = -2.2 -> LIKELY REAL (model too high).

_How to read: `gap` = actual minus what the model said. `z` says whether the gap is bigger than luck would explain for that many picks. Only LIKELY REAL rows are worth acting on, and only after the out-of-sample check._

## 1. Calibration (is a 65% pick really 65%?)

| model p | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| <55% | 2 | 51.9% | 50.0% | -1.9% | -0.1 | noise |
| 55-60% | 51 | 58.4% | 70.6% | +12.2% | 1.8 | watch (running hot) |
| 60-65% | 105 | 62.4% | 45.7% | -16.7% | -3.5 | LIKELY REAL (model too high) |
| 65-70% | 40 | 67.0% | 50.0% | -17.0% | -2.3 | LIKELY REAL (model too high) |
| 70-80% | 16 | 73.1% | 62.5% | -10.6% | -1.0 | noise |
| 80%+ | 67 | 84.9% | 89.6% | +4.6% | 1.1 | watch (running hot) |

## 2. By stat

| stat | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| REB | 46 | 68.0% | 52.2% | -15.8% | -2.3 | LIKELY REAL (model too high) |
| 3PM | 50 | 64.4% | 50.0% | -14.4% | -2.1 | LIKELY REAL (model too high) |
| PA | 9 | 73.0% | 55.6% | -17.5% | -1.2 | watch (running cold) |
| AST | 85 | 65.8% | 63.5% | -2.3% | -0.5 | noise |
| SB | 13 | 75.0% | 69.2% | -5.8% | -0.5 | noise |
| PRA | 10 | 78.5% | 80.0% | +1.5% | 0.1 | noise |
| PR | 17 | 78.3% | 82.4% | +4.1% | 0.4 | noise |
| RA | 34 | 66.2% | 70.6% | +4.4% | 0.6 | noise |

## 3. Over vs Under

| side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Less | 182 | 63.3% | 51.1% | -12.2% | -3.4 | LIKELY REAL (model too high) |
| More | 94 | 76.9% | 81.9% | +5.0% | 1.2 | watch (running hot) |

## 4. Stat + side

| stat_side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| 3PM Less | 46 | 63.3% | 45.7% | -17.7% | -2.5 | LIKELY REAL (model too high) |
| REB Less | 31 | 63.3% | 45.2% | -18.1% | -2.1 | LIKELY REAL (model too high) |
| AST Less | 59 | 63.1% | 54.2% | -8.8% | -1.4 | watch (running cold) |
| REB More | 14 | 77.1% | 64.3% | -12.8% | -1.2 | watch (running cold) |
| RA More | 10 | 71.5% | 70.0% | -1.5% | -0.1 | noise |
| PR More | 12 | 84.4% | 83.3% | -1.1% | -0.1 | noise |
| PRA More | 8 | 82.5% | 87.5% | +5.0% | 0.4 | noise |
| RA Less | 22 | 61.9% | 68.2% | +6.3% | 0.6 | noise |
| AST More | 25 | 71.7% | 84.0% | +12.3% | 1.4 | watch (running hot) |
| SB More | 8 | 79.0% | 100.0% | +21.0% | 1.5 | watch (running hot) |

## 5. By tier

| tier | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| standard | 121 | 62.6% | 47.1% | -15.5% | -3.5 | LIKELY REAL (model too high) |
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
| 7-15.5 | 52 | 67.7% | 55.8% | -11.9% | -1.9 | watch (running cold) |
| 0.5-2.5 | 123 | 67.9% | 61.8% | -6.1% | -1.5 | watch (running cold) |
| 3-6.5 | 83 | 67.5% | 62.7% | -4.8% | -1.0 | noise |
| 16+ | 23 | 74.2% | 78.3% | +4.0% | 0.5 | noise |

## 7. Projection bias (projected mean vs what happened)

_Positive miss = players beat the projection (model too low). Only players the model picked, so this leans toward whatever side the card favours._

| stat | n | avg_projection | avg_actual | miss | beat_projection | z | read |
|---|---|---|---|---|---|---|---|
| 3PM | 40 | 1.39 | 2.28 | +0.88 | 60% | 3.1 | LIKELY REAL (projects too low) |
| AST | 61 | 3.13 | 4.07 | +0.94 | 52% | 2.4 | LIKELY REAL (projects too low) |
| PA | 9 | 15.71 | 16.89 | +1.18 | 56% | 0.6 | noise |
| PR | 15 | 18.96 | 20.2 | +1.24 | 47% | 0.5 | noise |
| PRA | 10 | 21.8 | 24.3 | +2.50 | 60% | 1.2 | watch (projects too low) |
| PTS | 12 | 12.21 | 12.58 | +0.38 | 42% | 0.2 | noise |
| RA | 39 | 8.28 | 9.38 | +1.11 | 64% | 2.1 | LIKELY REAL (projects too low) |
| REB | 34 | 5.41 | 6.12 | +0.71 | 65% | 1.4 | watch (projects too low) |
| STL | 8 | 0.65 | 0.88 | +0.23 | 62% | 0.8 | noise |

## 8. Price check (card picks with a real book price)

- 92 priced picks: hit 45.7% vs average break-even 61.8% (average price -166).
- Model's own EV was **negative at the posted price on 48 of 92** (those went 26-22, -8.11u). The card ranks by chance, not price, so heavy-juice Unders (e.g. 3PM Unders at -180 to -240) make the card even when the price eats the edge.
- Picks the model rated +EV at the price went 16-28, -17.10u.

## 9. Players picked 4+ times

_Small samples: treat as a heads-up, not a rule._

| player | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Tari Eason | 10 | 62.1% | 30.0% | -32.1% | -2.1 | LIKELY REAL (model too high) |
| Caleb Martin | 5 | 63.2% | 20.0% | -43.2% | -2.0 | LIKELY REAL (model too high) |
| Franz Wagner | 6 | 65.8% | 33.3% | -32.5% | -1.7 | watch (running cold) |
| Evan Mobley | 5 | 68.4% | 40.0% | -28.4% | -1.4 | watch (running cold) |
| Myles Turner | 6 | 68.3% | 50.0% | -18.3% | -1.0 | noise |
| P.J. Washington | 4 | 65.1% | 50.0% | -15.1% | -0.7 | noise |
| Kyle Kuzma | 5 | 67.5% | 60.0% | -7.5% | -0.4 | noise |
| Devin Booker | 4 | 78.5% | 75.0% | -3.5% | -0.2 | noise |
| Isaiah Jackson | 8 | 62.1% | 62.5% | +0.4% | 0.0 | noise |
| Ace Bailey | 4 | 72.2% | 75.0% | +2.8% | 0.1 | noise |
| Brandin Podziemski | 4 | 60.6% | 75.0% | +14.4% | 0.6 | noise |
| Dyson Daniels | 4 | 76.5% | 100.0% | +23.5% | 1.1 | watch (running hot) |
| Jamal Murray | 4 | 78.4% | 100.0% | +21.6% | 1.1 | watch (running hot) |
| Stephon Castle | 4 | 70.9% | 100.0% | +29.1% | 1.3 | watch (running hot) |
| Dillon Brooks | 8 | 68.3% | 100.0% | +31.7% | 2.0 | watch (running hot) |

## 10. Out-of-sample check (calibration)

Fit on the oldest 196 picks (2026-10-21 to 2026-11-05), tested on the newest 85 (2026-11-05 to 2026-11-14) that the fit never saw.

- Best extra shrink on the old picks: x1.0 (1.0 = keep the current probabilities).
- Log loss on the new picks: current 0.7566, with x1.0: 0.7566 (lower is better).
- **Does not pass: keep the current calibration.**

## Rules

- This report never changes the model. A change needs (1) a LIKELY REAL pattern, (2) a fix that holds up out-of-sample on picks it was not fit on, and (3) Deon's approval.
- Re-check after ~50 more graded picks; patterns under ~30 picks are usually noise.
