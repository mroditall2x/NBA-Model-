"""Replay the 11/14 3PT volume rules on past boards (run_day card rules, top 10 by p).
vol3 here = max(rate x model minutes, last-10 3PA) from research/threes_volume.csv (the live board uses the sim's 3PA)."""
import re, pandas as pd, numpy as np
src = open('run_day.py').read()
rules = src[src.index('# ---- card rules'):src.index('# ---- price')]
rules = rules.replace("B=pd.read_csv(f'{D}/board_all.csv'); B['flags']=B['flags'].fillna('')", '')
old_rules = re.sub(r"ok&=~\(\(B.stat=='3PM'\).*?\n", '', rules)
old_rules = old_rules[:old_rules.index('# volume Overs')] + "card=pd.concat([std.assign(tier='standard',p=std.adj),gob.assign(tier='goblin',p=gob.model)])\ncard=card.sort_values('p',ascending=False).drop_duplicates(['player','stat'])\n"
V = pd.read_csv('research/threes_volume.csv', dtype={'date': str})
V['vol3'] = V[['proj3pa', 'l10_3pa']].max(axis=1)
out = []
for md in sorted(V.date.unique()):
    B0 = pd.read_csv(f'slate/{md}/board_all.csv'); B0['flags'] = B0['flags'].fillna('')
    if 'o' not in B0: continue
    v = V[V.date == md].drop_duplicates('player').set_index('player')
    B0['vol3'] = [v.vol3.get(pl, np.nan) if st == '3PM' else np.nan for pl, st in zip(B0.player, B0.stat)]
    act = V[V.date == md].drop_duplicates('player').set_index('player').act3pm
    for name, code in (('old', old_rules), ('new', rules)):
        g = {'B': B0.copy(), 'pd': pd}; exec(code, g)
        c = g['card'].sort_values('p', ascending=False).head(10)
        c = c[c.stat == '3PM']
        for r in c.itertuples():
            a = act.get(r.player, np.nan)
            out.append(dict(rules=name, date=md, player=r.player, line=r.line, side=r.side, vol3=r.vol3, actual=a,
                            result=None if np.isnan(a) else ('Win' if (a > r.line) == (r.side == 'More') else 'Loss')))
O = pd.DataFrame(out)
for name, x in O.groupby('rules'):
    print(name, 'card 3PM:', (x.result == 'Win').sum(), '-', (x.result == 'Loss').sum(),
          '| Overs', ((x.side == 'More') & (x.result == 'Win')).sum(), '-', ((x.side == 'More') & (x.result == 'Loss')).sum(),
          '| Unders', ((x.side == 'Less') & (x.result == 'Win')).sum(), '-', ((x.side == 'Less') & (x.result == 'Loss')).sum())
k = ['date', 'player', 'line', 'side']
m = O[O.rules == 'old'].merge(O[O.rules == 'new'], on=k, how='outer', suffixes=('_old', '_new'), indicator=True)
print('\ndropped by new rules:'); print(m[m._merge == 'left_only'][k + ['vol3_old', 'actual_old', 'result_old']].to_string(index=False))
print('\nadded by new rules:'); print(m[m._merge == 'right_only'][k + ['vol3_new', 'actual_new', 'result_new']].to_string(index=False))
