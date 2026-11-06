# Current-season data and with/without teammates (11/06)

**Bug found:** `slate1021.py` and `card_slate.py` loaded 2025 and 2026 only, so player and team rates ignored all 2026-27 games.
Traded players stayed flagged "new team" all season for the same reason.

**Replay, same lines and minutes, 6 slates (10/28-11/04), 1,570 props, no data from the slate date or later**

| Version | Right side | Log-loss | Card |
|---|---|---|---|
| Old (2025-26) | 53.2% | 0.6993 | 19-15 (55.9%) |
| With 2026-27 | 52.9% | 0.6979 | 26-16 (61.9%) |

Prop accuracy is about flat; AST and 3PM errors improve a little. The card gain is a small sample, partly from players no longer flagged.

**With/without teammates, 500 random 2025-26 games**
- Blanket per-player adjustment on AST, DREB, 2PA and 3PA: projections got worse at every stat (for example AST MAE 1.430 -> 1.449), even with heavy shrinkage. Mostly noise. The sim already moves a missing player's share to teammates.
- Top remaining passer when an 18%+ assist teammate is out: small gain (121 player-games, MAE 2.02 -> 1.97).
- With 2026-27 data in, that case added nothing in the replay (same card, same log-loss), because recent form already includes the absence. Not shipped.

Matchup strength stays 0 in `card_slate.py` (replay: ON 98-96, OFF 84-68).
