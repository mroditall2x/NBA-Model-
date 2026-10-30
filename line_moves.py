"""Line-movement check. Save a morning snapshot, compare to a pre-tip snapshot, adjust the card.
  python3 line_moves.py snap slate/MMDD open      (copies lines.json/props_p1.txt -> *_open)
  python3 line_moves.py check slate/MMDD          (compares open vs current, writes moves.csv, flags card.csv)
Rules (from 10/28 OKC -6.5 -> -5.5, DAL won by 24):
  sides/totals: line moved >= 1.0 pt AGAINST the model side -> 'market disagrees' -> drop the leg (or follow the market if the move is tied to injury news)
                moved >= 1.0 pt TOWARD the model side -> 'market agrees' -> keep, small confidence bump
  moneyline: home win prob (no-vig) moved >= 3 pts against the model's side -> drop / follow market
  props: line moved >= 1.0 (>= 0.5 on lines under 5) against the model side -> drop; toward -> keep"""
import sys, json, shutil, pandas as pd
cmd, D = sys.argv[1], sys.argv[2]
if cmd == 'snap':
    for f in ('lines.json', 'props_p1.txt'): shutil.copy(f'{D}/{f}', f'{D}/{f}.open')
    sys.exit(f'snapshot saved in {D}')
o = {f"{g['away']}@{g['home']}": g for g in json.load(open(f'{D}/lines.json.open'))['games']}
n = {f"{g['away']}@{g['home']}": g for g in json.load(open(f'{D}/lines.json'))['games']}
G = pd.read_csv(f'{D}/games.csv').set_index('game'); rows = []
for k, g in n.items():
    if k not in o or k not in G.index: continue
    m = G.loc[k]
    ds = g['home_spread'] - o[k]['home_spread']            # + = moved toward away team
    model_home = m.p_home_cover > 0.5
    if abs(ds) >= 1: rows.append((k, 'spread', o[k]['home_spread'], g['home_spread'], 'against' if (ds > 0) == model_home else 'toward'))
    imp = lambda x: (-x/(-x+100)) if x < 0 else 100/(x+100)
    ph0 = imp(o[k]['ml_home'])/(imp(o[k]['ml_home'])+imp(o[k]['ml_away'])); ph1 = imp(g['ml_home'])/(imp(g['ml_home'])+imp(g['ml_away']))
    if abs(ph1-ph0) >= 0.03:                                # moneyline: 3+ pts of win probability
        rows.append((k, 'moneyline', o[k]['ml_home'], g['ml_home'], 'toward' if (ph1 > ph0) == (m.p_home_win > 0.5) else 'against'))
    dt = g['total'] - o[k]['total']; model_over = m.p_over > 0.5
    if abs(dt) >= 1: rows.append((k, 'total', o[k]['total'], g['total'], 'toward' if (dt > 0) == model_over else 'against'))
cols = ['game', 'player', 'stat', 'line', 'o', 'u']
po = pd.read_csv(f'{D}/props_p1.txt.open', sep='|', names=cols); pn = pd.read_csv(f'{D}/props_p1.txt', sep='|', names=cols)
P = po.merge(pn, on=['game', 'player', 'stat'], suffixes=('_open', '_now'))
P['move'] = P.line_now - P.line_open
C = pd.read_csv(f'{D}/card.csv')
C = C.merge(P[['player', 'stat', 'line_open', 'line_now', 'move']], on=['player', 'stat'], how='left')
thr = C.line_open.apply(lambda l: 0.5 if l < 5 else 1.0)
C['line_move'] = ['' if pd.isna(mv) or abs(mv) < t else ('against' if (mv > 0) == (sd == 'More') else 'toward') for mv, t, sd in zip(C.move, thr, C.side)]
C['keep'] = C.line_move != 'against'
C.to_csv(f'{D}/card.csv', index=False)
pd.DataFrame(rows, columns=['game', 'market', 'open', 'now', 'vs_model']).to_csv(f'{D}/moves.csv', index=False)
print(pd.read_csv(f'{D}/moves.csv').to_string(index=False)); print(C[C.line_move != ''][['player', 'stat', 'side', 'line_open', 'line_now', 'line_move']].to_string(index=False))
