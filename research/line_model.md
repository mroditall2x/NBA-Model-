# Line model (11/06): why the line might be wrong tonight

`research/line_model.py` learns the gap between the closing line and the result, with the market line as an input.
Features are pre-game only: efficiency (season and last 10), pace, style (3PA / FT / OREB / TOV rates, fast-break
and paint points), rest and back-to-backs, and missing regulars. Training uses 2021-22 to 2024-25; each season is
tested only after training on the seasons before it. Closing lines from hoopR (through June 2026).

| Test season | Spreads, 1.5+ pt edge | Totals (ridge), 1.5+ pt edge | Totals (ridge), 3+ pt edge | Always Over |
|---|---|---|---|---|
| 2024-25 | 49-56% on small samples | 55.9% (467 bets) | 55.6% (126) | 52.5% |
| 2025-26 | 42-50% | 54.3% (409 bets) | 68.3% (82) | 49.3% |

Break-even at -110 is 52.4%.

- **Spreads:** no edge (XGBoost and ridge, about 50%). Not used.
- **Totals:** beat the line and the "always Over" baseline in both test seasons. Most picks are Overs (Overs 56.1% and 54.0%; Unders 54-57% on about 45 a season).
- **Factors:** the away team's fast-break points and the home defense allowing them push totals over the line. Missing players push the total over it (the market cuts too much). Home rest adds points.
- **Status:** tracking only. Two seasons, z about 1.7: promising, not proven. Needs this season's lines before any card use.

## This season, live check (11/12) - `research/totals_2027.py`
Trained on 2021-22..2025-26 closing lines, scored on the 88 2026-27 games we have a market total for (10/28-11/11, our last pull before tip).
| Model | All picks | 1.5+ pt edge | 3+ pt edge |
|---|---|---|---|
| Ridge | 43-45 (48.9%) | 13-13 (50.0%) | none |
| XGBoost | 39-49 (44.3%) | 17-24 (41.5%) | 5-8 |
Always Over 51.1%; the sim's total side 46.6%. Not beating the line yet. Early-season features lean on last season (rosters changed),
so keep tracking; re-run weekly and only consider units after ~250 games at 54%+ on the 1.5+ edge.
