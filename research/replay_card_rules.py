"""Replay the live card rule (main) vs the 11/12 side-calibration + market rule on the saved boards.
python3 research/replay_card_rules.py   -> prints record / units / ROI per rule, in-sample (design window) vs out-of-sample.
Board = slate/MMDD/board_all.csv as committed (last pre-tip build); actuals = slate/MMDD/espn_box.csv.
Flat 1u risk; price paid = best of the book price for our side and pick'em (-119)."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from slate_names import norm

DAYS = ['1104','1105','1106','1107','1108','1109','1110','1111','1112','1113','1114']
DESIGN_END = '1111'          # the 11/12 rule was fit on 10/31-11/11 -> 11/12 on is out-of-sample

def base_ok(B):
    B = B.copy(); B['flags'] = B['flags'].fillna('')
    B['adj'] = 0.5 + 0.6 * (B.model - 0.5)
    ok = (B['gap'].abs() <= 4) & ~B['flags'].str.contains('new team|small|unclear')
    ok &= ~((B.side == 'Less') & (B['gap'] > 2)) & ~((B.side == 'More') & (B['gap'] < -2))
    ok &= ~((B.side == 'Less') & B['flags'].str.contains('role up')) & ~((B.side == 'More') & B['flags'].str.contains('role down'))
    ok &= ~((B.side == 'More') & B['flags'].str.contains('teammate back'))
    if 'vol3' not in B: B['vol3'] = np.nan
    ok &= ~((B.stat == '3PM') & (B.side == 'Less') & (((B.line == 1.5) & (B.vol3 >= 4.5)) | ((B.line == 2.5) & (B.vol3 >= 6.5))))
    return B, ok

def pool(B, ok):
    return B[ok & B.type.isin(['PP standard', 'book line']) & ~B.stat.isin(['STL', 'BLK', 'STL+BLK'])].copy()

def rule_main(B):
    B, ok = base_ok(B); s = pool(B, ok)
    s = s[(s.adj >= 0.58) & (s.edge >= 0.05) & ~((s['min'] >= 35) & (s.side == 'Less') & (s.adj < 0.62))]
    s = s[~((s.stat == 'PTS') & (s.side == 'Less') & (s.adj < 0.60))]
    g = B[ok & (B.type == 'goblin') & (B.model >= 0.84)]
    return pd.concat([s.assign(tier='standard', p=s.adj), g.assign(tier='goblin', p=g.model)])

def rule_cal(B):
    B, ok = base_ok(B); s = pool(B, ok)
    s['cal'] = np.where(s.side == 'Less', np.where(s.adj > 0.62, 0.62 - (s.adj - 0.62), s.adj), 0.5 + 0.25 * (s.model - 0.5))
    s['px'] = np.where((s.o == -119) & (s.u == -119), -119, np.where(s.side == 'More', s.o, s.u))
    s['q'] = 0.5 * s.cal + 0.5 * s.market
    s = s[(s.o.abs() >= 100) & (s.u.abs() >= 100)]
    s = s[(s.cal >= 0.56) & (s.market >= 0.50) & (s.px >= -150)]
    g = B[ok & (B.type == 'goblin') & (B.model >= 0.84)]
    return pd.concat([s.assign(tier='standard', p=s.q), g.assign(tier='goblin', p=g.model)])

def finish(c):
    return c.sort_values('p', ascending=False).drop_duplicates(['player', 'stat']).head(10)

def actual(E, n, s):
    k = norm(n)
    if k not in E.index or not E.loc[k].minutes: return None
    r = E.loc[k]; P, R, A = r.PTS, r.REB, r.AST
    return {'PTS': P, 'REB': R, 'AST': A, 'RA': R + A, 'PR': P + R, 'PA': P + A, 'PRA': P + R + A, '3PM': r['3PM']}.get(s)

def paid(r):
    if r.tier == 'goblin': return None
    bk = r.o if r.side == 'More' else r.u
    if pd.isna(bk) or abs(bk) < 100 or (r.o == -119 and r.u == -119): return -119
    return max(bk, -119) if bk < 0 else bk     # pick'em at -119 or the book, whichever pays more

def units(res, px):
    if res != 'Win': return -1.0 if res == 'Loss' else 0.0
    if px is None: return 0.0
    return px / 100 if px > 0 else 100 / -px

rows = []
for d in DAYS:
    bf, ef = f'slate/{d}/board_all.csv', f'slate/{d}/espn_box.csv'
    if not (os.path.exists(bf) and os.path.exists(ef)): continue
    B = pd.read_csv(bf); E = pd.read_csv(ef); E['k'] = E.player.map(norm); E = E.drop_duplicates('k').set_index('k')
    done = set(E.game)
    for name, fn in (('main', rule_main), ('cal_market', rule_cal)):
        C = finish(fn(B)); C = C[C.game.isin(done)]
        for r in C.itertuples():
            a = actual(E, r.player, r.stat)
            res = 'DNP' if a is None or pd.isna(a) else 'Push' if a == r.line else 'Win' if ((a > r.line) if r.side == 'More' else (a < r.line)) else 'Loss'
            px = paid(r)
            rows.append(dict(day=d, rule=name, player=r.player, stat=r.stat, side=r.side, line=r.line, p=round(r.p, 3), actual=a, result=res, px=px, u=units(res, px), tier=r.tier))

R = pd.DataFrame(rows); R = R[R.tier == 'standard']   # goblins are Over-only and identical in both rules
R.to_csv('research/replay_card_rules.csv', index=False)
R['oos'] = np.where(R.day > DESIGN_END, 'out-of-sample (11/12+)', 'design window (11/04-11/11)')
def summ(g):
    g = g[g.result.isin(['Win', 'Loss'])]
    return pd.Series(dict(W=int((g.result == 'Win').sum()), L=int((g.result == 'Loss').sum()), hit=round((g.result == 'Win').mean(), 3), units=round(g.u.sum(), 2), roi=round(g.u.sum() / max(len(g), 1), 3)))
print(R.groupby(['oos', 'rule']).apply(summ).to_string())
print(); print(R.groupby('rule').apply(summ).to_string())
print(); print(R.groupby(['rule', 'day']).apply(summ).unstack(0).to_string())
