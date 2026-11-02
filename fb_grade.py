"""python3 fb_grade.py YYYY-MM-DD -> grades the first-basket picks (top 2 per team from fb_priced.csv) against fb_actual.csv,
writes slate/MMDD/fb_graded.csv and keeps fb_log.csv (one row per pick; re-grading a day replaces it).
Profit is 1 unit per pick at the book's American odds."""
import sys, os, pandas as pd
from slate_names import norm
DATE = sys.argv[1]; D = f'slate/{DATE[5:7]}{DATE[8:10]}'
if not (os.path.exists(f'{D}/fb_priced.csv') and os.path.exists(f'{D}/fb_actual.csv')): sys.exit('nothing to grade')
P = pd.read_csv(f'{D}/fb_priced.csv'); A = pd.read_csv(f'{D}/fb_actual.csv')
P = P[P.game.isin(A.game)].sort_values('p_first_fg', ascending=False).groupby(['game', 'team']).head(2)
first = {g: norm(p) for g, p in zip(A.game, A.player)}
P['first_scorer'] = P.game.map(dict(zip(A.game, A.player)))
P['hit'] = [norm(p) == first.get(g) for p, g in zip(P.player, P.game)]
P['profit'] = [b / 100 if h else -1 for b, h in zip(P.book, P.hit)]
P['date'] = DATE
cols = ['date', 'game', 'team', 'player', 'p_first_fg', 'fair_odds', 'book', 'ev', 'first_scorer', 'hit', 'profit']
P[cols].to_csv(f'{D}/fb_graded.csv', index=False)
L = pd.read_csv('fb_log.csv') if os.path.exists('fb_log.csv') else pd.DataFrame(columns=cols)
L = pd.concat([L[L.date.astype(str) != DATE], P[cols]]); L.to_csv('fb_log.csv', index=False)
print(P[cols].to_string(index=False)); print(f"{int(P.hit.sum())}/{len(P)} picks, {P.groupby('game').hit.any().sum()}/{P.game.nunique()} games, {P.profit.sum():+.2f}u")
