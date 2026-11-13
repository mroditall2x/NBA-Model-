"""Replay: role-change window = current starter/bench streak vs flat last 8 (11/13/26).
python3 research/replay_role_streak.py
Uses each day's saved board_all.csv (model mean per player+stat) and hoopR box scores; recomputes the role flag both
ways from games before that date (existing 'role up/down' flags are stripped first), then applies run_day card rules."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '.'); from slate_names import norm
pb = pd.read_parquet('repo/nba/player_box/parquet/player_box_2027.parquet')
c3 = [c for c in pb.columns if 'three_point_field_goals_made' in c][0]
for c in ['minutes', 'points', 'rebounds', 'assists', c3, 'steals', 'blocks']: pb[c] = pd.to_numeric(pb[c], errors='coerce')
pb = pb[pb.minutes > 0].copy(); pb['k'] = pb.athlete_display_name.map(norm); pb['d'] = pb.game_date.astype(str).str[:10]
P, Rb, A = pb.points, pb.rebounds, pb.assists
pb = pb.assign(PTS=P, REB=Rb, AST=A, PA=P + A, PR=P + Rb, RA=Rb + A, PRA=P + Rb + A, **{'3PM': pb[c3]}).sort_values('game_date')
STATS = ['PTS', 'REB', 'AST', 'PA', 'PR', 'RA', 'PRA', '3PM']
DMIN = {'PTS': 4, 'PA': 4, 'PR': 4, 'PRA': 5, 'RA': 2}
DAYS = ['1028', '1030', '1031', '1101', '1102', '1104', '1105', '1106', '1107', '1108', '1109', '1110', '1111']
THR = float(sys.argv[1]) if len(sys.argv) > 1 else 1.25


def windows(hist, mode):
    """hist: player's games this season before the slate, oldest first. Returns the games used for the role check."""
    if len(hist) < 5: return None
    if mode == 'last8': return hist.tail(8)
    s = hist.starter.astype(bool).values[::-1]; streak = 1
    while streak < len(s) and s[streak] == s[0]: streak += 1
    if streak >= 4: return hist.tail(min(streak, 8)).assign(_thr=THR)     # settled current role: judge on it alone
    return hist.tail(8)


def flags(B, date, mode):
    h = pb[pb.d < date]; byk = {k: x for k, x in h.groupby('k')}
    out = []
    for r in B.itertuples():
        f = [z.strip() for z in str(r.flags).split(';') if z.strip() and not z.strip().startswith('role ')]
        x = byk.get(norm(r.player)); w = windows(x, mode) if x is not None else None
        if w is not None and r.stat in STATS and r.mean > 0 and len(w) >= 4:
            rv = w[r.stat].mean(); mv = r.mean; dm = DMIN.get(r.stat, 1.0); th = w['_thr'].iloc[0] if '_thr' in w else 1.25
            if rv >= th * mv and rv - mv >= dm: f.append(f'role up ({rv:.1f})')
            elif rv <= 0.75 * mv and mv - rv >= dm: f.append(f'role down ({rv:.1f})')
        out.append('; '.join(f))
    return out


def card(B):
    B = B.copy(); B['adj'] = 0.5 + 0.6 * (B.model - 0.5)
    ok = (B['gap'].abs() <= 4) & ~B.fl.str.contains('new team|small|unclear')
    ok &= ~((B.side == 'Less') & (B['gap'] > 2)) & ~((B.side == 'More') & (B['gap'] < -2))
    ok &= ~((B.side == 'Less') & B.fl.str.contains('role up')) & ~((B.side == 'More') & B.fl.str.contains('role down'))
    std = B[ok & B.type.isin(['PP standard', 'book line']) & ~B.stat.isin(['STL', 'BLK', 'STL+BLK'])]
    std = std[(std.adj >= 0.58) & (std.edge >= 0.05) & ~((std['min'] >= 35) & (std.side == 'Less') & (std.adj < 0.62))]
    std = std[~((std.stat == 'PTS') & (std.side == 'Less') & (std.adj < 0.60))]
    gob = B[ok & (B.type == 'goblin') & (B.model >= 0.84)]
    c = pd.concat([std.assign(tier='standard', p=std.adj), gob.assign(tier='goblin', p=gob.model)])
    return c.sort_values('p', ascending=False).drop_duplicates(['player', 'stat']).head(10)


res = {m: [] for m in ('last8', 'streak')}; blocked = []
for d in DAYS:
    date = f'2026-{d[:2]}-{d[2:]}'
    B = pd.read_csv(f'slate/{d}/board_all.csv'); B['flags'] = B['flags'].fillna('')
    act = pb[pb.d == date].drop_duplicates('k').set_index('k')
    B['actual'] = [act[s].get(norm(p_)) if norm(p_) in act.index and s in act else np.nan for p_, s in zip(B.player, B.stat)]
    for m in res:
        B['fl'] = flags(B, date, m); c = card(B).assign(d=d, mode=m)
        c = c.dropna(subset=['actual']); c = c[c.actual != c.line]
        c['win'] = np.where(c.side == 'More', c.actual > c.line, c.actual < c.line).astype(int); res[m].append(c)
for m, cs in res.items():
    c = pd.concat(cs)
    print(f"{m:7s} card {c.win.sum()}-{len(c) - c.win.sum()} ({c.win.mean():.1%})  Unders {c[c.side=='Less'].win.mean():.1%} n={int((c.side=='Less').sum())}"
          f"  | pre-fix boards 10/28-11/08 {c[c.d<'1109'].win.sum()}-{(c.d<'1109').sum()-c[c.d<'1109'].win.sum()}"
          f"  | current model 11/09-11/11 {c[c.d>='1109'].win.sum()}-{(c.d>='1109').sum()-c[c.d>='1109'].win.sum()}")
a, b = pd.concat(res['last8']), pd.concat(res['streak'])
key = ['d', 'player', 'stat', 'side']
only_a = a.merge(b[key], on=key, how='left', indicator=True).query('_merge=="left_only"')
only_b = b.merge(a[key], on=key, how='left', indicator=True).query('_merge=="left_only"')
print('\nOn the old card only (removed by streak window):'); print(only_a[key + ['line', 'actual', 'win']].to_string(index=False))
print('\nOn the new card only:'); print(only_b[key + ['line', 'actual', 'win']].to_string(index=False))

# ---- minutes check: card picks where the last 4 games ran well above the projected minutes
c = pd.concat(res['last8']).copy()
def rec_min(r):
    h = pb[(pb.d < f"2026-{r.d[:2]}-{r.d[2:]}") & (pb.k == norm(r.player))].tail(4)
    return pd.Series(dict(rmin=h.minutes.mean() if len(h) else np.nan, starts=int(h.starter.astype(bool).sum()) if len(h) else 0))
c = pd.concat([c.reset_index(drop=True), c.reset_index(drop=True).apply(rec_min, axis=1)], axis=1)
c['mdiff'] = c.rmin - c['min']
for lab, m in [('recent min 4+ above proj', c.mdiff >= 4), ('within 4', c.mdiff.abs() < 4), ('4+ below', c.mdiff <= -4)]:
    x = c[m]; print(f"{lab:26s} {x.win.sum()}-{len(x)-x.win.sum()}  Unders {x[x.side=='Less'].win.sum()}-{(x.side=='Less').sum()-x[x.side=='Less'].win.sum()}")
x = c[(c.starts >= 3) & (c['min'] < 24)]; print('started 3+ of last 4 but projected <24 min:', f"{x.win.sum()}-{len(x)-x.win.sum()}")
print(x[['d', 'player', 'stat', 'side', 'line', 'actual', 'min', 'rmin', 'win']].to_string(index=False))
