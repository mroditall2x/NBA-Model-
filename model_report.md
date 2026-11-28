# Model error report

_Updated 2026-11-28 01:30 CT. 387 graded picks with a model probability (2026-10-21 to 2026-11-27). Report only: nothing here changes the model._

**Overall:** model said 65.2%, picks hit 57.1% (221-166). z = -3.4 -> LIKELY REAL (model too high).

_How to read: `gap` = actual minus what the model said. `z` says whether the gap is bigger than luck would explain for that many picks. Only LIKELY REAL rows are worth acting on, and only after the out-of-sample check._

## 1. Calibration (is a 65% pick really 65%?)

| model p | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| <55% | 16 | 54.1% | 31.2% | -22.8% | -1.8 | watch (running cold) |
| 55-60% | 143 | 57.9% | 54.5% | -3.3% | -0.8 | noise |
| 60-65% | 105 | 62.4% | 45.7% | -16.7% | -3.5 | LIKELY REAL (model too high) |
| 65-70% | 40 | 67.0% | 50.0% | -17.0% | -2.3 | LIKELY REAL (model too high) |
| 70-80% | 16 | 73.1% | 62.5% | -10.6% | -1.0 | noise |
| 80%+ | 67 | 84.9% | 89.6% | +4.6% | 1.1 | watch (running hot) |

## 2. By stat

| stat | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| REB | 69 | 64.1% | 50.7% | -13.4% | -2.4 | LIKELY REAL (model too high) |
| 3PM | 80 | 62.4% | 51.2% | -11.2% | -2.1 | LIKELY REAL (model too high) |
| PA | 10 | 71.4% | 50.0% | -21.4% | -1.6 | watch (running cold) |
| PTS | 14 | 65.6% | 50.0% | -15.6% | -1.3 | watch (running cold) |
| AST | 103 | 64.3% | 59.2% | -5.0% | -1.1 | watch (running cold) |
| RA | 57 | 62.3% | 57.9% | -4.4% | -0.7 | noise |
| SB | 13 | 75.0% | 69.2% | -5.8% | -0.5 | noise |
| PR | 21 | 73.6% | 71.4% | -2.2% | -0.2 | noise |
| PRA | 10 | 78.5% | 80.0% | +1.5% | 0.1 | noise |

## 3. Over vs Under

| side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Less | 266 | 61.1% | 48.1% | -13.0% | -4.4 | LIKELY REAL (model too high) |
| More | 116 | 73.6% | 75.9% | +2.2% | 0.6 | noise |

## 4. Stat + side

| stat_side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| REB Less | 54 | 60.4% | 46.3% | -14.1% | -2.1 | LIKELY REAL (model too high) |
| 3PM Less | 55 | 62.3% | 49.1% | -13.2% | -2.0 | LIKELY REAL (model too high) |
| AST Less | 77 | 61.6% | 50.6% | -10.9% | -2.0 | watch (running cold) |
| PTS Less | 8 | 56.9% | 25.0% | -31.9% | -1.8 | watch (running cold) |
| REB More | 14 | 77.1% | 64.3% | -12.8% | -1.2 | watch (running cold) |
| RA Less | 44 | 59.3% | 52.3% | -7.0% | -0.9 | noise |
| 3PM More | 25 | 62.7% | 56.0% | -6.7% | -0.7 | noise |
| PR Less | 8 | 55.8% | 50.0% | -5.8% | -0.3 | noise |
| PR More | 12 | 84.4% | 83.3% | -1.1% | -0.1 | noise |
| RA More | 11 | 70.2% | 72.7% | +2.6% | 0.2 | noise |
| PRA More | 8 | 82.5% | 87.5% | +5.0% | 0.4 | noise |
| AST More | 25 | 71.7% | 84.0% | +12.3% | 1.4 | watch (running hot) |
| SB More | 8 | 79.0% | 100.0% | +21.0% | 1.5 | watch (running hot) |

## 5. By tier

| tier | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| standard | 227 | 60.1% | 45.4% | -14.7% | -4.5 | LIKELY REAL (model too high) |
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
| 3-6.5 | 127 | 63.8% | 53.5% | -10.3% | -2.5 | LIKELY REAL (model too high) |
| 7-15.5 | 74 | 64.1% | 52.7% | -11.4% | -2.1 | LIKELY REAL (model too high) |
| 0.5-2.5 | 158 | 65.9% | 59.5% | -6.4% | -1.7 | watch (running cold) |
| 16+ | 28 | 70.7% | 71.4% | +0.8% | 0.1 | noise |

## 7. Projection bias (projected mean vs what happened)

_Positive miss = players beat the projection (model too low). Only players the model picked, so this leans toward whatever side the card favours._

| stat | n | avg_projection | avg_actual | miss | beat_projection | z | read |
|---|---|---|---|---|---|---|---|
| 3PM | 70 | 1.57 | 2.06 | +0.49 | 51% | 2.3 | LIKELY REAL (projects too low) |
| AST | 79 | 3.26 | 4.18 | +0.92 | 54% | 2.9 | LIKELY REAL (projects too low) |
| PA | 10 | 15.62 | 19.7 | +4.08 | 60% | 1.2 | watch (projects too low) |
| PR | 19 | 18.13 | 19.84 | +1.71 | 53% | 0.9 | noise |
| PRA | 10 | 21.8 | 24.3 | +2.50 | 60% | 1.2 | watch (projects too low) |
| PTS | 19 | 12.1 | 12.79 | +0.69 | 53% | 0.5 | noise |
| RA | 62 | 7.91 | 9.15 | +1.23 | 66% | 3.1 | LIKELY REAL (projects too low) |
| REB | 57 | 5.08 | 5.74 | +0.66 | 63% | 1.8 | watch (projects too low) |
| STL | 8 | 0.65 | 0.88 | +0.23 | 62% | 0.8 | noise |

## 8. Price check (card picks with a real book price)

- 198 priced picks: hit 44.4% vs average break-even 59.9% (average price -152).
- Model's own EV was **negative at the posted price on 130 of 198** (those went 63-67, -27.54u). The card ranks by chance, not price, so heavy-juice Unders (e.g. 3PM Unders at -180 to -240) make the card even when the price eats the edge.
- Picks the model rated +EV at the price went 25-43, -24.84u.

## 9. Players picked 4+ times

_Small samples: treat as a heads-up, not a rule._

| player | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Tari Eason | 10 | 62.1% | 30.0% | -32.1% | -2.1 | LIKELY REAL (model too high) |
| Caleb Martin | 5 | 63.2% | 20.0% | -43.2% | -2.0 | LIKELY REAL (model too high) |
| Franz Wagner | 7 | 64.4% | 28.6% | -35.8% | -2.0 | watch (running cold) |
| Jake LaRavia | 4 | 68.1% | 25.0% | -43.1% | -1.9 | watch (running cold) |
| Kyshawn George | 4 | 60.6% | 25.0% | -35.6% | -1.5 | watch (running cold) |
| Tristan da Silva | 4 | 59.8% | 25.0% | -34.8% | -1.4 | watch (running cold) |
| Evan Mobley | 5 | 68.4% | 40.0% | -28.4% | -1.4 | watch (running cold) |
| Myles Turner | 6 | 68.3% | 50.0% | -18.3% | -1.0 | noise |
| Jordan Poole | 5 | 58.3% | 40.0% | -18.3% | -0.8 | noise |
| P.J. Washington | 4 | 65.1% | 50.0% | -15.1% | -0.7 | noise |
| Naji Marshall | 6 | 59.1% | 50.0% | -9.1% | -0.5 | noise |
| De'Andre Hunter | 6 | 59.3% | 50.0% | -9.3% | -0.5 | noise |
| Tre Johnson | 4 | 59.2% | 50.0% | -9.2% | -0.4 | noise |
| Kenrich Williams | 4 | 60.2% | 50.0% | -10.2% | -0.4 | noise |
| Andrew Nembhard | 5 | 65.3% | 60.0% | -5.3% | -0.3 | noise |
| Karl-Anthony Towns | 6 | 71.4% | 66.7% | -4.7% | -0.3 | noise |
| Kevin Durant | 4 | 57.7% | 50.0% | -7.7% | -0.3 | noise |
| Ace Bailey | 6 | 68.1% | 66.7% | -1.4% | -0.1 | noise |
| Devin Booker | 9 | 68.2% | 66.7% | -1.5% | -0.1 | noise |
| Kyle Kuzma | 6 | 66.3% | 66.7% | +0.4% | 0.0 | noise |
| Isaiah Jackson | 8 | 62.1% | 62.5% | +0.4% | 0.0 | noise |
| Zach LaVine | 5 | 59.9% | 60.0% | +0.1% | 0.0 | noise |
| Jalen Brunson | 4 | 72.1% | 75.0% | +2.9% | 0.1 | noise |
| Brandin Podziemski | 4 | 60.6% | 75.0% | +14.4% | 0.6 | noise |
| Dyson Daniels | 4 | 76.5% | 100.0% | +23.5% | 1.1 | watch (running hot) |
| Jamal Murray | 4 | 78.4% | 100.0% | +21.6% | 1.1 | watch (running hot) |
| Stephon Castle | 4 | 70.9% | 100.0% | +29.1% | 1.3 | watch (running hot) |
| Jayson Tatum | 5 | 73.6% | 100.0% | +26.4% | 1.4 | watch (running hot) |
| Dillon Brooks | 8 | 68.3% | 100.0% | +31.7% | 2.0 | watch (running hot) |

## 10. Out-of-sample check (calibration)

Fit on the oldest 270 picks (2026-10-21 to 2026-11-13), tested on the newest 117 (2026-11-13 to 2026-11-27) that the fit never saw.

- Best extra shrink on the old picks: x0.9 (1.0 = keep the current probabilities).
- Log loss on the new picks: current 0.7220, with x0.9: 0.7180 (lower is better).
- **Does not pass: keep the current calibration.**

## Rules

- This report never changes the model. A change needs (1) a LIKELY REAL pattern, (2) a fix that holds up out-of-sample on picks it was not fit on, and (3) Deon's approval.
- Re-check after ~50 more graded picks; patterns under ~30 picks are usually noise.
