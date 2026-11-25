# REB / AST / RA team-play study (11/25)

Run: `python3 research/reb_ast_research.py <repo> <hoopR nba data dir> out.csv`
Sample: 5,132 REB/AST/RA props on board_all.csv, 10/28-11/23 (standard lines, no goblins/demons), graded with ESPN box scores.
Every feature uses games before that date only.

## Model Unders by how often the player cleared tonight's line in his last 10

| | <=5 of 10 | 6 of 10 | 7+ of 10 |
|---|---|---|---|
| AST Under | 56.6% (693) | 49.2% (126) | 43.7% (87) |
| RA Under  | 60.7% (758) | 52.5% (160) | 42.6% (122) |
| REB Under | 57.6% (844) | 57.1% (191) | 53.0% (100) |

Held in both halves: 10/28-11/11 60.3 / 57.3 / 50.4%, 11/12-11/23 56.6 / 50.6 / 43.0% (all three stats).

## Other checks (Unders)
- REB Unders vs a defense in the top third of rebounds allowed to his position (per 36, vs league): 53.1% vs 58.0-59.9%. Lean.
- AST Unders when teammates shot cold lately (assists x league FG% / teammates' FG% above real assists): 51.8% vs 58.4%. Lean ("potential assist" proxy; NBA.com tracking data was not reachable).
- REB Unders on players with few rebound chances (team + opp misses x min/48, bottom third): 61.3% vs 54.5%.
- Opponent assists allowed (per game or to the position): noise / wrong direction.
- Model edge size (model - market): no relationship (edge 0-5% 56.3%, 15%+ 53.2%).

## Projections
Board-wide the sim is not biased low on REB/AST/RA (actual - sim: REB -0.15, AST +0.08, RA -0.09; MAE about equal to last-10 average).
The "projects too low" rows in model_report.md come from the picks the card selects (Unders where the sim sits below the line).

## In the pipeline
`reb_ast_check.py` (run_day.py, after style.py) writes `slate/MMDD/reb_ast_check.csv`: l10_cleared / l10_games, opp_reb_pos,
soft_reb_vs_pos, teammates_cold, under_check (SKIP = AST/RA Under at 6+ of 10, REB Under at 7+ of 10), note. It never changes the card.
