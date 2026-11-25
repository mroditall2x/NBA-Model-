"""REB / AST / RA team-play check (added 11/25 at Deon's request).

python3 reb_ast_check.py slate/MMDD YYYY-MM-DD
Writes slate/MMDD/reb_ast_check.csv for every
REB / AST / RA prop on board_all.csv. It never changes the card; the daily review reads it.

Board study (5,132 REB/AST/RA board props 10/28-11/23, research/reb_ast_study.md):
  - last-10 clear rate was the one check that held up in both halves of the sample.
    AST/RA Unders: cleared <=5 of 10 -> 57-61%, 6 of 10 -> 49-53%, 7+ -> 43%.
    REB Unders: <=6 of 10 -> 57%, 7+ -> 53%.
  - REB Unders vs a defense in the top third for rebounds allowed to his position: 53% vs 58-60% (lean).
  - AST Unders when teammates have shot cold lately (assists held down by misses): 52% vs 58% (lean).
Rules written to `under_check`: SKIP an AST/RA Under at 6+ of 10, a REB Under at 7+ of 10.
"""
import os, sys
import numpy as np, pandas as pd

D, DATE = sys.argv[1], sys.argv[2]
ROOT = os.environ.get('NBA_DATA', '/home/claude/nba/repo/nba')
asof = pd.Timestamp(DATE)


def read(kind, seasons):
    fs = [f'{ROOT}/{kind}/parquet/{kind}_{s}.parquet' for s in seasons]
    fs = [f for f in fs if os.path.exists(f)]
    return pd.concat([pd.read_parquet(f) for f in fs]) if fs else pd.DataFrame()


b = pd.read_csv(f'{D}/board_all.csv')
b = b[b.stat.isin(['REB', 'AST', 'RA'])].dropna(subset=['line']).drop_duplicates(['player', 'stat', 'line', 'side'])
pb = read('player_box', (2026, 2027))
tb = read('team_box', (2026, 2027))
if b.empty or pb.empty or tb.empty:
    print('reb_ast_check: nothing to do (no REB/AST/RA props or no box data)')
    sys.exit(0)

pb = pb[(pb.season_type == 2) & (~pb.did_not_play.fillna(False)) & (pb.minutes.fillna(0) > 0)].copy()
pb['date'] = pd.to_datetime(pb.game_date)
pb = pb[pb.date < asof].sort_values('date')
pb['pos'] = pb.athlete_position_abbreviation.fillna('F').str[0].map({'G': 'G', 'F': 'F', 'C': 'C', 'P': 'G', 'S': 'G'}).fillna('F')
pb['ra'] = pb.rebounds + pb.assists
tb = tb[tb.season_type == 2].copy()
lg_fg = tb.field_goals_made.sum() / tb.field_goals_attempted.sum()
pb = pb.merge(tb[['game_id', 'team_id', 'field_goals_made', 'field_goals_attempted']].rename(
    columns={'field_goals_made': 't_fgm', 'field_goals_attempted': 't_fga'}), on=['game_id', 'team_id'], how='left')
mate_fg = (pb.t_fgm - pb.field_goals_made) / (pb.t_fga - pb.field_goals_attempted).clip(lower=1)
pb['ast_adj'] = pb.assists * (lg_fg / mate_fg.clip(0.30, 0.65))

cur = pb[pb.season == pb.season.max()]
base = cur if len(cur) > 1500 else pb[pb.date >= asof - pd.Timedelta(days=200)]
lg36 = base.groupby('pos').rebounds.sum() / base.groupby('pos').minutes.sum() * 36
opp36 = base.groupby(['opponent_team_abbreviation', 'pos']).rebounds.sum() / \
    base.groupby(['opponent_team_abbreviation', 'pos']).minutes.sum() * 36
opp_ratio = (opp36 / opp36.index.get_level_values('pos').map(lg36).values).rename('opp_reb_pos')
# top third of rebounds allowed to the position (per position)
soft_cut = opp_ratio.groupby(level='pos').quantile(2 / 3)

# opponent tonight from the game string AWAY@HOME and the team column
col = {'REB': 'rebounds', 'AST': 'assists', 'RA': 'ra'}
rows = []
for r in b.itertuples():
    h = pb[pb.athlete_display_name == r.player]
    hs = h[h.season == pb.season.max()]
    l10 = hs.tail(10)
    away, home = str(r.game).split('@') if '@' in str(r.game) else (None, None)
    opp = home if r.team == away else away
    c = col[r.stat]
    n = len(l10)
    cleared = int((l10[c] > r.line).sum()) if n else np.nan
    pos = h.pos.iloc[-1] if len(h) else None
    ratio = opp_ratio.get((opp, pos), np.nan) if pos else np.nan
    soft_reb = bool(pos and not np.isnan(ratio) and ratio >= soft_cut.get(pos, np.inf))
    cold_mates = False
    if n:
        gap = (l10.ast_adj.sum() - l10.assists.sum()) / max(l10.minutes.sum(), 1) * (r.min if pd.notna(r.min) else l10.minutes.mean())
        cold_mates = gap >= 0.11
    check, note = '', []
    if r.side == 'Less' and n >= 5:
        limit = 7 if r.stat == 'REB' else 6
        scaled = cleared * 10 / n
        check = 'SKIP' if scaled >= limit else 'OK'
        if check == 'SKIP':
            note.append(f'clears this line often: {cleared} of {n}')
        if r.stat in ('REB', 'RA') and soft_reb:
            note.append(f'{opp} gives up a lot of REB to {pos}s (lean against Under)')
        if r.stat in ('AST', 'RA') and cold_mates:
            note.append('teammates shooting cold lately - assists due to bounce back (lean against Under)')
    elif n < 5:
        check = 'NO DATA'
    rows.append(dict(game=r.game, team=r.team, player=r.player, stat=r.stat, line=r.line, side=r.side,
                     l10_games=n, l10_cleared=cleared, l10_avg=round(l10[c].mean(), 2) if n else np.nan,
                     season_clear=round((hs[c] > r.line).mean(), 3) if len(hs) else np.nan,
                     pos=pos, opp=opp, opp_reb_pos=round(ratio, 3) if not np.isnan(ratio) else np.nan,
                     soft_reb_vs_pos=soft_reb, teammates_cold=cold_mates, under_check=check, note='; '.join(note),
                     summary=f'cleared {r.line:g} {r.stat} in {cleared} of last {n}' if n else 'no recent games'))
out = pd.DataFrame(rows)
out.insert(0, 'date', DATE)
out.to_csv(f'{D}/reb_ast_check.csv', index=False)
print(f'reb_ast_check: {len(out)} props, {int((out.under_check == "SKIP").sum())} Unders flagged SKIP')
