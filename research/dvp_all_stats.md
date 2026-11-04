# Defense vs position, every prop stat (2024-25 + 2025-26, ~35,000 player-games, out-of-sample)
Player's own prior per-minute average vs what the opponent allowed to his position (G/F/C) in prior games.
| Stat | soft D | tough D | strength used |
|---|---|---|---|
| Points | +7% | -3% | 0.50 |
| Rebounds | +7% (C +9%) | -7% (C -10%) | 0.25 |
| Assists | +9% (G +19%) | -3% | 0.50 |
| Threes | +7% (G +10%) | mixed/noisy | 0.25 |
| Steals | +12% | -2% | 0.50 |
| Blocks | +26% | +5% | 0.50 |
| Off. rebounds | +11% | +1% | 0.25 (no OREB props in the odds feed yet) |
Applied in card_slate.py to every stat and combo (combos built from the adjusted parts). Both sides of each prop are priced for EV+ (ev_props.csv).
