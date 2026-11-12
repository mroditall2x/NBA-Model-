"""Totals line model on THIS season (2026-27), live check - 11/12.
Trains research/line_model.py's totals model (ridge + XGBoost, FEATS_OU) on 2021-22..2025-26 closing lines, then scores every
2026-27 game we have a market total for (slate/MMDD/games.csv mkt_total = our last pull before tip, ~close) against the final.
python3 research/totals_2027.py   (needs NBA_DATA = hoopR repo/nba with team_box, player_box 2022-2027 and betting_lines)
Writes research/totals_2027_games.csv (one row per game: line, model gap, pick, result)."""
import os, sys, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import line_model as LM

t = LM.team_games(); r = LM.rolling(t)
r = r.merge(LM.availability(), on=['game_id', 'team_id'], how='left').fillna({'miss_val': 0, 'miss_min': 0})
h = r[r.team_home_away == 'home'].drop(columns='team_home_away'); a = r[r.team_home_away == 'away'].drop(columns=['team_home_away', 'season', 'date'])
g = h.merge(a, on='game_id', suffixes=('_h', '_a'))
g['total'] = g.team_score_h + g.opponent_team_score_h
L = pd.read_parquet(f'{LM.ROOT}/betting_lines/closing_lines_odds_api.parquet')[['game_id', 'over_under']]
L['game_id'] = L.game_id.astype(g.game_id.dtype)
# this season's lines from our own slate pulls
rows = []
for f in sorted(glob.glob('slate/1[01][0-9][0-9]/games.csv')) + sorted(glob.glob('slate/0[1-6][0-9][0-9]/games.csv')):
    md = f.split('/')[1]; yr = 2026 if int(md[:2]) >= 9 else 2027
    x = pd.read_csv(f)
    for q in x.itertuples():
        aw, hm = q.game.split('@')
        rows.append(dict(date=pd.Timestamp(f'{yr}-{md[:2]}-{md[2:]}'), team_abbreviation_h=hm, team_abbreviation_a=aw, line_now=q.mkt_total, sim_total=q.model_total))
S = pd.DataFrame(rows).drop_duplicates(['date', 'team_abbreviation_h'], keep='last')
g['date'] = pd.to_datetime(g.date).dt.normalize()
cur = g[g.season == 2027].merge(S, on=['date', 'team_abbreviation_h', 'team_abbreviation_a'])
cur['over_under'] = cur.line_now
hist = g[g.season < 2027].merge(L, on='game_id').dropna(subset=['over_under'])
for d in (hist, cur):
    d['ou'] = d.total - d.over_under
F = LM.FEATS_OU
import xgboost as xgb
from sklearn.linear_model import Ridge
Xtr = hist[F].fillna(0); mu, sd = Xtr.mean(), Xtr.std()
rg = Ridge(alpha=50).fit((Xtr - mu) / sd, hist.ou)
xm = xgb.XGBRegressor(**LM.PARAMS).fit(Xtr, hist.ou)
Xc = cur[F].fillna(0)
cur['ridge_gap'] = rg.predict((Xc - mu) / sd); cur['xgb_gap'] = xm.predict(Xc)
cur = cur[cur.ou != 0].copy()
out = []
for name in ('ridge_gap', 'xgb_gap'):
    for th in (0, 1.5, 3):
        k = cur[name].abs() >= th
        w = (np.sign(cur.loc[k, name]) == np.sign(cur.loc[k, 'ou'])).mean() if k.any() else np.nan
        ov = cur.loc[k & (cur[name] > 0)]; un = cur.loc[k & (cur[name] < 0)]
        out.append(dict(model=name.split('_')[0], edge_pts=th, bets=int(k.sum()), win=round(w, 3),
                        overs=f"{int((ov.ou > 0).sum())}-{int((ov.ou < 0).sum())}", unders=f"{int((un.ou < 0).sum())}-{int((un.ou > 0).sum())}"))
print(len(cur), 'games', cur.date.min().date(), '->', cur.date.max().date())
print(pd.DataFrame(out).to_string(index=False))
print('always Over:', round((cur.ou > 0).mean(), 3), '| sim (games.csv model_total) side:',
      round((np.sign(cur.sim_total - cur.line_now) == np.sign(cur.ou)).mean(), 3), '| break-even at -110: 52.4%')
cur['pick'] = np.where(cur.ridge_gap > 0, 'Over', 'Under'); cur['hit'] = np.sign(cur.ridge_gap) == np.sign(cur.ou)
cur[['date', 'team_abbreviation_a', 'team_abbreviation_h', 'line_now', 'total', 'ridge_gap', 'xgb_gap', 'sim_total', 'pick', 'hit']].round(2) \
    .to_csv('research/totals_2027_games.csv', index=False)
