"""3PM volume backtest (11/14).  python3 research/threes_volume.py
For every graded slate: projected 3PA (player's pre-game per-minute 3PA rate, same shrinkage as nba_sim,
x the board's model minutes) vs the actual 3PA/3PM from hoopR.  Tests the volume rules:
  no 3PM Under 1.5 at proj 3PA >= 5, no Under 2.5 at proj 3PA >= 7, Over 1.5 candidates at proj 3PA >= 6."""
import glob, os, sys, warnings
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
warnings.filterwarnings('ignore')
import nba_sim as S
from slate_names import norm

p, t = S.load((2025, 2026, 2027)); pri = S.pos_priors(p)
p['k'] = p.name.map(norm)
pid_of = p.sort_values('game_date').groupby('k').pid.last().to_dict()
imp = lambda o: (-o) / (-o + 100) if o < 0 else 100 / (o + 100)
rows = []
for d in sorted(glob.glob('slate/1[01][0-9][0-9]')):
    md = d[-4:]; date = pd.Timestamp(f"{2026 if int(md[:2]) >= 9 else 2027}-{md[:2]}-{md[2:]}")
    bf = f'{d}/board_all.csv'
    if not os.path.exists(bf): continue
    B = pd.read_csv(bf); B = B[(B.stat == '3PM') & B.type.isin(['PP standard', 'book line'])]
    act = p[p.game_date == date].set_index('k')
    if not len(B) or not len(act): continue
    prof = {}
    for r in B.itertuples():
        k = norm(r.player)
        if k not in act.index or k not in pid_of: continue
        a = act.loc[k]
        if isinstance(a, pd.DataFrame): a = a.iloc[0]
        if a['min'] <= 0: continue
        if k not in prof: prof[k] = S.player_profile(p, pid_of[k], date, pri)
        f = prof[k]
        last10 = p[(p.k == k) & (p.game_date < date)].tail(10)
        try:
            pm, pu = imp(int(r.o)), imp(int(r.u)); mo = pm / (pm + pu)
        except Exception:
            mo = r.market if r.side == 'More' else 1 - r.market
        rows.append(dict(date=md, game=r.game, player=r.player, line=r.line, model_mean=r.mean, model_min=r.min,
                         p_over=getattr(r, 'p_over', r.model if r.side == 'More' else 1 - r.model), mkt_over=mo, side=r.side, model=r.model,
                         rate3a=f['fg3a'], p3=f['p3'], proj3pa=f['fg3a'] * r.min, l10_3pa=last10.fg3a.mean() if len(last10) else np.nan,
                         act3pa=a.fg3a, act3pm=a.fg3m, act_min=a['min']))
R = pd.DataFrame(rows).drop_duplicates(['date', 'player', 'line'])
R['over'] = R.act3pm > R.line
R.to_csv('research/threes_volume.csv', index=False)
print(f"{len(R)} 3PM props, {R.date.nunique()} slates ({R.date.min()}-{R.date.max()})\n")
print('projected 3PA (rate x model min):', round(R.proj3pa.mean(), 2), ' last-10 avg:', round(R.l10_3pa.mean(), 2), ' actual:', round(R.act3pa.mean(), 2))
print('implied 3P% in model mean (mean/proj3pa):', round(R.model_mean.sum() / R.proj3pa.sum(), 3), ' actual 3P%:', round(R.act3pm.sum() / R.act3pa.sum(), 3))
print('corr proj3pa~act3pa', round(R.proj3pa.corr(R.act3pa), 3), ' l10~act', round(R.l10_3pa.corr(R.act3pa), 3), '\n')
R['bucket'] = pd.cut(R.proj3pa, [0, 3, 4, 5, 6, 7, 20], right=False)
for L in (0.5, 1.5, 2.5, 3.5):
    x = R[R.line == L]
    if not len(x): continue
    g = x.groupby('bucket', observed=True).agg(n=('over', 'size'), over_hit=('over', 'mean'), model_p_over=('p_over', 'mean'),
                                               mkt_p_over=('mkt_over', 'mean'), act3pa=('act3pa', 'mean'), proj3pa=('proj3pa', 'mean')).round(3)
    print(f'line {L}  (Over hit rate by projected 3PA)'); print(g.to_string(), '\n')
