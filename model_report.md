# Model error report

_Updated 2026-11-10 20:27 CT. 239 graded picks with a model probability (2026-10-21 to 2026-11-09). Report only: nothing here changes the model._

**Overall:** model said 69.5%, picks hit 64.4% (154-85). z = -1.7 -> watch (running cold).

_How to read: `gap` = actual minus what the model said. `z` says whether the gap is bigger than luck would explain for that many picks. Only LIKELY REAL rows are worth acting on, and only after the out-of-sample check._

## 1. Calibration (is a 65% pick really 65%?)

| model p | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| <55% | 2 | 51.9% | 50.0% | -1.9% | -0.1 | noise |
| 55-60% | 40 | 58.2% | 77.5% | +19.3% | 2.5 | LIKELY REAL (model too low) |
| 60-65% | 77 | 62.7% | 45.5% | -17.3% | -3.1 | LIKELY REAL (model too high) |
| 65-70% | 37 | 67.1% | 45.9% | -21.2% | -2.7 | LIKELY REAL (model too high) |
| 70-80% | 16 | 73.1% | 62.5% | -10.6% | -1.0 | noise |
| 80%+ | 67 | 84.9% | 89.6% | +4.6% | 1.1 | watch (running hot) |

## 2. By stat

| stat | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| REB | 41 | 68.9% | 53.7% | -15.3% | -2.2 | LIKELY REAL (model too high) |
| 3PM | 34 | 65.7% | 55.9% | -9.8% | -1.2 | watch (running cold) |
| AST | 68 | 66.9% | 61.8% | -5.1% | -0.9 | noise |
| PA | 8 | 74.6% | 62.5% | -12.1% | -0.8 | noise |
| SB | 13 | 75.0% | 69.2% | -5.8% | -0.5 | noise |
| PRA | 10 | 78.5% | 80.0% | +1.5% | 0.1 | noise |
| PR | 17 | 78.3% | 82.4% | +4.1% | 0.4 | noise |
| RA | 31 | 66.8% | 74.2% | +7.4% | 0.9 | noise |

## 3. Over vs Under

| side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Less | 144 | 63.8% | 52.1% | -11.7% | -2.9 | LIKELY REAL (model too high) |
| More | 90 | 77.6% | 82.2% | +4.6% | 1.1 | watch (running hot) |

## 4. Stat + side

| stat_side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| AST Less | 44 | 63.5% | 50.0% | -13.5% | -1.9 | watch (running cold) |
| REB Less | 26 | 63.9% | 46.2% | -17.8% | -1.9 | watch (running cold) |
| 3PM Less | 31 | 64.1% | 51.6% | -12.4% | -1.4 | watch (running cold) |
| REB More | 14 | 77.1% | 64.3% | -12.8% | -1.2 | watch (running cold) |
| PR More | 12 | 84.4% | 83.3% | -1.1% | -0.1 | noise |
| RA More | 9 | 72.9% | 77.8% | +4.9% | 0.3 | noise |
| PRA More | 8 | 82.5% | 87.5% | +5.0% | 0.4 | noise |
| RA Less | 20 | 62.1% | 70.0% | +7.9% | 0.7 | noise |
| AST More | 23 | 72.7% | 82.6% | +9.9% | 1.1 | watch (running hot) |
| SB More | 8 | 79.0% | 100.0% | +21.0% | 1.5 | watch (running hot) |

## 5. By tier

| tier | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| standard | 79 | 63.3% | 45.6% | -17.7% | -3.3 | LIKELY REAL (model too high) |
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
| 7-15.5 | 49 | 68.2% | 57.1% | -11.1% | -1.7 | watch (running cold) |
| 0.5-2.5 | 94 | 69.8% | 63.8% | -5.9% | -1.3 | watch (running cold) |
| 3-6.5 | 74 | 68.4% | 66.2% | -2.1% | -0.4 | noise |
| 16+ | 22 | 74.8% | 77.3% | +2.4% | 0.3 | noise |

## 7. Projection bias (projected mean vs what happened)

_Positive miss = players beat the projection (model too low). Only players the model picked, so this leans toward whatever side the card favours._

| stat | n | avg_projection | avg_actual | miss | beat_projection | z | read |
|---|---|---|---|---|---|---|---|
| 3PM | 24 | 1.37 | 2.17 | +0.79 | 58% | 2.1 | LIKELY REAL (projects too low) |
| AST | 44 | 3.36 | 4.61 | +1.26 | 57% | 2.7 | LIKELY REAL (projects too low) |
| PA | 8 | 17.11 | 17.5 | +0.39 | 50% | 0.2 | noise |
| PR | 15 | 18.96 | 20.2 | +1.24 | 47% | 0.5 | noise |
| PRA | 10 | 21.8 | 24.3 | +2.50 | 60% | 1.2 | watch (projects too low) |
| PTS | 12 | 12.21 | 12.58 | +0.38 | 42% | 0.2 | noise |
| RA | 36 | 8.1 | 9.25 | +1.15 | 64% | 2.1 | LIKELY REAL (projects too low) |
| REB | 29 | 5.56 | 6.24 | +0.69 | 66% | 1.2 | watch (projects too low) |
| STL | 8 | 0.65 | 0.88 | +0.23 | 62% | 0.8 | noise |

## 8. Price check (card picks with a real book price)

- 50 priced picks: hit 42.0% vs average break-even 61.5% (average price -164).
- Model's own EV was **negative at the posted price on 21 of 50** (those went 9-12, -7.26u). The card ranks by chance, not price, so heavy-juice Unders (e.g. 3PM Unders at -180 to -240) make the card even when the price eats the edge.
- Picks the model rated +EV at the price went 12-17, -9.00u.

## 9. Players picked 4+ times

_Small samples: treat as a heads-up, not a rule._

| player | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Tari Eason | 7 | 62.4% | 28.6% | -33.9% | -1.9 | watch (running cold) |
| Franz Wagner | 6 | 65.8% | 33.3% | -32.5% | -1.7 | watch (running cold) |
| Evan Mobley | 5 | 68.4% | 40.0% | -28.4% | -1.4 | watch (running cold) |
| Myles Turner | 6 | 68.3% | 50.0% | -18.3% | -1.0 | noise |
| P.J. Washington | 4 | 65.1% | 50.0% | -15.1% | -0.7 | noise |
| Kyle Kuzma | 5 | 67.5% | 60.0% | -7.5% | -0.4 | noise |
| Isaiah Jackson | 8 | 62.1% | 62.5% | +0.4% | 0.0 | noise |
| Dyson Daniels | 4 | 76.5% | 100.0% | +23.5% | 1.1 | watch (running hot) |
| Jamal Murray | 4 | 78.4% | 100.0% | +21.6% | 1.1 | watch (running hot) |
| Stephon Castle | 4 | 70.9% | 100.0% | +29.1% | 1.3 | watch (running hot) |
| Dillon Brooks | 7 | 69.2% | 100.0% | +30.8% | 1.8 | watch (running hot) |

## 10. Out-of-sample check (calibration)

Fit on the oldest 167 picks (2026-10-21 to 2026-10-30), tested on the newest 72 (2026-10-30 to 2026-11-09) that the fit never saw.

- Best extra shrink on the old picks: x1.05 (1.0 = keep the current probabilities).
- Log loss on the new picks: current 0.7595, with x1.05: 0.7651 (lower is better).
- **Does not pass: keep the current calibration.**

## Rules

- This report never changes the model. A change needs (1) a LIKELY REAL pattern, (2) a fix that holds up out-of-sample on picks it was not fit on, and (3) Deon's approval.
- Re-check after ~50 more graded picks; patterns under ~30 picks are usually noise.
