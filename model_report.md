# Model error report

_Updated 2026-11-20 01:15 CT. 319 graded picks with a model probability (2026-10-21 to 2026-11-19). Report only: nothing here changes the model._

**Overall:** model said 67.0%, picks hit 58.3% (186-133). z = -3.4 -> LIKELY REAL (model too high).

_How to read: `gap` = actual minus what the model said. `z` says whether the gap is bigger than luck would explain for that many picks. Only LIKELY REAL rows are worth acting on, and only after the out-of-sample check._

## 1. Calibration (is a 65% pick really 65%?)

| model p | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| <55% | 7 | 53.8% | 28.6% | -25.2% | -1.3 | watch (running cold) |
| 55-60% | 84 | 58.2% | 54.8% | -3.4% | -0.6 | noise |
| 60-65% | 105 | 62.4% | 45.7% | -16.7% | -3.5 | LIKELY REAL (model too high) |
| 65-70% | 40 | 67.0% | 50.0% | -17.0% | -2.3 | LIKELY REAL (model too high) |
| 70-80% | 16 | 73.1% | 62.5% | -10.6% | -1.0 | noise |
| 80%+ | 67 | 84.9% | 89.6% | +4.6% | 1.1 | watch (running hot) |

## 2. By stat

| stat | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| REB | 55 | 66.1% | 47.3% | -18.8% | -3.0 | LIKELY REAL (model too high) |
| 3PM | 62 | 63.3% | 46.8% | -16.6% | -2.7 | LIKELY REAL (model too high) |
| PA | 10 | 71.4% | 50.0% | -21.4% | -1.6 | watch (running cold) |
| AST | 93 | 65.1% | 60.2% | -4.9% | -1.0 | watch (running cold) |
| PTS | 8 | 73.5% | 62.5% | -11.0% | -0.7 | noise |
| SB | 13 | 75.0% | 69.2% | -5.8% | -0.5 | noise |
| PRA | 10 | 78.5% | 80.0% | +1.5% | 0.1 | noise |
| PR | 18 | 77.0% | 77.8% | +0.8% | 0.1 | noise |
| RA | 40 | 64.8% | 67.5% | +2.7% | 0.4 | noise |

## 3. Over vs Under

| side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Less | 212 | 62.4% | 48.1% | -14.3% | -4.3 | LIKELY REAL (model too high) |
| More | 102 | 75.5% | 77.5% | +1.9% | 0.5 | noise |

## 4. Stat + side

| stat_side | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| REB Less | 40 | 61.7% | 40.0% | -21.7% | -2.8 | LIKELY REAL (model too high) |
| 3PM Less | 50 | 62.8% | 46.0% | -16.8% | -2.5 | LIKELY REAL (model too high) |
| AST Less | 67 | 62.4% | 50.7% | -11.6% | -2.0 | watch (running cold) |
| 3PM More | 12 | 65.6% | 50.0% | -15.6% | -1.2 | watch (running cold) |
| REB More | 14 | 77.1% | 64.3% | -12.8% | -1.2 | watch (running cold) |
| PR More | 12 | 84.4% | 83.3% | -1.1% | -0.1 | noise |
| RA More | 10 | 71.5% | 70.0% | -1.5% | -0.1 | noise |
| PRA More | 8 | 82.5% | 87.5% | +5.0% | 0.4 | noise |
| RA Less | 28 | 60.8% | 64.3% | +3.5% | 0.4 | noise |
| AST More | 25 | 71.7% | 84.0% | +12.3% | 1.4 | watch (running hot) |
| SB More | 8 | 79.0% | 100.0% | +21.0% | 1.5 | watch (running hot) |

## 5. By tier

| tier | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| standard | 159 | 61.4% | 42.8% | -18.6% | -4.8 | LIKELY REAL (model too high) |
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
| 3-6.5 | 100 | 65.7% | 55.0% | -10.7% | -2.3 | LIKELY REAL (model too high) |
| 0.5-2.5 | 138 | 66.9% | 59.4% | -7.5% | -1.9 | watch (running cold) |
| 7-15.5 | 56 | 66.8% | 55.4% | -11.5% | -1.9 | watch (running cold) |
| 16+ | 25 | 72.7% | 72.0% | -0.7% | -0.1 | noise |

## 7. Projection bias (projected mean vs what happened)

_Positive miss = players beat the projection (model too low). Only players the model picked, so this leans toward whatever side the card favours._

| stat | n | avg_projection | avg_actual | miss | beat_projection | z | read |
|---|---|---|---|---|---|---|---|
| 3PM | 52 | 1.48 | 2.1 | +0.61 | 52% | 2.4 | LIKELY REAL (projects too low) |
| AST | 69 | 3.17 | 4.22 | +1.04 | 55% | 3.0 | LIKELY REAL (projects too low) |
| PA | 10 | 15.62 | 19.7 | +4.08 | 60% | 1.2 | watch (projects too low) |
| PR | 16 | 18.42 | 19.75 | +1.33 | 50% | 0.6 | noise |
| PRA | 10 | 21.8 | 24.3 | +2.50 | 60% | 1.2 | watch (projects too low) |
| PTS | 13 | 12.44 | 12.92 | +0.48 | 46% | 0.3 | noise |
| RA | 45 | 8.04 | 9.0 | +0.96 | 62% | 2.0 | LIKELY REAL (projects too low) |
| REB | 43 | 5.1 | 6.05 | +0.95 | 67% | 2.3 | LIKELY REAL (projects too low) |
| STL | 8 | 0.65 | 0.88 | +0.23 | 62% | 0.8 | noise |

## 8. Price check (card picks with a real book price)

- 130 priced picks: hit 40.8% vs average break-even 60.8% (average price -159).
- Model's own EV was **negative at the posted price on 73 of 130** (those went 34-39, -19.68u). The card ranks by chance, not price, so heavy-juice Unders (e.g. 3PM Unders at -180 to -240) make the card even when the price eats the edge.
- Picks the model rated +EV at the price went 19-38, -24.71u.

## 9. Players picked 4+ times

_Small samples: treat as a heads-up, not a rule._

| player | n | model_says | actual | gap | z | read |
|---|---|---|---|---|---|---|
| Tari Eason | 10 | 62.1% | 30.0% | -32.1% | -2.1 | LIKELY REAL (model too high) |
| Caleb Martin | 5 | 63.2% | 20.0% | -43.2% | -2.0 | LIKELY REAL (model too high) |
| Franz Wagner | 7 | 64.4% | 28.6% | -35.8% | -2.0 | watch (running cold) |
| Kyshawn George | 4 | 60.6% | 25.0% | -35.6% | -1.5 | watch (running cold) |
| Evan Mobley | 5 | 68.4% | 40.0% | -28.4% | -1.4 | watch (running cold) |
| Myles Turner | 6 | 68.3% | 50.0% | -18.3% | -1.0 | noise |
| Devin Booker | 7 | 70.6% | 57.1% | -13.4% | -0.8 | noise |
| P.J. Washington | 4 | 65.1% | 50.0% | -15.1% | -0.7 | noise |
| Kyle Kuzma | 5 | 67.5% | 60.0% | -7.5% | -0.4 | noise |
| Tre Johnson | 4 | 59.2% | 50.0% | -9.2% | -0.4 | noise |
| Naji Marshall | 4 | 60.7% | 50.0% | -10.7% | -0.4 | noise |
| Karl-Anthony Towns | 6 | 71.4% | 66.7% | -4.7% | -0.3 | noise |
| Isaiah Jackson | 8 | 62.1% | 62.5% | +0.4% | 0.0 | noise |
| Ace Bailey | 4 | 72.2% | 75.0% | +2.8% | 0.1 | noise |
| Brandin Podziemski | 4 | 60.6% | 75.0% | +14.4% | 0.6 | noise |
| Jayson Tatum | 4 | 78.4% | 100.0% | +21.6% | 1.1 | watch (running hot) |
| Dyson Daniels | 4 | 76.5% | 100.0% | +23.5% | 1.1 | watch (running hot) |
| Jamal Murray | 4 | 78.4% | 100.0% | +21.6% | 1.1 | watch (running hot) |
| Stephon Castle | 4 | 70.9% | 100.0% | +29.1% | 1.3 | watch (running hot) |
| Dillon Brooks | 8 | 68.3% | 100.0% | +31.7% | 2.0 | watch (running hot) |

## 10. Out-of-sample check (calibration)

Fit on the oldest 223 picks (2026-10-21 to 2026-11-08), tested on the newest 96 (2026-11-08 to 2026-11-19) that the fit never saw.

- Best extra shrink on the old picks: x0.95 (1.0 = keep the current probabilities).
- Log loss on the new picks: current 0.7433, with x0.95: 0.7397 (lower is better).
- **Does not pass: keep the current calibration.**

## Rules

- This report never changes the model. A change needs (1) a LIKELY REAL pattern, (2) a fix that holds up out-of-sample on picks it was not fit on, and (3) Deon's approval.
- Re-check after ~50 more graded picks; patterns under ~30 picks are usually noise.
